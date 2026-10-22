# Letter-counting experiment — report

*22 Oct 2026 · 3,200 questions (32 setups × 100 words), 0 failed calls · raw data: `results/full_20261022/`*

## 1. Background

Language models read text as *tokens* (chunks of several characters), not as individual letters. So a
question that is trivial for a person, "how many times does ר appear in הרהורים?", can be hard for a
model: it has to recall the spelling of a token it never "sees" letter by letter. This experiment
measures how often Claude gets such questions right, and which conditions help or hurt.

## 2. Method

### 2.1 Procedure

For each setup, the script (`experiment.py`) repeated 100 times:

1. Pick a random word from the dictionary.
2. Pick a random letter from that word (a random position, so letters that repeat are picked more often).
3. Open a **new** Claude session (no memory of earlier questions) and ask how many times the letter
   appears in the word.
4. Pull the number out of the answer and compare it with the true count, computed by the script.

The same 100 (word, letter) pairs were used in every setup with the same dictionary, so setups are
compared on identical questions.

### 2.2 Restrictions on every call

```
MAX_THINKING_TOKENS=0 claude -p --model <model> --tools "" \
    --strict-mcp-config --system-prompt "You are a helpful assistant."
```

No tools (the model can't run code to count), no MCP servers, a neutral system prompt, and an empty
working directory, so no project context leaks in. Only the variables below were changed.

### 2.3 Variables (2 × 2 × 2 × 2 × 2 = 32 setups)

| Variable | Values |
|---|---|
| Word language | Hebrew / English words |
| Question language | Hebrew / English |
| CoT prompt | **no:** "Answer with a number only."  **yes:** "Spell the word out one letter at a time and count. On the last line write `Answer: <number>`." |
| Extended thinking | **off:** `MAX_THINKING_TOKENS=0`  **on:** Claude Code's default thinking |
| Model | Claude Haiku 4.5 (older) / Claude Haiku 5.5 (newer) |

Example (Hebrew question, no CoT): `כמה פעמים האות "ר" מופיעה במילה "הרהורים"? ענה במספר בלבד.`

### 2.4 Word lists

The plan was to use the Even-Shoshan dictionary, but it isn't freely available. Both languages instead
use the [FrequencyWords](https://github.com/hermitdave/FrequencyWords) lists (word frequencies in movie
subtitles): the 20,000 most common words, limited to 3–12 letters. Using the same kind of source for
both languages keeps the comparison fair.

### 2.5 Scoring

- **True count:** computed by the script.
- **Model's answer:** the number on the `Answer:` / `תשובה:` line if there is one, otherwise the last
  number in the reply. All 3,200 answers were parsed successfully.
- **Final letters:** whether ם counts as מ is ambiguous (does "מים" have one מ or two?), and the
  models disagree, so both counts are accepted. This affected 32 questions and decided 14.

## 3. Expectations

Before running, these were the expected results:

1. **CoT will beat no CoT.** Spelling the word out turns each letter into its own token, so the model
   counts what it sees instead of recalling a spelling.
2. **An English question will beat a Hebrew question.** Models see far more English training data, so
   they should follow instructions and reason better in English.
3. **A Hebrew question about an English word will do worse than an English question about a Hebrew
   word.** If the question's language matters more than the word's language, the English question
   should win.
4. **The newer model will beat the older one.** Haiku 5.5 should be generally stronger than Haiku 4.5.

The oldest Haiku models (3 and 3.5) have been retired, so Haiku 4.5 served as the "older model".

## 4. Results

### 4.1 Expectations vs. results

With a CoT prompt, almost every setup scored 99–100%, which leaves no room to see differences. So the
expectations are tested in the hardest setting: **no CoT prompt, thinking off.**

| # | Expectation | Result | Verdict |
|---|---|---|---|
| 1 | CoT beats no CoT | 99.9% vs 85.4% | ✅ confirmed |
| 2 | English question beats Hebrew question | 87.8% vs 83.0% | ⚠️ partly: only for Hebrew words (88.5% vs 77.5%); for English words 87.0% vs 88.5% |
| 3 | Hebrew question / English word < English question / Hebrew word | 88.5% vs 88.5% | ❌ no difference |
| 4 | Newer model beats older model | 95.8% vs 75.0% | ✅ confirmed |

### 4.2 Accuracy by model and language (no CoT, thinking off)

| Question → word | Haiku 4.5 | Haiku 5.5 |
|---|---|---|
| Hebrew → Hebrew | **55%** | 100% |
| Hebrew → English | 81% | 96% |
| English → Hebrew | 79% | 98% |
| English → English | 85% | **89%** |

### 4.3 All 32 setups

| Words | Question | CoT | Thinking | Haiku 4.5 | Haiku 5.5 |
|---|---|---|---|---|---|
| he | he | no | off | 55% | 100% |
| he | he | no | on | 100% | 100% |
| he | he | yes | off | 100% | 100% |
| he | he | yes | on | 100% | 100% |
| he | en | no | off | 79% | 98% |
| he | en | no | on | 100% | 99% |
| he | en | yes | off | 100% | 100% |
| he | en | yes | on | 100% | 100% |
| en | he | no | off | 81% | 96% |
| en | he | no | on | 100% | 99% |
| en | he | yes | off | 100% | 100% |
| en | he | yes | on | 99% | 100% |
| en | en | no | off | 85% | 89% |
| en | en | no | on | 100% | 89% |
| en | en | yes | off | 99% | 100% |
| en | en | yes | on | 100% | 100% |

Each cell is out of 100 questions.

## 5. Discussion

- **Errors come from answering without reasoning.** Every setup with a CoT prompt scored 99–100%. The
  remaining errors are all "answer immediately" cases, consistent with the token explanation in §1.
- **The two models have opposite weak spots.** Haiku 4.5 is weakest in Hebrew (55% on Hebrew words
  asked in Hebrew); Haiku 5.5 is perfect there but weakest in English (89% on English words asked in
  English). So expectation 2 holds only for the older model.
- **Thinking helped Haiku 4.5 but not Haiku 5.5.** With thinking on, Haiku 4.5 reached 100% everywhere.
  Haiku 5.5 repeated exactly the same mistakes as with thinking off (e.g. "almost"/t → 0,
  "liable"/l → 1). Apparently it doesn't think by default on a question this easy; only the explicit
  CoT prompt fixed it.
- **Mistakes are nearly always off by one:** 75 answers were one too low, 55 one too high, 2 off by two.

## 6. Limitations

- Subtitle words instead of Even-Shoshan: the list includes names and slang (e.g. "קתרין", "allan").
- 100 questions per setup: differences of a few percentage points are within noise.
- Claude Code doesn't show whether thinking actually happened, so the "thinking on" result for Haiku 5.5
  is inferred from its identical answers.
- Only two models; "older vs. newer" here means Haiku 4.5 vs. 5.5, not a broader model history.

## 7. Reproduce

```bash
./experiment.py --runs 100 --workers 8                 # full grid, ~35 minutes
./experiment.py --report results/full_20261022         # rebuild the tables from saved answers
```
