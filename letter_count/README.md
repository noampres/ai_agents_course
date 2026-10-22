# letter_count

Can Claude count how many times a letter appears in a word?

For each configuration, `experiment.py` samples N random words, picks a random letter from each word,
opens a fresh `claude -p` session and asks how many times the letter appears. Every call uses (thinking is turned on only in the `--thinking yes` variation):

```
MAX_THINKING_TOKENS=0 claude -p --model <model> --tools "" \
    --strict-mcp-config --system-prompt "You are a helpful assistant."
```

## Variations (full grid = 32 configs)

| factor  | values |
|---------|--------|
| `--dict`  | `he` (Hebrew words), `en` (English words) |
| `--qlang` | `he` / `en`: language the question is asked in |
| `--cot`   | `no`: "answer with a number only"; `yes`: "spell it out letter by letter, then `Answer: N`" |
| `--thinking` | `no`: `MAX_THINKING_TOKENS=0`; `yes`: Claude Code's normal thinking (or `--thinking-tokens N`) |
| `--model` | `claude-haiku-4-5` vs. `claude-haiku-5-5` (older Haikus 3 / 3.5 are retired, so 4.5 is the oldest available) |

## Run

```bash
./experiment.py --runs 100                         # full grid: 3200 calls
./experiment.py --runs 100 --dict he --cot no,yes  # a slice
./experiment.py --dry-run --runs 3                 # just print the prompts
./experiment.py --out results/<dir>                # resume an interrupted run
./experiment.py --report results/<dir>             # rebuild the tables only
```

Output goes to `results/<timestamp>/`: `results.jsonl` (every question and answer), `summary.csv`, and `results.md`
(accuracy table: one row per dictionary/question/CoT/thinking combination, one column per model).

## Notes

- **Word lists:** Even-Shoshan isn't freely available, so both languages use the
  [FrequencyWords](https://github.com/hermitdave/FrequencyWords) lists (OpenSubtitles 2018), filtered
  to 3-12 letter words from the top 20k. Using the same source for both keeps the comparison fair.
  To use another dictionary, replace the file in `wordlists/`.
- **Final letters:** it's ambiguous whether ם counts as מ ("מים" has two מ, or one?), and models disagree
  (Haiku 5.5 counts ם as a separate letter). Both answers are accepted. The prompt shows the
  regular form, and rows where this matters are marked `final_form_case: true` in `results.jsonl`, with
  both `expected` and `expected_strict`.
- The same (word, letter) pairs are used in every config with the same dictionary (`--seed`), so
  comparisons are paired.
- Each call runs in an empty temporary directory, so no project context (CLAUDE.md etc.) leaks in.
