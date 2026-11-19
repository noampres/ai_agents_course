# All-Pairs Shortest Paths → Floyd–Warshall: SHORT Script (DRAFT v4)

**Goal:** same story as v3, with every non-essential demonstration cut, so a full render
from scratch takes **≤ 20 min**. (v3 stays as the long version in `SCRIPT_OUTLINE.md`.)

## Render budget (measured, not guessed)

- Measured: `07_fw_demo` (40.7 s of video) renders in **85.6 s** with TTS cached → ~2.1 s per video-second;
  fresh Kokoro TTS adds ~0.7 s per audio-second → **~2.8 s of rendering per second of video**.
- v4 target length: **~2 min 30 s** (narration at 1.5×) → **~7 min** to render all segments
  + ~1 min stitching ≈ **8 min**, which leaves 2.5× headroom under 20 min.
- (v3 is ~4.5 min ≈ 13–15 min to render; the time saving is mostly in production and checking, since there are fewer
  and simpler segments.)

## Rules for cutting

1. Show **one** fully worked example per algorithm; everything else changes **all at once** with one sentence.
2. No rejected checks ("8 + ∞ = ∞, no change"). Only show what changes the answer.
3. Every number on screen appears **once**; no repeated examples (B→D is worked in the edge-by-edge demo, then
   reused as the FW detour, with no second walkthrough).
4. Tables instead of animations wherever the point is a comparison (cost, head-to-head).
5. Reuse finished segments by trimming (02, 04, 07) rather than rebuilding them.

Notation and running example: unchanged from v3 (`m` = max edges, `k` = a vertex; graph A–D, same tables).

---

## 01_hook (~8 s) · new, simple
- **On screen:** ONE web photo (cars on a highway, per CLAUDE.md image rules) for the first line; it
  dissolves into the drawn graph; title bar fades in.
- **Narration:**
  1. "A navigation app needs the cheapest route between every pair of cities."
  2. "That's the all-pairs shortest-paths problem."
- *Cut from v3:* city-map photo, markers tracing roads.

## 02_problem (~25 s) · trim of the finished `segments/02_problem`
- **Narration:**
  1. "We get a directed graph with n vertices and a weight on every edge."
  2. "We want an n-by-n table: row i, column j holds the shortest distance from i to j."
  3. "Weights may be negative, but no cycle may have a negative total. Then shortest paths never repeat a vertex, so they use at most n − 1 edges."
  4. "Running Bellman–Ford from every vertex would cost up to Θ(n⁴)."
  5. "We start from the direct roads: this table W is the best using at most one edge."
- **On screen:** the same elements as the finished 02 segment, with the assumption card and key fact merged into one card
  and the 7 weight flights replaced by **all edges' weights fading into the table at once**.
- *Cut from v3:* the path-length example (B→A→D vs B→C→D, which the 03 demo shows anyway), separate
  assumption/key-fact beats, per-edge flights.

## 03_edge_by_edge (~35 s) · trim of `segments/04_extend_demo` + its idea
- **Narration:**
  1. "Natural idea: allow one more edge at a time. A path with at most m edges is a shorter one plus a last edge k → j."
  2. Formula strip: `L⁽ᵐ⁾[i][j] = min over k ( L⁽ᵐ⁻¹⁾[i][k] + W[k][j] )`. "Try every last stop k and keep the cheapest."
  3. **Worked cell L⁽²⁾[B][D]** (the one full demo, kept from 04): work table A: 15, B: ∞, **C: 3**, D: ∞ (old value), min = 3.
  4. "Doing that for every cell gives L⁽²⁾…" (all changed cells turn GOOD at once) "…and once more gives L⁽³⁾, the answer."
- *Cut from v3:* separate 03_extend_idea segment, the min-plus ↔ matrix multiplication inset, individual flashes
  of each changed cell, the A→D walk-through in L⁽³⁾.

## 04_cost (~12 s) · new, a single table
- **On screen:** 3-row table appears row by row.

  | Method | Time |
  |---|---|
  | n × Bellman–Ford | up to Θ(n⁴) |
  | Edge by edge | Θ(n⁴): n tables × n³ each |
  | …with repeated squaring | Θ(n³ log n) |

- **Narration:** "Each table costs n³, and we need about n of them: n⁴. Squaring the tables instead gets n³ log n. Can we reach n³?"
- *Cut from v3:* pulsing cells, stacked-table animation, chip chains.

## 05_floyd_warshall (~40 s) · trim of `segments/07_fw_demo` + its idea
- **Narration:**
  1. "Floyd–Warshall asks a different question: not how many edges, but which vertices a path may pass through."
  2. Formula strip: `dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])`. "Round k: is going through k shorter? One comparison per cell."
  3. **k = A, improvements only:** B→D 15, C→B 8, D→B 5 (one short line each, detour drawn on the graph).
  4. "Rounds B, C and D do the same…" (each round's updates flash together, ~2 s per round)
  5. "…and we land on exactly the same table, in Θ(n³)."
- *Cut from v3:* separate 06_fw_idea segment and its preview, the 3 rejected checks in round A, the narrated k = B detail.

## 06_compare (~15 s) · new, a single table
- **On screen:** comparison table; FW column outlined GOOD.

  | | Edge by edge | Squaring | Floyd–Warshall |
  |---|---|---|---|
  | Work per round | n³ | n³ | n² |
  | Time | Θ(n⁴) | Θ(n³ log n) | **Θ(n³)** |
  | n = 1000 | ~10¹² | ~10¹⁰ | ~10⁹ |

- **Narration:** "The difference: one comparison per cell instead of a min over every vertex. That's a factor of n,
  a thousand times fewer steps when n is a thousand."
- *Cut from v3:* side-by-side pseudocode, cost counters, the in-place icons, the bar chart, the space row.

## 07_recap (~10 s + 3 s ending slide) · new
- **Narration:**
  1. "Bonus: a negative number on the diagonal at the end reveals a negative cycle."
  2. "Grow paths edge by edge: n⁴. Choose the stepping stones: n³. That's Floyd–Warshall."
- **On screen:** two summary lines, then the ending slide (VISUALS.md; character slot user-supplied, fallback layout if absent).
- *Cut from v3:* the 3-card caveats segment (the Dijkstra card; negative weights were already covered in 02).

---

## Length summary

| Segment | v3 | v4 |
|---|---|---|
| hook | 13 s | 8 s |
| problem | 35 s (built) | ~25 s |
| edge by edge (idea + demo) | 20 + 44 s | ~35 s |
| cost | 20 s | ~12 s |
| FW (idea + demo) | 23 + 41 s | ~40 s |
| compare | 27 s | ~15 s |
| notes + recap | 17 + 10 s | ~10 s |
| ending slide | 3 s | 3 s |
| **Total** | **~4.5 min** | **~2.5 min** |

## Open questions
- Keep the one web photo in the hook, or start straight on the graph (saves search time, not render time)?
- OK to drop the min-plus / matrix-multiplication remark? (It's what makes "repeated squaring" make sense; v4
  keeps squaring only as one row of the cost table.)
