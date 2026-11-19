# 02_problem: the problem, precisely

Render (from this folder):

```
../../../kokoro-video/.venv/bin/python render.py            # out/segment.mp4, first/last_frame.png, script.txt
../../../kokoro-video/.venv/bin/python render.py --frames   # also dumps one PNG per cue / beat end into frames/ (git-ignored)
```

TTS clips are cached in `out/tts/` (key = voice + `spec.SPEED` + text). Every event time is derived
from Kokoro word timestamps (`^` cue markers in `BEATS`). Drawing reuses `segments/07_fw_demo/fw_draw.py`
(Canvas, edge geometry, cell boxes, value glyphs, title), imported via `sys.path`; 07 is not modified.
`render.py` asserts the W table, the 8+7 / 2+1 sums, that the baseline line is one sentence, that every
text line fits its box, and that at most 2 weight flights overlap.

Output: **35.23 s** at `SPEED` 1.5, 1280×720, 30 fps, h264 yuv420p, AAC 24 kHz mono, −16.1 LUFS.
Speech starts at 0.12 s; gaps between lines 0.15–0.18 s (≤ `MAX_GAP`); tail 0.32 s (≤ `TAIL`).

## Beats

| # | Start–end (s) | Narration (script.txt) | Visual |
|---|---|---|---|
| 1 | 0.12–3.18 | We're given a directed graph with n vertices, here four, and a weight on every edge. | Right half: "INPUT" + 3 bullets fade in on the words; the 4 nodes pulse (ACCENT ring) on "four"; the 7 weight labels pulse (ACCENT ring + color) on "weight" |
| 2 | 3.32–9.82 | A path's length is the sum of its weights. From B to D, going through A costs eight plus seven, … but going through C costs only two plus one, which is three. | "PATH LENGTH = sum of its weights"; B→A→D dashed BAD with a travelling dot + `B→A→D 8 + 7 = 15`; then B→C→D solid GOOD + `2 + 1 = 3 ✓`, the BAD path dims |
| 3 | 9.96–14.04 | The goal is an n by n table: the entry in row i, column j, is the shortest distance from i to j. | Beats 1–2 fade out; "OUTPUT shortest distance i → j" in the top band; grid strokes in at the standard matrix position, headers fade in, 16 "?" (MUTED) on "n by n"; corner shows i╲j; row header B (INFO) on "row i", column header D on "column j", cell B,D INFO outline + INFO rings on B, D on "from i to j" |
| 4 | 14.18–19.07 | Weights may even be negative, as long as no cycle has a negative total. Otherwise you could loop forever, … | OUTPUT line → assumption card (650,80)–(1230,160): "negative weights: allowed ✓" / "negative cycles: forbidden ✗" + small BAD 3-cycle icon; a dot loops around it on "loop forever" |
| 5 | 19.21–22.92 | The obvious fix is to run Bellman-Ford from every vertex, which costs up to theta of n to the fourth. | Pill on the caption line: `n × Bellman–Ford ≈ Θ(n⁴)` (Θ(n⁴) BAD, appears on "theta"); dashed ACCENT spokes fan out from A, B, C, D in turn (≤ 2 sources at once); pill fades at the end of the line |
| 6 | 23.07–26.96 | Also, a shortest path never repeats a vertex, so it uses at most n minus one, here three, edges. | Card text → "no repeats ⇒ ≤ n − 1 = 3 edges"; path A→B→C→D (3 edges, 4 vertices) GOOD with dot; at the line end the card shrinks (MOVE) into the title-bar pill |
| 7 | 27.11–32.32 | What do we know for sure? The direct roads: zero from a city to itself, the edge weight where a road exists, and infinity where there's none yet. | "?" → 0 on the diagonal on "zero"; on "edge weight" each of the 7 edges flashes ACCENT and a copy of its weight flies into its cell (0.33 s each, 0.18 s stagger, ≤ 2 in flight), lands ACCENT then settles to FG; on "infinity" the 5 remaining cells become ∞; corner hint fades |
| 8 | 32.47–34.93 | This table, W, is the best we can do using at most one edge. | Corner label "W" fades in on "W"; on "at most one edge" it crossfades to "L⁽¹⁾" and the caption "at most 1 edge" fades in |

## Handoff frames

- **First frame** (= 01_hook's handoff): title "All-Pairs Shortest Paths" (bold 38, divider at y 69),
  graph at `spec.NODE_POS` pixel-identical to 07_fw_demo's graph, right half empty BG. No formula strip, no pill.
- **Last frame**: same title + graph (no highlights); W matrix at `MATRIX_X0/Y0` (cells 794–1146 × 226–578),
  values `0 3 ∞ 7 / 8 0 2 ∞ / 5 ∞ 0 1 / 2 ∞ ∞ 0` in FG; corner label "L⁽¹⁾" (MUTED); caption
  "at most 1 edge" at `CAPTION_Y`; the "≤ n − 1 = 3 edges" pill in the title bar. No formula strip, no round pill.

## Elements that later segments must keep (exact values)

| Element | Spec |
|---|---|
| **"≤ n − 1 = 3 edges" pill** | box **(740, 12)–(1040, 58)** (same height as `ROUND_BOX`, 20 px left of it), radius 23, 2 px `MUTED` outline, no fill; text centred at (890, 35): "≤ " + **"n − 1"** + " = 3 edges", DejaVu Sans 28, FG with "n − 1" in DejaVu Sans Bold 28 `ACCENT`. Fits between the title (ends x≈548) and `ROUND_BOX` (starts 1060); never overlaps the formula strip, matrix or caption |
| Corner label "L⁽¹⁾" | runs centred at (762, 200): "L" DejaVu Sans 32 + "⁽¹⁾" DejaVu Sans 40 (the font's superscript glyphs), both `MUTED` |
| Caption | "at most 1 edge", DejaVu Sans 30, `FG`, centred at (940, `CAPTION_Y`=636) |
| Matrix values | as fw_draw: digits DejaVu Sans Mono Bold 42, ∞ DejaVu Sans Bold 54, FG; headers DejaVu Sans Bold 36 FG |
