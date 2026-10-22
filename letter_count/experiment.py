#!/usr/bin/env python3
"""Letter-counting experiment.

For every configuration (dictionary language x question language x CoT x model)
this samples N random words, picks a random letter from each word, opens a fresh
`claude -p` session and asks how many times the letter appears in the word.

The same (word, letter) pairs are reused across all configurations that share a
dictionary, so the comparisons are paired.

Example:
    ./experiment.py --runs 100                       # full grid (16 configs)
    ./experiment.py --runs 10 --dict he --cot no     # a slice of the grid
    ./experiment.py --dry-run --runs 3               # print prompts, no calls
"""

import argparse
import csv
import itertools
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORDLISTS = {"he": HERE / "wordlists" / "he_50k.txt", "en": HERE / "wordlists" / "en_50k.txt"}
WORD_RE = {"he": re.compile(r"^[א-ת]{3,12}$"), "en": re.compile(r"^[a-z]{3,12}$")}

# Final letters count as the regular letter (מים has two מ).
FINAL_FORMS = str.maketrans("ךםןףץ", "כמנפצ")

PROMPTS = {
    ("he", "no"): 'כמה פעמים האות "{letter}" מופיעה במילה "{word}"? ענה במספר בלבד.',
    ("he", "yes"): (
        'כמה פעמים האות "{letter}" מופיעה במילה "{word}"? '
        "חשוב שלב אחר שלב: פרק את המילה לאותיות, אחת בכל פעם, וספור. "
        'בשורה האחרונה כתוב "תשובה: <מספר>".'
    ),
    ("en", "no"): 'How many times does the letter "{letter}" appear in the word "{word}"? '
                  "Answer with a number only.",
    ("en", "yes"): (
        'How many times does the letter "{letter}" appear in the word "{word}"? '
        "Think step by step: spell the word out one letter at a time and count. "
        'On the last line write "Answer: <number>".'
    ),
}

NUMBER_WORDS = {
    "zero": 0, "none": 0, "one": 1, "once": 1, "two": 2, "twice": 2, "three": 3, "four": 4, "five": 5,
    "אפס": 0, "אחת": 1, "אחד": 1, "פעם אחת": 1, "שתיים": 2, "שתי": 2, "שניים": 2, "פעמיים": 2,
    "שלוש": 3, "שלושה": 3, "ארבע": 4, "ארבעה": 4, "חמש": 5,
}


def normalize(text, lang):
    return text.translate(FINAL_FORMS) if lang == "he" else text.lower()


def load_words(lang, top):
    words = []
    with open(WORDLISTS[lang], encoding="utf-8") as f:
        for line in itertools.islice(f, top):
            w = line.split()[0]
            if WORD_RE[lang].match(w):
                words.append(w)
    return words


def sample_items(lang, n, top, seed):
    rng = random.Random(f"{seed}-{lang}")
    items = []
    for idx, word in enumerate(rng.sample(load_words(lang, top), n)):
        letter = normalize(rng.choice(word), lang)
        expected = normalize(word, lang).count(letter)
        items.append({
            "idx": idx,
            "word": word,
            "letter": letter,
            "expected": expected,
            # True when the word has a final form of the asked letter (e.g. מ in מים)
            "final_form_case": word.count(letter) != expected,
        })
    return items


def parse_answer(text, cot):
    marked = re.findall(r"(?:Answer|תשובה)\s*[:：]?\s*\**\s*(\d+)", text, re.IGNORECASE)
    if marked:
        return int(marked[-1])
    nums = re.findall(r"\d+", text)
    if nums:
        return int(nums[-1] if cot else nums[0])
    for phrase in sorted(NUMBER_WORDS, key=len, reverse=True):
        if re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text, re.IGNORECASE):
            return NUMBER_WORDS[phrase]
    return None


def ask_claude(prompt, model, workdir, retries=2):
    cmd = [os.environ.get("CLAUDE_BIN", "claude"), "-p", "--model", model, "--tools", "",
           "--strict-mcp-config", "--system-prompt", "You are a helpful assistant."]
    env = {**os.environ, "MAX_THINKING_TOKENS": "0"}
    for attempt in range(retries + 1):
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                              env=env, cwd=workdir, timeout=300)
        if proc.returncode == 0:
            return proc.stdout.strip()
        if attempt < retries:
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"claude failed ({proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}")


def check_models(models, workdir):
    for model in models:
        try:
            ask_claude("Reply with the word ok.", model, workdir, retries=0)
        except Exception as e:
            sys.exit(f"Model {model!r} is not usable: {e}")


