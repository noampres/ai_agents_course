# 04_extend_demo: edge-by-edge walkthrough (L⁽¹⁾ → L⁽²⁾ → L⁽³⁾)

Render (from anywhere):

```
/home/noam_wsl_admin/claude_projects/kokoro-video/.venv/bin/python render.py            # out/segment.mp4, first/last_frame.png, script.txt
/home/noam_wsl_admin/claude_projects/kokoro-video/.venv/bin/python render.py --frames   # also dumps one PNG per cue into frames/ (git-ignored)
```

- TTS is cached in `out/tts/`, keyed by lang + voice + `spec.SPEED` + text. Cue times come from
  Kokoro's word timestamps (`^name` markers in `LINES` in render.py).
- The algorithm runs in code: `render.py` computes L⁽²⁾, L⁽³⁾ with the min-plus product from
  `spec.EDGES`, asserts them against SCRIPT_OUTLINE.md, checks L⁽³⁾ = Floyd–Warshall and
  L⁽⁴⁾ = L⁽³⁾, and derives the worked-cell rows, the changed cells, the paths and the
  narration numbers for the "rest of" lines from the computation.
- Audio: lines trimmed, 0.18 s gaps (+0.02 s pad each side ≤ `spec.MAX_GAP`), speech starts at
  0.10 s, tail 0.31 s; two-pass `loudnorm` to `spec.LUFS` (measured −16.3 LUFS integrated).
- All durations are scaled by `spec.TIME_SCALE` (narration at `spec.SPEED` = 1.5).

Output: **44.46 s**, 1280×720, 30 fps CFR, h264 yuv420p, AAC 24 kHz mono.

## Beats (timings at SPEED 1.5)

| # | Beat | Start–end (s) | On screen |
|---|---|---|---|
| 1 | intro | 0.10–4.06 | "m = 2" pill fades in; target cell B→D gets an INFO outline, INFO headers, INFO rings on B and D |
| 2 | bands | 4.25–9.61 | row B tinted ACCENT + frame, then column D |
| 3 | row0 | 9.80–12.04 | graph crossfades to the work table (left half); row "A 8 + 7 = 15" fills word by word; operands L[B][A], W[A][D] get ACCENT outlines |
| 4 | row1 | 12.22–14.01 | "B 0 + ∞ = ∞" |
| 5 | row2 | 14.19–15.30 | "C 2 + 1 = 3" |
| 6 | row3 | 15.48–18.50 | "D ∞ + 0 = ∞" with note "k = D: + 0 keeps the old value" |
| 7 | min | 18.69–20.05 | min row framed + "= 3" circled in GOOD, other rows dim |
| 8 | write | 20.23–23.65 | work table crossfades back to the graph; path B→C→D grows in GOOD; ∞ struck in BAD → 3 in GOOD; labels L⁽¹⁾ → L⁽²⁾ |
| 9 | rest2 | 23.83–29.01 | A→C 5, B→A 7, C→A 3, C→B 8, D→B 5 flash in one by one (GOOD outline + underline) |
| 10 | m3 | 29.20–31.69 | GOOD fades back to FG; pill m = 2 → 3; labels L⁽²⁾ → L⁽³⁾ |
| 11 | featured | 31.87–36.81 | A→D outlined INFO, rings on A, D; path A→B→C→D grows; caption `A→B→C→D 3 + 2 + 1 = 6 < 7`; 7 struck → 6 |
| 12 | rest3 | 36.99–40.19 | B→A 5, C→B 6, D→C 7 flash in |
| 13 | close | 40.37–44.15 | colours back to FG; the "≤ n − 1 = 3 edges" pill pulses ACCENT once and settles |

Narration: `script.txt` (one line per beat). The first line continues from 03's
"That's matrix multiplication, with plus instead of times and min instead of sum."

## Layout

Graph and matrix are drawn by `segments/07_fw_demo/fw_draw.py` (imported, read-only), so
they are pixel-identical to 07: nodes at `spec.NODE_POS`, matrix `spec.MATRIX_*`
(cells x 794–1146, y 226–578), formula strip `spec.FORMULA_BOX`, pill `spec.ROUND_BOX`.
Additions of this segment (in `extend_draw.py`):

- Title "Edge by Edge" + title-bar label `L⁽ᵐ⁾ = shortest paths, at most m edges`, right-aligned
  to x = 1036 (just left of the pill).
- Corner label `L⁽ᵐ⁾` in the matrix header corner (L MUTED, superscript ACCENT).
- Superscripts are drawn as real raised `(m)` runs at ≥ 28 px, not Unicode superscript glyphs.
- `N1_PILL_BOX = (940, 646, 1240, 690)`: "≤ n − 1 = 3 edges" pill (2 px MUTED frame, bold 28 px).
- Work table: in the left half (`PANEL`), crossfaded with the graph (`swap_panel`), since it
  does not fit around the 88 px matrix. The graph is restored pixel-exactly.
- Caption at y = 612 (not `spec.CAPTION_Y` = 636, which would touch the n − 1 pill).

## Handoff frames

- **First frame** (`first_frame.png` = `extend_draw.handoff_frame(1)`): title "Edge by Edge",
  title-bar label "L⁽¹⁾ = shortest paths, at most 1 edge", **no** m pill, formula strip
  `L⁽ᵐ⁾[i][j] = min over k ( L⁽ᵐ⁻¹⁾[i][k] + W[k][j] )`, graph with all edges MUTED, matrix
  W = L⁽¹⁾ (0 3 ∞ 7 / 8 0 2 ∞ / 5 ∞ 0 1 / 2 ∞ ∞ 0) with corner label L⁽¹⁾, n − 1 pill. No highlights.
- **Last frame** (`last_frame.png` = `extend_draw.handoff_frame(3)`): same layout, label
  "L⁽³⁾ = shortest paths, at most 3 edges", "m = 3" pill, matrix L⁽³⁾ (0 3 5 6 / 5 0 2 3 /
  3 6 0 1 / 2 5 7 0) all FG, corner label L⁽³⁾, n − 1 pill unlit. No highlights, no caption.

`render.py` asserts both frames are byte-identical to `handoff_frame(1)` / `handoff_frame(3)`.

## Using extend_draw.py from other segments (03, 05, 02)

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "04_extend_demo"))
import extend_draw as xd

img = xd.handoff_frame(1)     # 03's last frame must equal this (02 can end on it too)
img = xd.handoff_frame(3)     # 05's first frame

c = xd.Canvas()
xd.draw_title(c, m=1)                     # or label_mix=(1, 2, a) to crossfade the label
xd.draw_m(c, 2)                           # "m = 2" pill
xd.draw_formula_strip(c, alpha)           # fade the recurrence in (03)
xd.draw_graph(c, rings={"B": [(spec.INFO, 1)]}, paths=[(["B", "C", "D"], spec.GOOD, 1, False)])
xd.draw_matrix(c, xd.W_MATRIX, m=1, overrides=..., bands=..., outlines=..., header_hl=...)
xd.draw_n1_pill(c, pulse=0)
img = c.finish()
```

Also exported: `extend_tables()`, `min_plus()`, `path_of()`, `changed_cells()`,
`draw_work_table()`, `swap_panel()`, `draw_caption()`, `math_runs()` / `draw_runs()`
(text with superscripts), `env()` (uses `spec.FADE`), `ease`, `mix`.
