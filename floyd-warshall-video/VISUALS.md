# Visual Plan per Segment (PROPOSAL v1)

Companion to `SCRIPT_OUTLINE.md` (narration) and `CLAUDE.md` (rules). All coordinates are
for a 1280×720 canvas and come from `common/spec.py`; anything marked **NEW** should be added
to `spec.py` before more segments are built.

---

## 0. Global visual system (all segments)

| Element | Exact spec |
|---|---|
| Background | solid `BG` on every frame; photos are the only exception (see 01, 10) |
| Title bar | `TITLE_BAR` (0,0)–(1280,70), fill `BG` lightened 6 %, 1 px `GRID` bottom rule. Chapter title left-aligned at x=40, DejaVu Sans Bold 34 px, `FG`. Chapter tag right-aligned at x=1240, 28 px `MUTED` (e.g. "1 / 3") |
| Chapter titles | 01–02 "All-Pairs Shortest Paths" · 03–05 "Edge by Edge" · 06–07 "Floyd–Warshall" · 08 "Head to Head" · 09–10 "All-Pairs Shortest Paths". The title text crossfades (0.3 s) when the chapter changes; the bar itself never moves |
| Formula strip **NEW** `FORMULA_BOX` | (40,85)–(1240,155), rounded 12 px, fill `GRID` at 35 %, formula in DejaVu Sans Mono 30 px centered; colored sub-terms (see per segment) |
| Graph | nodes at `NODE_POS`, radius `NODE_R`=36, fill `BG`, 3 px `FG` ring, label Bold 32 px. Edges 3 px `MUTED` with 14 px arrowheads stopping at the ring. Two-way pairs A↔B and A↔D are two arcs bent ±18 px. Weight labels in rounded pills (fill `BG`, 1 px `GRID`), Mono 28 px, at the arc midpoint offset outward |
| Path highlight | edge recolored + widened to 6 px, plus a moving dot (12 px) traveling along the path over 0.6 s; the color tells the role (`INFO` = existing path, `ACCENT` = detour/new edge, `GOOD` = accepted result) |
| Matrix **NEW** `MATRIX_CELL`=72 | 5×5 grid (header row/col + 4×4) = 360×360, centered in `MATRIX_BOX` at x=940, top y=220. Header letters Bold 30 px `MUTED`; values Mono 32 px `FG`; ∞ in `MUTED`; diagonal cells tinted `GRID` 25 %. Matrix label above the grid at y=180, 28 px (e.g. "L⁽²⁾ · at most 2 edges") |
| Cell states | *focus*: 3 px `INFO` outline · *pivot row/col*: `ACCENT` 18 % fill · *improved*: value turns `GOOD` + 3 px `GOOD` outline for 0.6 s, old value shown struck through in `BAD` beside it, fading over 0.4 s · *checked, no change*: brief `MUTED` outline |
| Round indicator **NEW** `ROUND_POS` | top-right of matrix box (1240, 180) right-aligned pill, Bold 30 px: "m = 2" (edge method: max edges) / "k = A" (FW: stepping stone) |
| Motion | ease-in-out cubic; fades 0.25 s; moves 0.4–0.6 s; at most 2 elements animate at once |
| Photos | see CLAUDE.md "Images from the web": cover-crop, darken 35 %, desaturate 20 %, corner radius 16 px when not full-frame |

---

## 01_hook: The problem (~20 s)

**Assets (web):** `cars_highway.jpg` (traffic on a multi-lane highway, preferably dusk),
`city_road_map.jpg` (top-down road map or aerial photo of a city road grid).

| Beat | Time | Visual |
|---|---|---|
| 1 "Imagine a map of cities…" | 0–5 s | Full-frame `cars_highway.jpg`, slow push-in 1.00→1.06 scale. No title bar yet |
| 2 "…between every pair…" | 5–12 s | Cross-dissolve (0.8 s) to full-frame `city_road_map.jpg`. Four glowing `ACCENT` markers pop in one by one at the photo's points matching `NODE_POS`, then thin animated lines trace between them along the 7 edges |
| 3 "Let's start with the most natural idea…" | 12–20 s | Photo dims to 0 % over 1 s while the markers morph into graph nodes (rings + labels A–D) and the traced lines become arrows with weight pills. Title bar slides down from y=−70 (0.4 s) |

**Last frame:** title bar "All-Pairs Shortest Paths", graph in `GRAPH_BOX`, right half empty, no strip.