def split(value):
    return [v.strip() for v in value.split(",") if v.strip()]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--runs", type=int, default=100, help="words per configuration")
    p.add_argument("--dict", default="he,en", help="dictionary language(s): he,en")
    p.add_argument("--qlang", default="he,en", help="question language(s): he,en")
    p.add_argument("--cot", default="no,yes", help="chain of thought: no,yes")
    p.add_argument("--model", default="claude-haiku-4-5,claude-3-5-haiku-20241022",
                   help="model(s), comma separated")
    p.add_argument("--top", type=int, default=20000, help="sample from the N most frequent words")
    p.add_argument("--seed", default="42")
    p.add_argument("--workers", type=int, default=4, help="parallel claude sessions")
    p.add_argument("--out", type=Path, help="results dir (reuse one to resume an interrupted run)")
    p.add_argument("--dry-run", action="store_true", help="print the prompts without calling claude")
    args = p.parse_args()

    dicts, qlangs, cots, models = split(args.dict), split(args.qlang), split(args.cot), split(args.model)
    items = {lang: sample_items(lang, args.runs, args.top, args.seed) for lang in dicts}
    configs = [dict(dict=d, qlang=q, cot=c, model=m)
               for d, q, c, m in itertools.product(dicts, qlangs, cots, models)]

    jobs = []
    for cfg in configs:
        for item in items[cfg["dict"]]:
            prompt = PROMPTS[(cfg["qlang"], cfg["cot"])].format(**item)
            jobs.append((cfg, item, prompt))

    if args.dry_run:
        for cfg, item, prompt in jobs:
            print(f"{cfg} expected={item['expected']}\n  {prompt}")
        return

    out = args.out or HERE / "results" / time.strftime("%Y%m%d_%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    results_path = out / "results.jsonl"
    key = lambda r: (r["dict"], r["qlang"], r["cot"], r["model"], r["idx"])
    done = {}
    if results_path.exists():
        for line in results_path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            done[key(r)] = r
    todo = [j for j in jobs if key({**j[0], **j[1]}) not in done]

    print(f"{len(configs)} configs x {args.runs} words = {len(jobs)} calls "
          f"({len(jobs) - len(todo)} already done). Results: {out}")

    with tempfile.TemporaryDirectory() as workdir:  # empty cwd so no project context leaks in
        check_models(models, workdir)

        def run(job):
            cfg, item, prompt = job
            try:
                answer, error = ask_claude(prompt, cfg["model"], workdir), None
            except Exception as e:
                answer, error = "", str(e)
            parsed = parse_answer(answer, cfg["cot"] == "yes")
            return {**cfg, **item, "prompt": prompt, "answer": answer, "parsed": parsed,
                    "correct": parsed == item["expected"], "error": error}

        with ThreadPoolExecutor(args.workers) as pool, open(results_path, "a", encoding="utf-8") as f:
            futures = [pool.submit(run, j) for j in todo]
            for n, fut in enumerate(as_completed(futures), 1):
                r = fut.result()
                if r["error"]:
                    print(f"  error: {r['error']}", file=sys.stderr)
                    continue  # not saved, so a rerun with --out retries it
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                f.flush()
                done[key(r)] = r
                mark = "✓" if r["correct"] else "✗"
                print(f"[{n}/{len(todo)}] {mark} {r['dict']}/{r['qlang']}/cot={r['cot']}/{r['model']} "
                      f"{r['word']} '{r['letter']}' expected={r['expected']} got={r['parsed']}")

    summarize(list(done.values()), configs, out)


def summarize(rows, configs, out):
    def acc(subset):
        return (sum(r["correct"] for r in subset), len(subset))

    lines = [("dict", "qlang", "cot", "model", "correct", "total", "accuracy", "unparsed")]
    for cfg in configs:
        subset = [r for r in rows if all(r[k] == v for k, v in cfg.items())]
        c, t = acc(subset)
        unparsed = sum(r["parsed"] is None for r in subset)
        lines.append((cfg["dict"], cfg["qlang"], cfg["cot"], cfg["model"], c, t,
                      f"{c / t:.1%}" if t else "-", unparsed))

    with open(out / "summary.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(lines)

    widths = [max(len(str(row[i])) for row in lines) for i in range(len(lines[0]))]
    print()
    for row in lines:
        print("  ".join(str(v).ljust(w) for v, w in zip(row, widths)))

    print("\nAccuracy by factor (averaged over everything else):")
    for factor in ("dict", "qlang", "cot", "model"):
        parts = []
        for value in sorted({r[factor] for r in rows}):
            c, t = acc([r for r in rows if r[factor] == value])
            parts.append(f"{value}={c / t:.1%} ({c}/{t})")
        print(f"  {factor:6} " + "   ".join(parts))
    print(f"\nSaved {out / 'results.jsonl'} and {out / 'summary.csv'}")


if __name__ == "__main__":
    main()
