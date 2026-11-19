# All-Pairs Shortest Paths → Floyd–Warshall: SHORT Script (DRAFT v4)

**Goal:** same story as v3, with every non-essential demonstration cut, so a full render
from scratch takes **≤ 20 min**. (v3 stays as the long version in `SCRIPT_OUTLINE.md`.)

## Render budget (measured, not guessed)

- Measured: `07_fw_demo` (40.7 s of video) renders in **85.6 s** with TTS cached → ~2.1 s per video-second;
  fresh Kokoro TTS adds ~0.7 s per audio-second → **~2.8 s of rendering per second of video**.
- v4 target length: **~3 min** (narration at 1.2×). Only the 2 table demos are drawn frame by frame;
  everything else is static keyframes → **~6–8 min** total render, well under 20 min (see the table at the end).
- (v3 is ~4.5 min ≈ 13–15 min to render; the time saving is mostly in production and checking, since there are fewer
  and simpler segments.)

## Rules for cutting

1. Show **one** fully worked example per algorithm; everything else changes **all at once** with one sentence.
2. No rejected checks ("8 + ∞ = ∞, no change"). Only show what changes the answer.
3. Every number on screen appears **once**; no repeated examples (B→D is worked in the edge-by-edge demo, then
   reused as the FW detour, with no second walkthrough).
4. Tables instead of animations wherever the point is a comparison (cost, head-to-head).
5. Reuse finished segments by trimming (02, 04, 07) rather than rebuilding them.
6. **At most 3 table demonstrations in the whole video:** ① edge-by-edge (03), ② Floyd–Warshall (05),
   ③ final comparison (06). No other segment animates a table: W is first *shown* as the starting
   state of demo ①, and costs are text in the formula strip.
7. **Static images over effects.** Photos and non-demo slides are static: no Ken Burns zoom,
   no morphing markers, no flying elements. The only transitions are plain crossfades. Static
   segments (01, 02, 04, 07) are rendered as a few **keyframe PNGs held by ffmpeg** (`-loop 1 -t <dur>`,
   joined with short xfades) instead of drawing every frame in Python; they render in seconds.

Notation and running example: unchanged from v3 (`m` = max edges, `k` = a vertex; graph A–D, same tables).

---

## 01_hook (~10 s) · new, STATIC (2 keyframes)
- **On screen:** keyframe 1 = ONE static web photo (cars on a highway, per CLAUDE.md image rules),
  darkened, with title text. Crossfade → keyframe 2 = title bar + drawn graph.
- **Narration:**
  1. "A navigation app needs the cheapest route between every pair of cities."
  2. "That's the all-pairs shortest-paths problem."
- *Cut from v3:* city-map photo, markers tracing roads.

## 02_problem (~28 s) · new, STATIC (3 keyframes; replaces the animated 02 segment)
- **Narration:**
  1. "We get a directed graph with n vertices and a weight on every edge, and we want the shortest distance from every i to every j."
  2. "Weights may be negative, but no cycle may have a negative total. Then shortest paths never repeat a vertex, so they use at most n − 1 edges."
  3. "Running Bellman–Ford from every vertex would cost up to Θ(n⁴)."
- **On screen:** graph on the left the whole time; the right half shows one text card per line
  (keyframes crossfade): ① "INPUT graph, n = 4 · OUTPUT dist(i → j) for all pairs" ② "no negative cycles ⇒ ≤ n − 1 edges"
  ③ "n × Bellman–Ford ≈ Θ(n⁴)".
- *Cut from v3:* the path-length example, the "?" goal table, the W table build (W now first appears,
  already filled, as the opening state of demo ①), all flights and pulses. The finished animated
  `segments/02_problem` stays in the repo for the long version.

## 03_edge_by_edge (~48 s) · TABLE DEMO ① · trim of `segments/04_extend_demo` + its idea
- **Narration:**
  0. "Start with the direct roads: this table W is the best using at most one edge." (W fades in, already filled)
  1. "Natural idea: allow one more edge at a time. A path with at most m edges is a shorter one plus a last edge k → j."
  2. Formula strip: `L⁽ᵐ⁾[i][j] = min over k ( L⁽ᵐ⁻¹⁾[i][k] + W[k][j] )`. "Try every last stop k and keep the cheapest."
  3. **Worked cell L⁽²⁾[B][D]** (the one full demo, kept from 04): work table A: 15, B: ∞, **C: 3**, D: ∞ (old value), min = 3.
  4. "Doing that for every cell gives L⁽²⁾…" (all changed cells turn GOOD at once) "…and once more gives L⁽³⁾, the answer."