## 02_problem: The problem, precisely (~55 s)

| Beat | Visual |
|---|---|
| 1 Input | Right half: tag "INPUT" (28 px `MUTED`) then "directed graph · n = 4 vertices · weighted edges". All 4 nodes pulse once (n = 4), then all 7 weight pills pulse once |
| 2 Path length | Graph: path B→A→D drawn `BAD` with pill "8 + 7 = 15"; then B→C→D drawn `GOOD` with pill "2 + 1 = 3" and a ✓. Both clear |
| 3 Output | Tag "OUTPUT"; empty 5×5 grid draws in (lines stroke left→right 0.5 s); headers A–D fade in; every cell shows "?" in `MUTED`; hints "from ↓" / "to →" for 2 s. Label above: "goal: shortest distance i → j" |
| 4 Assumption | Card over the bottom of the right half (y 560–680): "no negative cycles" with a tiny 3-node cycle icon labelled "−1 total" struck through in `BAD` |
| 5 Baseline | One pill under the assumption card, Mono 28 px: "n × Bellman–Ford ≈ Θ(n⁴)" with Θ(n⁴) in `BAD`; 4 tiny source arrows fan out from each node in turn (0.15 s each). Pill fades after the line; its text reappears in the 05 cost table as a reference row |
| 6 Key fact | Card text changes to: "⇒ shortest paths use ≤ n − 1 = 3 edges" (`ACCENT` on "n − 1"); the card shrinks to a 300×50 pill at the bottom right that stays until 04 beat 4 (where it pulses once) |
| 7 Starting point | "?" cells replaced: diagonal 0s pop in together; then for each of the 7 edges, in order, the edge flashes `ACCENT` on the graph and a copy of its weight pill flies along a curve into its cell (0.5 s each, overlapping by 0.2 s); remaining 5 cells become ∞ together. Label crossfades to "W" |
| 8 "…at most one edge." | Label crossfades "W" → "L⁽¹⁾ · at most 1 edge" |

**Last frame:** graph left + W matrix right with label, no highlights.

## 03_extend_idea: Grow paths one edge at a time (~30 s)

| Beat | Visual |
|---|---|
| 1 "The most natural idea: allow one more edge…" | Graph: B→C highlighted `INFO` (a ≤1-edge path), then edge C→D extends it in `ACCENT` with the moving dot; caption under the graph (y≈650, 28 px): "≤ m−1 edges + one last edge k→j" |
| 2 "…try every possible last stop k…" | Ghost arrows B→k→D fan out in `MUTED` (dashed) for k = A, then k = C, one at a time; then node D gets a small "k = j: +0" loop badge (the stay-put option); all fade |
| 3 Formula | Formula strip fades in: `L⁽ᵐ⁾[i][j] = min over k ( L⁽ᵐ⁻¹⁾[i][k] + W[k][j] )`; `L⁽ᵐ⁻¹⁾[i][k]` colored `INFO`, `W[k][j]` colored `ACCENT` (same colors as beat 1) |
| 4 "…matrix multiplication…" | Inset card over the matrix area (matrix dims to 25 %): two rows in Mono 30 px: `ordinary:  Σ a·b` → `min-plus:  min (a + b)`; the `Σ`→`min` and `·`→`+` swap with a 0.4 s flip. Card fades out, matrix back to 100 % |

**Last frame:** graph left, L⁽¹⁾ right, formula strip, no highlights (= 04_extend_demo first frame).

## 04_extend_demo: Walkthrough (~60 s) — subagent "extend-demo"

Built by the subagent in `segments/04_extend_demo/`; its README holds the final layout.
Required elements: round indicator "m = 2"/"m = 3"; worked-cell **work table**
(via k | L⁽¹⁾[B][k] | + W[k][D] | =; the "via D" row is labelled "old value"), with each row filling in turn and the min circled in `GOOD`; path B→C→D
on graph in `GOOD`; fast flashes for the other changed cells; A→D 7→6 with path A→B→C→D.

**Last frame:** L⁽³⁾ with label "L⁽³⁾ · at most 3 edges", no highlights, formula strip.

## 05_extend_cost: What it costs (~30 s)

