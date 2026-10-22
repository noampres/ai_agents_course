# Can Claude count letters? — Lab report

**TL;DR:** Answering instantly, Claude miscounts letters, worst of all claude-haiku-4-5 on Hebrew (55% correct);
a step-by-step (CoT) prompt fixed almost every mistake (99.9% over 1,600 runs).

**Experiment.** Each run takes a random word (from the 20k most common Hebrew or English subtitle words) and a
random letter from it, and asks a fresh Claude Code session `How many times does the letter "r" appear in the
word "reports"?`. Settings: `claude -p --tools "" --strict-mcp-config --system-prompt "You are a helpful
assistant."`. 5 factors × 2 values = 32 setups × 100 runs (the same 100 words in each): model `claude-haiku-4-5`
vs `claude-haiku-5-5`; Hebrew vs English words; question in Hebrew vs English; no CoT (*"Answer with a number
only."*) vs CoT (*"Think step by step: spell the word out one letter at a time and count. On the last line
write "Answer: <number>"."*); thinking off (`MAX_THINKING_TOKENS=0`) vs on (default). Correct = final number
equals the true count (for Hebrew final letters, ם counted as מ or not are both accepted).

**My expectations vs. results** (no CoT, thinking off unless noted; runs per side in brackets):

| Expectation | Result | Verdict |
|---|---|---|
| CoT beats no CoT | 99.9% vs 85.4% (800), thinking off | ✅ Confirmed |
| English question beats Hebrew question | 87.8% vs 83.0% (400) | ⚠️ Partly: Hebrew words only (88.5% vs 77.5%, 200); haiku-5-5 was better in Hebrew |
| Hebrew Q on English words < English Q on Hebrew words | 88.5% vs 88.5% (200) | ❌ No difference |
| Newer model beats older | haiku-5-5 95.8% vs haiku-4-5 75.0% (400) | ✅ Confirmed |

**Harder cases.** Thinking fixed claude-haiku-4-5 (100%, 400 runs) but not claude-haiku-5-5, which repeated the
same mistakes on English words (89%, 100 runs), suggesting it doesn't think by default on easy questions.
Almost all mistakes were off by one.