- *Cut from v3:* separate 03_extend_idea segment, the min-plus ↔ matrix multiplication inset, individual flashes
  of each changed cell, the A→D walk-through in L⁽³⁾.

## 04_cost (~13 s) · new, STATIC (2 keyframes, no table)
- **On screen:** 03's last frame stays; the formula strip text swaps (crossfade) to
  `n tables × n³ each = Θ(n⁴)`, then to `squaring: log n tables → Θ(n³ log n)`.
- **Narration:** "Each table costs n³, and we need about n of them: n⁴. Squaring the tables instead gets n³ log n. Can we reach n³?"
- *Cut from v3:* the cost table (its numbers move into the comparison table ③), pulsing cells, stacked tables, chip chains.

## 05_floyd_warshall (~50 s) · TABLE DEMO ② · trim of `segments/07_fw_demo` + its idea
- **Narration:**
  1. "Floyd–Warshall asks a different question: not how many edges, but which vertices a path may pass through."
  2. Formula strip: `dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])`. "Round k: is going through k shorter? One comparison per cell."
  3. **k = A, improvements only:** B→D 15, C→B 8, D→B 5 (one short line each, detour drawn on the graph).
  4. "Rounds B, C and D do the same…" (each round's updates flash together, ~2 s per round)
  5. "…and we land on exactly the same table, in Θ(n³)."
- *Cut from v3:* separate 06_fw_idea segment and its preview, the 3 rejected checks in round A, the narrated k = B detail.

## 06_compare (~19 s) · TABLE DEMO ③ (the last table), near-static (2 keyframes)
- **On screen:** keyframe 1 = the full comparison table; keyframe 2 = same table with the FW column outlined GOOD.

  | | n × Bellman–Ford | Edge by edge | Squaring | Floyd–Warshall |
  |---|---|---|---|---|
  | Work per round | — | n³ | n³ | n² |
  | Time | up to Θ(n⁴) | Θ(n⁴) | Θ(n³ log n) | **Θ(n³)** |
  | n = 1000 | ~10¹² | ~10¹² | ~10¹⁰ | ~10⁹ |

- **Narration:** "The difference: one comparison per cell instead of a min over every vertex. That's a factor of n,
  a thousand times fewer steps when n is a thousand."
- *Cut from v3:* side-by-side pseudocode, cost counters, the in-place icons, the bar chart, the space row.

## 07_recap (~13 s + 3 s ending slide) · new, STATIC (2 keyframes + ending slide)
- **Narration:**
  1. "Bonus: a negative number on the diagonal at the end reveals a negative cycle."
  2. "Grow paths edge by edge: n⁴. Choose the stepping stones: n³. That's Floyd–Warshall."
- **On screen:** two summary lines, then the ending slide (VISUALS.md; character slot user-supplied, fallback layout if absent).
- *Cut from v3:* the 3-card caveats segment (the Dijkstra card; negative weights were already covered in 02).

---

## Length summary

| Segment | v3 | v4 |
|---|---|---|
| Segment | v3 | v4 | v4 render method | est. render time |
|---|---|---|---|---|
| hook | 17 s | 10 s | static keyframes | ~10 s |
| problem | 46 s | ~28 s | static keyframes | ~25 s |
| edge by edge (idea + demo) ① | 25 + 50 s | ~48 s | animated (trimmed 04) | ~2.3 min |
| cost | 25 s | ~13 s | static keyframes | ~10 s |
| FW (idea + demo) ② | 29 + 75 s | ~50 s | animated (trimmed 07) | ~2.4 min |
| compare ③ | 33 s | ~19 s | static keyframes | ~15 s |
| notes + recap | 21 + 13 s | ~13 s | static keyframes | ~10 s |
| ending slide | 3 s | 3 s | static | ~2 s |
| stitching | | | ffmpeg xfade | ~1 min |
| **Total** | **~5.5 min** | **~3 min** | | **~6–8 min** |

Estimates: animated = 2.8 s per video-second (measured); static = TTS (~0.7 s per audio-second) + an ffmpeg hold (~a few s).
Table demonstrations: **3** (①②③).

## Open questions
- Keep the one web photo in the hook, or start straight on the graph (saves search time, not render time)?
- OK to drop the min-plus / matrix-multiplication remark? (It's what makes "repeated squaring" make sense; v4
  keeps squaring only as one row of the cost table.)