| Beat | Visual |
|---|---|
| 1 "Each new table: n² cells…" | Matrix stays; all 16 cells pulse once (`n²`), then one cell expands a fan of 4 thin lines to row/column (`× n`). Equation builds in the strip: `n² cells × n choices = n³ per table` |
| 2 "…n − 1 tables… Θ(n⁴)" | Matrix shrinks (0.5 s) to a stack of 3 offset "cards" L¹ L² L³ in the right half; strip becomes `(n − 1) × n³ = Θ(n⁴)`, with Θ(n⁴) in `BAD` |
| 3 "Trick: square instead…" | Below the stack, two chip chains, Mono 28 px: naive `L¹→L²→L³→L⁴→…→Lⁿ⁻¹` (many chips, `MUTED`) vs squaring `L¹→L²→L⁴→L⁸` (chips `ACCENT`, arrows labelled "²") |
| 4 "…Θ(n³ log n). Can we reach n³?" | Chains collapse into the 2-row **cost table** (Variant / Time / Space), 28 px; the "Θ(n³)?" question appears as a third row with "?" in `ACCENT` |

**Last frame:** graph left, cost table right. **Handoff note:** in 06 the cost table shrinks
to a 260×90 chip at bottom-right (1240,690 anchor) and stays there until 08.

## 06_fw_idea: Floyd–Warshall's insight (~35 s)

