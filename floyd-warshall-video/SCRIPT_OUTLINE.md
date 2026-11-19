# All-Pairs Shortest Paths → Floyd–Warshall: Script Structure (DRAFT v2)

Target length: ~6 min. One continuous narration in the same voice; segments are joined
with 0.4 s crossfades (see CLAUDE.md). Each segment lists its **handoff**: what's on
screen at its last frame, which must be what the next segment starts with.

**Story arc:** the problem → the natural approach (grow paths one edge at a time) →
what it costs → Floyd–Warshall's smarter idea → side-by-side comparison → recap.

---

## Running example (shared by ALL segments; data lives in `common/spec.py`)

Directed, weighted graph, 4 vertices **A, B, C, D** (n = 4):

| Edge | Weight |
|---|---|
| A → B | 3 |
| A → D | 7 |
| B → A | 8 |
| B → C | 2 |
| C → A | 5 |
| C → D | 1 |
| D → A | 2 |

`W` = L⁽¹⁾ (shortest paths using **at most 1 edge**), row = from, col = to:

|   | A | B | C | D |
|---|---|---|---|---|
| A | 0 | 3 | ∞ | 7 |
| B | 8 | 0 | 2 | ∞ |
| C | 5 | ∞ | 0 | 1 |
| D | 2 | ∞ | ∞ | 0 |

### Algorithm 1: Extend-by-one-edge (paths of at most k edges)

`L⁽ᵏ⁾[i][j]` = shortest i→j path using **at most k edges**.
`L⁽ᵏ⁾[i][j] = min over all m of ( L⁽ᵏ⁻¹⁾[i][m] + W[m][j] )` (the last edge is m→j).
A shortest path never needs more than n − 1 = 3 edges, so L⁽³⁾ is the answer.

L⁽²⁾ (changed cells in **bold**):

|   | A | B | C | D |
|---|---|---|---|---|
| A | 0 | 3 | **5** | 7 |
| B | **7** | 0 | 2 | **3** |
| C | **3** | **8** | 0 | 1 |
| D | 2 | **5** | ∞ | 0 |

L⁽³⁾ (= final answer):

|   | A | B | C | D |
|---|---|---|---|---|
| A | 0 | 3 | 5 | **6** |
| B | **5** | 0 | 2 | 3 |
| C | 3 | **6** | 0 | 1 |
| D | 2 | 5 | **7** | 0 |

Worked cell to show in full detail, **L⁽²⁾[B][D]** (row B of L⁽¹⁾ "dot" column D of W, with + and min):

| via m | L⁽¹⁾[B][m] | + W[m][D] | = |
|---|---|---|---|
| A | 8 | 7 | 15 |
| B | 0 | ∞ | ∞ |
| C | 2 | 1 | **3** ← min |
| D | ∞ | 0 | ∞ |

### Algorithm 2: Floyd–Warshall updates per round

- **k = A:** B→D = 15, C→B = 8, D→B = 5
- **k = B:** A→C = 5, D→C = 7
- **k = C:** A→D = 6, B→A = 7, B→D = 3
- **k = D:** B→A = 5, C→A = 3, C→B = 6

Final `dist` is identical to L⁽³⁾ above.

---

## 01_hook: The problem (~20 s)

- **On screen:** real photos from the web (see CLAUDE.md "Images from the web"): cars on a
  highway, then a city road map; the map cross-dissolves into the drawn graph, with four cities
  becoming A–D. The title bar fades in; the graph settles on the left.
- **Beats:**
  1. "Imagine a map of cities with one-way roads, each with a travel cost."
  2. "We want the shortest route between *every* pair of cities: all-pairs shortest paths."
  3. "Let's start with the most natural idea, then make it much faster."
- **Handoff →** graph on left (`GRAPH_BOX`), right half empty.

## 02_setup: The distance table (~25 s)

- **On screen:** matrix builds in the right half from the edges.
- **Beats:**
  1. "Store distances in a table: row is where you start, column is where you end."
  2. "Zero on the diagonal, the edge weight where there's a direct road, infinity elsewhere."
  3. "This table is exactly the best you can do using at most one edge."
- **Handoff →** graph left + W matrix right, labelled "L⁽¹⁾ · at most 1 edge".

## 03_extend_idea: Grow paths one edge at a time (~30 s)

- **On screen:** a path on the graph grows edge by edge; recurrence appears in the formula strip.
- **Beats:**
  1. "What if we allow two edges? Any such path is a shorter path plus one final edge m→j."
  2. "So: try every possible last stop m, and keep the cheapest."
  3. Formula: `L⁽ᵏ⁾[i][j] = min over m of ( L⁽ᵏ⁻¹⁾[i][m] + W[m][j] )`
  4. "That's matrix multiplication, with plus instead of times and min instead of sum."
- **Handoff →** demo layout (graph left, L⁽¹⁾ right, formula strip), no highlights.

## 04_extend_demo: Walkthrough with tables (~60 s) ← subagent "extend-demo"

- **On screen:** graph + matrix + formula strip + "at most k edges" indicator; a small
  side "work table" for the worked cell.
