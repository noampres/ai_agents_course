# All-Pairs Shortest Paths → Floyd–Warshall: Script Structure (DRAFT v3)

Target length: ~5.5 min (narration at 1.2× speed, `spec.SPEED`). One continuous narration in the same voice; segments are joined
with ~0.33 s crossfades (`spec.XFADE`) (see CLAUDE.md). Each segment lists its **handoff**: what's on
screen at its last frame, which must be what the next segment starts with.

**Story arc:** motivation → the problem stated precisely (input, output, assumptions) →
the natural approach (grow paths one edge at a time) → what it costs → Floyd–Warshall's
smarter idea → side-by-side comparison → caveats → recap.

**Notation (fixed for the whole video):**
- `n` = number of vertices (here 4). `i` = start, `j` = end.
- `k` is ALWAYS a **vertex** used as a stepping stone: the last stop before j in the
  edge-by-edge method, the allowed intermediate vertex in Floyd–Warshall.
- `m` = the **maximum number of edges** in the edge-by-edge method: `L⁽ᵐ⁾`.
- `W` = direct-edge table, `L⁽ᵐ⁾` = edge-by-edge tables, `dist` = Floyd–Warshall's table.

---

## Running example (shared by ALL segments; data lives in `common/spec.py`)

Directed, weighted graph, 4 vertices **A, B, C, D** (n = 4), no negative cycles:

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

### Algorithm 1: Edge by edge (paths of at most m edges)

`L⁽ᵐ⁾[i][j]` = shortest i→j path using **at most m edges**.
`L⁽ᵐ⁾[i][j] = min over all k of ( L⁽ᵐ⁻¹⁾[i][k] + W[k][j] )` (the last edge is k→j).
Choosing k = j adds W[j][j] = 0, which keeps paths that don't need an extra edge.
Without negative cycles a shortest path never repeats a vertex, so it has at most
n − 1 = 3 edges, which makes L⁽³⁾ the answer.

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

Worked cell to show in full detail, **L⁽²⁾[B][D]** (row B of L⁽¹⁾ combined with column D of W, using + and min):

| via k | L⁽¹⁾[B][k] | + W[k][D] | = |
|---|---|---|---|
| A | 8 | 7 | 15 |
| B | 0 | ∞ | ∞ |
| C | 2 | 1 | **3** ← min |
| D | ∞ | 0 | ∞ (k = D means "no extra edge": the old value) |

### Algorithm 2: Floyd–Warshall updates per round

- **k = A:** B→D = 15, C→B = 8, D→B = 5
- **k = B:** A→C = 5, D→C = 7
- **k = C:** A→D = 6, B→A = 7, B→D = 3
- **k = D:** B→A = 5, C→A = 3, C→B = 6