| Beat | Visual |
|---|---|
| 1 "…which vertices may we pass through" | Cost table → corner chip. Matrix fades back in showing **W**, label "dist · start". Title crossfades to "Floyd–Warshall". A row of 4 chips `A B C D` under the matrix label (y≈200): "allowed stops", all `MUTED` |
| 2 "Round k: may we use vertex k…" | Chip A lights `ACCENT`; round indicator "k = A" appears |
| 3 Formula | Strip crossfades to `dist[i][j] = min( dist[i][j], dist[i][k] + dist[k][j] )`; `dist[i][k]` `INFO`, `dist[k][j]` `ACCENT`. Cell B→D gets focus; graph draws B→A (`INFO`) + A→D (`ACCENT`); arithmetic pill near the cell: `8 + 7 = 15 < ∞` |
| 4 "One comparison per cell…" | Arithmetic pill reduces to a single `<` glyph pulsing once; then all highlights clear, B→D reverts to ∞ (it's a preview, 07 does it for real) |

**Last frame:** demo layout: graph, W matrix, FW strip, chips row (A lit), "k = A", corner chip. No cell highlights.

## 07_fw_demo: Walkthrough (~90 s) — subagent "fw-demo"

Built by the subagent in `segments/04_demo/` (to be renamed `07_fw_demo/`). Required to adopt
from this plan: the chips row and corner chip from 06 (or 06 adapts to the subagent's layout, whichever
is finished first sets the standard). Pivot cross in `ACCENT` 18 %, improvements in `GOOD` with old value
struck through, detour path on graph.

**Last frame:** final matrix, no highlights, strip visible.

## 08_compare: Why Floyd–Warshall wins (~40 s)

| Beat | Visual |
|---|---|
| 1 "Side by side…" | Graph and matrix fade out (0.4 s). Two code panels (each 570×380, at x=40 and x=670, y=170), Mono 28 px, line numbers `MUTED`. Left "Edge by edge": 4 nested `for` lines + `min`; right "Floyd–Warshall": 3 `for` lines + `if`. The extra innermost `for m` loop on the left gets a `BAD` outline + tag "× n" |
| 2 "…n rounds × n² cells = Θ(n³)" | Under each panel, a cost line counts up: left `n · n · n · n = n⁴`, right `n · n · n = n³` |
| 3 "…one table, in place" | Small icons under the panels: left two stacked tables "L, L'" ; right a single table with a circular "in place" arrow |
| 4 "Same answer, a factor of n faster…" | Panels slide up and shrink away; **comparison table** (from outline) fills `STAGE`, 28 px, FW column outlined `GOOD`. Last row "n = 1000" shows horizontal bars, log scale: 10¹² (long, `BAD`), 10¹⁰ (`ACCENT`), 10⁹ (short, `GOOD`) |

**Last frame:** comparison table, centered.

## 09_notes: Caveats (~25 s)

Three cards 370×260 at x = 40 / 455 / 870, y = 230, appear left→right, 1 per beat. Cards are drawn,
except card 3 which may use a photo header.

| Card | Visual |
|---|---|
| 1 "Negative weights ✓" | mini graph of 2 nodes with a `−2` edge, ✓ in `GOOD` |
| 2 "Negative cycle" | mini 3×3 matrix with diagonal `−1` cell in `BAD` + outline, caption "dist[i][i] < 0" |
| 3 "Huge & sparse?" | photo header `road_network_aerial.jpg` (130 px tall), caption "weights ≥ 0: n × Dijkstra can beat n³" |

**Last frame:** three cards.

## 10_recap: Wrap-up (~15 s)

**Assets (web):** `gps_navigation.jpg` (phone/car GPS showing a route) *or* `flight_routes.jpg`.

| Beat | Visual |
|---|---|
| 1 "Growing paths edge by edge… n⁴" | Cards collapse into a summary line at y=200: "Edge by edge → Θ(n⁴)" (`BAD` Θ) |
| 2 "Floyd–Warshall… n³" | Second line: "Floyd–Warshall → Θ(n³)" (`GOOD` Θ). Graph returns on the left at 70 % scale; behind everything the GPS photo fades in at 20 % opacity |
| End slide (3 s, see below) | Summary lines, graph and photo cross-dissolve (0.6 s) into the ending slide |

### Ending slide (final ~3 s, the only long hold in the video)

```
┌──────────────────────────────────────────────────────────────┐
│ All-Pairs Shortest Paths                        (title bar)  │
├──────────────────────────────────────────────────────────────┤
│                                    ┌──────────────────────┐  │
│   Thanks for watching!             │                      │  │
│                                    │   CHARACTER IMAGE    │  │
│   Edge by edge    Θ(n⁴)            │   (user-supplied)    │  │
│   Floyd–Warshall  Θ(n³)            │                      │  │
│                                    │                      │  │
│   [mini graph A–D, 45 % scale]     └──────────────────────┘  │
│                                                              │
│  Photos: … (credits strip)                                   │
└──────────────────────────────────────────────────────────────┘
```

| Element | Exact spec |
|---|---|
| Character image slot | `assets/images/ending_character.png` (**supplied by the user**; not downloaded by Claude). Box (800,120)–(1220,640); contain-fit (never crop a character), bottom-aligned. Transparent PNG sits directly on `BG` with a soft `ACCENT` radial glow behind it; an opaque image gets the photo treatment (radius 16, 2 px `GRID` border, no darkening). Entrance: rises 30 px + fades in over 0.5 s, then a gentle 2 % "breathing" scale loop |
| Headline | "Thanks for watching!", DejaVu Sans Bold 48 px, `FG`, at (80,170) |
| Summary | two lines at y=270/330, Mono 32 px; Θ(n⁴) in `BAD`, Θ(n³) in `GOOD` (carried over from beat 2, they just move into place) |
| Mini graph | `NODE_POS` scaled to 45 % and placed at (80,420)–(330,560); edges static, the final shortest path A→B→C→D traced once in `GOOD` |
| Credits strip | y=680, 20 px `MUTED` (exempt from the 28 px rule because it's credits): "Photos: <author> / <source> (license) · …" from `assets/CREDITS.md`; the character image is credited here as its owner requires |
| Fallback | if `ending_character.png` is missing, the left column centers horizontally and the slot is omitted. The build must not fail |
| Audio | narration ends before the slide; the 3 s hold is silent apart from the crossfade tail (the explicit exception to `MAX_GAP`) |

---

## Assets to download (web, per CLAUDE.md rules)

| File | Segment | Content |
|---|---|---|
| `cars_highway.jpg` | 01 | traffic on a highway |
| `city_road_map.jpg` | 01 | top-down city road map / aerial grid |
| `road_network_aerial.jpg` | 09 | large sparse road network |
| `gps_navigation.jpg` or `flight_routes.jpg` | 10 | real-world routing |
| `ending_character.png` | 10 | **user-supplied**, not downloaded (see ending slide) |

## Proposed `spec.py` additions

`FORMULA_BOX=(40,85,1240,155)`, `MATRIX_CELL=72`, `MATRIX_ORIGIN=(760,220)`, `MATRIX_LABEL_Y=180`,
`ROUND_POS=(1240,180)`, `CORNER_CHIP=(980,600,1240,690)`, `CHAPTER_TITLES` dict, `PHOTO_DARKEN=0.35`,
`PHOTO_DESAT=0.2`, `RADIUS=16`.

## Open decisions

- Chapter tag in the title bar ("1 / 3") yes/no?
- 09 card 3: photo header or fully drawn?
- 10: GPS photo or flight-route photo?
