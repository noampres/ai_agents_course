# 07_fw_demo: Floyd–Warshall walkthrough

Render (from this folder):

```
../../../kokoro-video/.venv/bin/python render.py            # out/segment.mp4, first/last_frame.png, script.txt
../../../kokoro-video/.venv/bin/python render.py --frames   # also dumps a PNG every 0.5 s into frames/ (git-ignored)
```

TTS clips are cached in `out/tts/` (keyed by text + voice + speed). The algorithm runs in code;
`render.py` asserts the per-round updates and final matrix against SCRIPT_OUTLINE.md, and
checks that each narration line names the right numbers.

Output: 64.50 s, 1280×720, 30 fps, h264 yuv420p, AAC 24 kHz mono, −16.2 LUFS integrated.
Speech starts at 0.14 s; tail after the last word is 0.49 s.

## Beats

| # | Start–end (s) | Kind | Narration |
|---|---|---|---|
| 1 | 0.12–7.74 | k = A intro | Let's start with k equals A. Row A and column A form the pivot cross, … |
| 2 | 7.96–12.35 | check B→C | 8 + ∞ = ∞ ≥ 2, rejected |
| 3 | 12.57–17.10 | check B→D | 8 + 7 = 15 < ∞, **update**, path B→A→D |
| 4 | 17.32–21.01 | check C→B | 5 + 3 = 8 < ∞, **update**, path C→A→B |
| 5 | 21.23–25.03 | check C→D | 5 + 7 = 12 ≥ 1, rejected (dashed red C→A→D) |
| 6 | 25.25–28.45 | check D→B | 2 + 3 = 5 < ∞, **update**, path D→A→B |
| 7 | 28.67–32.79 | check D→C | 2 + ∞ = ∞ ≥ ∞, rejected |
| 8 | 33.01–36.11 | k = B intro | Now k equals B, so paths may pass through A and B. |
| 9 | 36.33–38.41 | check A→C | 3 + 2 = 5, **update**, path A→B→C |
| 10 | 38.63–44.38 | check D→C | 5 + 2 = 7, **update**, path D→A→B→C |
| 11 | 44.60–51.74 | k = C fast | A→D 6 • B→A 7 • B→D 3 |
| 12 | 51.96–57.01 | k = D fast | B→A 5 • C→A 3 • C→B 6 |
| 13 | 57.23–64.02 | final | …every entry is now the true shortest distance, the same table the edge-by-edge method found. |

Gaps between beats are 0.22 s of silence (+ 0.02 s trim padding each side).

## Visual language

- Pivot k: row k and column k tinted ACCENT with an ACCENT frame; header letters ACCENT;
  ACCENT ring on node k; "k = X" pill at the right of the title bar.
- Current cell (i, j): INFO outline, row/col headers INFO, INFO rings on nodes i and j.
- Operands dist[i][k], dist[k][j]: thick ACCENT outlines.
- Detour path on the graph: thick GOOD solid (accepted) or BAD dashed (rejected).
- Update: old value gets a red strike, slides up and fades; new value slides in, GOOD with an
  underline bar until the round ends, then back to FG.
- Caption under the matrix (y≈636): arithmetic `B→D  8 + 7 = 15 < ∞ ✓` / round summary.

## Layout constants (fw_draw.py)

Graph data and node positions come from `common/spec.py` (`NODES`, `EDGES`, `NODE_POS`,
`NODE_R`): A (170, 300), B (470, 300), C (470, 590), D (170, 590), r = 36. Two-way pairs
(A↔B, A↔D) are quadratic arcs with 34 px bulge (`EDGE_CURVE`); weight labels 30 px bold on a BG disc.

Local constants (candidates for spec.py): `FORMULA_BOX = (40, 82, 1240, 138)` (mono 30 px,
GRID rounded frame), matrix `CELL = 88`, `HEAD = 60`, `MAT_X0 = 734`, `MAT_Y0 = 166`
(cells span x 794–1146, y 226–578), `CAPTION_Y = 636`, `K_BOX = (1060, 12, 1240, 58)`.
Title "Floyd–Warshall" bold 38 px at x = 40, GRID divider at y = 69.

`fw_draw.py` is importable by other segments: `Canvas`, `draw_title`, `draw_k`, `draw_formula`,
`draw_graph(rings, paths)`, `draw_matrix(cells, pivot, outlines, header_hl, label)`,
`draw_caption`, `matrix_cells`, `floyd_warshall`, `ease`, `env`, `mix`.

## Handoff frames

- **First frame:** title bar "Floyd–Warshall" (no k pill), formula strip, graph with all 7
  edges in MUTED and white nodes, initial matrix (0 3 ∞ 7 / 8 0 2 ∞ / 5 ∞ 0 1 / 2 ∞ ∞ 0)
  in FG, `dist` corner label. No highlights, no caption.
- **Last frame:** identical layout, final matrix (0 3 5 6 / 5 0 2 3 / 3 6 0 1 / 2 5 7 0) all
  in FG, no k pill, no highlights, no caption, formula strip still visible.
