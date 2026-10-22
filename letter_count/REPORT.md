# Letter-counting experiment — final report

*22 Oct 2026 · 3,200 answers (32 setups × 100 words), 0 errors · raw data: `results/full_20261022/`*

**Question.** Can Claude count how often a letter appears in a word? For each setup, 100 random words
(the 20k most common Hebrew / English words from subtitles) got one random letter each. Each question
went to a fresh `claude -p` session with no tools and no MCP servers. Variations: word language (he/en),
question language (he/en), a step-by-step (CoT) prompt or not, extended thinking or not
(`MAX_THINKING_TOKENS=0`), and Haiku 4.5 (oldest model still available) vs. Haiku 5.5.

## Expectations vs. results

Tested in the hardest setting (no CoT prompt, thinking off), where the errors happen; with a CoT prompt,
accuracy is 99.9% overall.

| # | Expectation | Result | Verdict |
|---|---|---|---|
| 1 | CoT beats no CoT | 99.9% vs 85.4% | ✅ confirmed |
| 2 | English question beats Hebrew question | 87.8% vs 83.0% | ⚠️ partly: only Hebrew words, only Haiku 4.5 |
| 3 | Hebrew question about English words < English question about Hebrew words | 88.5% vs 88.5% | ❌ no difference |
| 4 | Newer model beats older model | Haiku 5.5 95.8% vs Haiku 4.5 75.0% | ✅ confirmed |

## Key findings

- **Errors come from answering without reasoning.** Haiku 4.5, asked in Hebrew about Hebrew words without
  reasoning, got only **55%**. A CoT prompt brought every setup to 99–100%.
- **Language hurts the older model most.** Without reasoning, Haiku 4.5 got 55% (he→he), 79–81% (mixed)
  and 85% (en→en). Haiku 5.5 was the reverse: 100% on he→he but only **89% on en→en**.
- **Thinking helped Haiku 4.5 but not Haiku 5.5.** With thinking on, Haiku 4.5 reached 100%, but Haiku 5.5
  repeated exactly the same mistakes as without it (e.g. "almost"/t → 0, "liable"/l → 1). Apparently it
  doesn't think by default on a question this easy; only the CoT prompt fixed it.
- Mistakes are almost always off by one (75 too low, 55 too high, 2 off by two).

## Caveats

- Even-Shoshan isn't freely available; a subtitle-frequency list was used (includes names and slang).
- Final letters (ם/ן/ץ/ף/ך) are ambiguous: Haiku 5.5 counts ם as separate from מ. Both counts are
  accepted (decides 14 of the 32 affected answers).
- 100 words per setup: differences of a few points are within noise.