Final `dist` is identical to L⁽³⁾ above. (The in-between tables differ from L⁽²⁾: they
mean "only stepping stones up to k", not "at most m edges". Don't present them as equal.)

---

## 01_hook: Motivation (~17 s)

- **On screen:** photos of cars on a highway, then a city road map; four cities become A–D and
  the map dissolves into the drawn graph. The title bar fades in.
- **Beats:**
  1. "Imagine a map of cities with one-way roads, each with a travel cost."
  2. "A navigation app doesn't just need one route; it may need the cheapest route between *every* pair of cities."
  3. "That's called the all-pairs shortest-paths problem. Let's state it precisely."
- **Handoff →** graph on left (`GRAPH_BOX`), right half empty.

## 02_problem: The problem, precisely (~46 s)

- **On screen:** labels on the graph, an example path comparison, the empty goal table,
  the assumption card, a one-line baseline cost pill, then the starting table built from the edges.
- **Beats:**
  1. **Input:** "We're given a directed graph with n vertices, here four, and a weight on every edge."
  2. **Path length:** "A path's length is the sum of its weights. From B to D, going through A costs 8 + 7 = 15, but going through C costs only 2 + 1 = 3."
  3. **Output:** "The goal is an n-by-n table: the entry in row i, column j is the shortest distance from i to j." (empty table, cells show "?")
  4. **Assumption:** "Weights may even be negative, as long as no cycle has a negative total. Otherwise you could loop forever and 'shortest' would have no meaning."
  5. **Baseline (one line):** "The obvious fix: run a single-source algorithm from every vertex. With negative weights that's Bellman–Ford n times: up to Θ(n⁴)."
  6. **Key fact:** "Also, a shortest path never repeats a vertex, which means it uses at most n − 1 edges."
  7. **Starting point:** "What do we know for sure? The direct roads: zero from a city to itself, the edge weight where a road exists, infinity where there's none yet."
  8. "This table, W, is the best we can do using at most one edge."
- **Handoff →** graph left + W matrix right, labelled "L⁽¹⁾ · at most 1 edge".

## 03_extend_idea: Grow paths one edge at a time (~25 s)

- **On screen:** a path on the graph grows edge by edge; recurrence appears in the formula strip.
- **Beats:**
  1. "The most natural idea: allow one more edge at a time. A path with at most two edges is a path with at most one edge, plus one final edge from some vertex k to j."
  2. "So try every possible last stop k and keep the cheapest. Picking k = j costs nothing extra, so paths that are already good enough survive."
  3. Formula: `L⁽ᵐ⁾[i][j] = min over k ( L⁽ᵐ⁻¹⁾[i][k] + W[k][j] )`
  4. "That's matrix multiplication, with plus instead of times and min instead of sum."
- **Handoff →** demo layout (graph left, L⁽¹⁾ right, formula strip), no highlights.

## 04_extend_demo: Walkthrough with tables (~50 s) ← subagent "extend-demo"

- **On screen:** graph + matrix + formula strip + "m = …" indicator; a small side "work
  table" for the worked cell.
- **Beats:**
  1. **Worked cell L⁽²⁾[B][D] in full:** highlight row B of L⁽¹⁾ and column D of W; fill the
     4-row work table (via A: 8+7=15, via B: ∞, via C: 2+1=**3**, via D: ∞, which is the old value); draw B→C→D.
  2. **Rest of L⁽²⁾ fast:** the other changed cells flash in (A→C, B→A, C→A, C→B, D→B).
  3. **L⁽³⁾, medium:** narrate one change (A→D: 7 → 6 via A→B→C→D), flash the others.
  4. "Remember, a shortest path needs at most n − 1, here three, edges, so L⁽³⁾ is our answer."
- **Handoff →** final matrix (L⁽³⁾), no highlights.

## 05_extend_cost: What it costs (~25 s)

- **On screen:** cost breakdown builds as a small table; then the "repeated squaring" trick.
- **Beats:**
  1. "Each new table has n² cells, and each cell is a min over n choices of k: n³ work per table."
  2. "We build tables up to L⁽ⁿ⁻¹⁾, about n of them, so Θ(n⁴) time. Memory stays Θ(n²), since we only keep two tables."
  3. "Trick: it's a matrix product, so square instead: L¹ → L² → L⁴ → L⁸…"
  4. "Overshooting past n − 1 edges is harmless, because the answer doesn't change. That's only about log n products: Θ(n³ log n). Better, but can we reach plain n³?"

  | Variant | Time | Space |
  |---|---|---|
  | (baseline) n × Bellman–Ford | Θ(n²·E) ≤ Θ(n⁴) | Θ(n²) |
  | Extend one edge at a time | Θ(n⁴) | Θ(n²) |
  | Repeated squaring | Θ(n³ log n) | Θ(n²) |

- **Handoff →** cost table in the right half, graph left. (06 shrinks it to a corner chip
  that comes back in 08.)

## 06_fw_idea: Floyd–Warshall's insight (~29 s)

- **On screen:** back to the demo layout with W; a single cell (B→D = ∞) highlighted; detour
  B→A→D on the graph; the FW formula replaces the previous one in the strip.
- **Beats:**
  1. "Floyd–Warshall changes the question: instead of *how many edges* a path may use, ask *which vertices it may pass through*."
  2. "Round k adds one vertex, k, to the set of allowed stepping stones."
  3. Formula: `dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])`, i.e. "go through k, or don't."
  4. "That's one comparison per cell per round, instead of a min over every vertex."
- **Handoff →** demo layout, FW formula strip visible, no highlights.

## 07_fw_demo: Walkthrough (~75 s) ← subagent "fw-demo"

- **On screen:** graph + matrix + formula strip; k-round indicator.
- **Beats:**
  1. **k = A, in full detail:** pivot row/column A highlighted; animate the 3 improvements
     (B→D, C→B, D→B) with the detour path drawn on the graph.
  2. **k = B, medium:** narrate the 2 improvements.
  3. **k = C and k = D, fast:** updates flash, with a short summary line.
  4. "After the last round, every entry is the true shortest distance, the same table the edge-by-edge method found."
- **Handoff →** final matrix, no highlights, formula strip still visible.

## 08_compare: Why Floyd–Warshall wins (~33 s)

- **On screen:** both pseudocodes side by side (4 loops vs 3 loops), then the comparison table.
- **Beats:**
  1. "Side by side: the edge-by-edge method has a fourth loop, a min over every k, inside each of its n rounds."
  2. "Floyd–Warshall does one constant-time check per cell per round: n rounds × n² cells = Θ(n³)."
  3. "It also updates a single table in place, with no second copy."
  4. "Same final answer: a factor of n faster than the naive version, and log n faster than squaring."

  | | Edge by edge (naive) | Edge by edge (squaring) | Floyd–Warshall |
  |---|---|---|---|
  | Subproblem | paths with ≤ m edges | paths with ≤ 2ʲ edges | stepping stones ⊆ {first k vertices} |
  | Work per round | Θ(n³) | Θ(n³) | Θ(n²) |
  | Rounds | n − 2 | ⌈log₂(n−1)⌉ | n |
  | **Time** | **Θ(n⁴)** | **Θ(n³ log n)** | **Θ(n³)** |
  | Space | Θ(n²) (2 tables) | Θ(n²) | Θ(n²) (1 table, in place) |
  | n = 1000 → ops | ~10¹² | ~10¹⁰ | ~10⁹ |

- **Handoff →** comparison table centered.

## 09_notes: Caveats (~21 s)

- **On screen:** three cards appear in turn.
- **Beats:**
  1. "Both methods handle negative edge weights."
  2. "And Floyd–Warshall even detects the one forbidden case: if a diagonal entry ends up negative, there's a negative cycle."
  3. "And that every-vertex idea from the start? With non-negative weights on huge sparse graphs, n runs of Dijkstra can beat n³."
- **Handoff →** cards.

## 10_recap: Wrap-up (~13 s + 3 s ending slide)

- **On screen:** cards collapse into two summary lines; graph returns; then the ending slide (see VISUALS.md).
- **Beats:**
  1. "Growing paths edge by edge works, but costs n⁴."
  2. "Floyd–Warshall asks which vertices to pass through instead, and solves all pairs in n³."
- **End:** 3 s ending slide (the only place a longer hold is allowed).

---

## Change log v2 → v3 (logic fixes)

1. **Problem introduced before any algorithm.** New 02_problem (input, path length, output,
   no-negative-cycle assumption, "≤ n − 1 edges" fact). 01 no longer jumps to "the natural idea".
2. **`k` clash removed.** In v2 `k` meant "number of edges" in the edge-by-edge method and
   "stepping-stone vertex" in Floyd–Warshall. Now `m` = number of edges, `k` = vertex in both.
3. **"Why stop at L⁽³⁾" is justified.** The ≤ n − 1 edges fact needs the no-negative-cycle
   assumption, which v2 never stated. It's now stated in 02, and 04 refers back to it.
4. **The "via D" row explained.** k = j adds 0, which keeps the old value; v2's "shorter path +
   one last edge" didn't cover paths that don't need another edge.
5. **Squaring overshoot explained** (L⁴ when only L³ is needed is harmless).
6. **Rounds count** for the naive method: n − 2 products (L² … Lⁿ⁻¹), not n − 1.
7. **Dijkstra caveat** now says "non-negative weights" (it fails with negative edges).
8. **Negative-cycle detection** attributed to Floyd–Warshall specifically.
9. **History:** "Floyd and Warshall changed the question" became "Floyd–Warshall changes the
   question" (Warshall's original paper was on reachability, not distances).
10. **Intermediate tables** of FW ≠ L⁽ᵐ⁾ tables: only the final tables are equal (note added).
11. **Baseline mentioned:** running a single-source algorithm from every vertex (n × Bellman–Ford ≈ Θ(n⁴)), so
    the viewer knows the bar the APSP algorithms must beat; 09 calls back to it with Dijkstra.
12. **Hook:** v2's "every pair" motivation is now a concrete navigation app.

## Open questions

- Show indices 0–3 instead of letters A–D to match code? (Letters are easier to read aloud.)
- Show repeated squaring's L⁽⁴⁾ on screen, or only mention it in narration? (Here L⁽⁴⁾ = L⁽³⁾.)
- Light or dark theme? `spec.py` currently uses dark.