- **Beats:**
  1. **Worked cell L⁽²⁾[B][D] in full:** highlight row B of L⁽¹⁾ and column D of W, fill the
     4-row work table (via A: 8+7=15, via B: ∞, via C: 2+1=**3**, via D: ∞), and draw the path B→C→D.
  2. **Rest of L⁽²⁾ fast:** the other changed cells flash in (A→C, B→A, C→A, C→B, D→B).
  3. **L⁽³⁾, medium:** narrate one change (A→D: 7 → 6 via A→B→C→D), flash the others.
  4. "Three edges is the most any shortest path here needs, so L⁽³⁾ is our answer."
- **Handoff →** final matrix (L⁽³⁾), no highlights.

## 05_extend_cost: What it costs (~30 s)

- **On screen:** cost breakdown builds as a small table; then the "repeated squaring" trick.
- **Beats:**
  1. "Each new table: n² cells, each a min over n choices: n³ work."
  2. "We need n − 1 tables, so Θ(n⁴) time; memory stays O(n²), keeping only two tables."
  3. "Trick: since it's a matrix product, square instead: L¹ → L² → L⁴ → L⁸…"
  4. "Only about log n products: Θ(n³ log n). Better, but can we reach plain n³?"

  | Variant | Time | Space |
  |---|---|---|
  | Extend one edge at a time | Θ(n⁴) | Θ(n²) |
  | Repeated squaring | Θ(n³ log n) | Θ(n²) |

- **Handoff →** cost table in the right half, graph left. (05 → 06 can keep the cost table
  small in a corner so it can come back in 08.)

## 06_fw_idea: Floyd–Warshall's insight (~35 s)

- **On screen:** back to demo layout with W; a single cell (B→D = ∞) highlighted; detour
  B→A→D on the graph; FW formula replaces the previous one in the strip.
- **Beats:**
  1. "Floyd and Warshall changed the question: instead of *how many edges*, ask *which vertices may we pass through*."
  2. "Round k: may we use vertex k as a stepping stone?"
  3. Formula: `dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])`
  4. "One comparison per cell, not a min over every vertex."
- **Handoff →** demo layout, FW formula strip visible, no highlights.

## 07_fw_demo: Walkthrough (~90 s) ← subagent "fw-demo"

- **On screen:** graph + matrix + formula strip; k-round indicator.
- **Beats:**
  1. **k = A, in full detail:** pivot row/column A highlighted; animate the 3 improvements
     (B→D, C→B, D→B) with the detour path drawn on the graph.
  2. **k = B, medium:** narrate the 2 improvements.
  3. **k = C and k = D, fast:** updates flash, with a short summary line.
  4. "After the last round, every entry is the true shortest distance, the same table as before."
- **Handoff →** final matrix, no highlights, formula strip still visible.

## 08_compare: Why Floyd–Warshall wins (~40 s)

- **On screen:** both pseudocodes side by side (4 loops vs 3 loops), then the comparison table.
- **Beats:**
  1. "Side by side: the edge-count method needs a fourth loop, a min over every middle vertex, for each of n rounds."
  2. "Floyd–Warshall does one O(1) check per cell per round: n rounds × n² cells = Θ(n³)."
  3. "It also updates a single table in place, with no second copy."
  4. "Same answer, a factor of n faster than the naive version, and log n faster than squaring."

  | | Edge-count (naive) | Edge-count (squaring) | Floyd–Warshall |
  |---|---|---|---|
  | Subproblem | paths ≤ k edges | paths ≤ 2ʲ edges | intermediates ⊆ {1..k} |
  | Work per round | Θ(n³) | Θ(n³) | Θ(n²) |
  | Rounds | n − 1 | ⌈log₂(n−1)⌉ | n |
  | **Time** | **Θ(n⁴)** | **Θ(n³ log n)** | **Θ(n³)** |
  | Space | Θ(n²) (2 tables) | Θ(n²) | Θ(n²) (1 table, in place) |
  | n = 1000 → ops | ~10¹² | ~10¹⁰ | ~10⁹ |

- **Handoff →** comparison table centered.

## 09_notes: Caveats (~25 s)

- **On screen:** three cards appear in turn.
- **Beats:**
  1. "Negative edge weights are fine for both."
  2. "A negative value on the diagonal at the end means a negative cycle."
  3. "For huge sparse graphs, running Dijkstra from every vertex can beat n³."
- **Handoff →** cards.

## 10_recap: Wrap-up (~15 s)

- **On screen:** cards collapse into a one-line summary; graph returns.
- **Beats:**
  1. "Growing paths edge by edge works, but costs n⁴."
  2. "Floyd–Warshall asks which vertices to pass through, and gets all pairs in n³."
- **End:** hold 1.5 s on the final frame (the only place a longer hold is allowed).

---

## Open questions

- Show indices 0–3 instead of letters A–D to match code? (Letters are easier to read aloud.)
- Show repeated squaring's L⁽⁴⁾ on screen, or only mention it in narration? (Here L⁽⁴⁾ = L⁽³⁾.)
- Light or dark theme? `spec.py` currently uses dark.
