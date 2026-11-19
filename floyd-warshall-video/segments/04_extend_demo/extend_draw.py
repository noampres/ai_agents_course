"""Drawing helpers for the edge-by-edge part of the video (segments 03_extend_idea,
04_extend_demo, 05_extend_cost), built on the standard demo layout of
segments/07_fw_demo/fw_draw.py (Canvas, graph, matrix and caption are imported from there,
so the graph and matrix are pixel-identical to the Floyd–Warshall demo).

Notation (SCRIPT_OUTLINE v3): m = max number of edges (L^(m), "m = 2" pill),
k = the last stop before j (the vertex the min runs over).

Usage from another segment:

    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "04_extend_demo"))
    import extend_draw as xd

    img = xd.handoff_frame(1)     # exact first frame of 04 (= what 03 must end on)
    img = xd.handoff_frame(3)     # exact last frame of 04 (= what 05 starts from)

    # or compose a frame yourself:
    c = xd.Canvas()
    xd.draw_title(c, m=1)                    # "Edge by Edge" + "L(1) = shortest paths ..."
    xd.draw_m(c, 2)                          # optional "m = 2" pill (spec.ROUND_BOX)
    xd.draw_formula_strip(c)                 # L^(m)[i][j] = min over k ( ... )
    xd.draw_graph(c)                         # fw_draw.draw_graph (rings=, paths=)
    xd.draw_matrix(c, xd.W_MATRIX, m=1)      # fw_draw matrix + "L(1)" corner label
    xd.draw_n1_pill(c)                       # "<= n - 1 = 3 edges" reminder pill
    img = c.finish()

Colours are opaque mixes toward the colour underneath ("alpha"), so BG is the only
background colour.
"""
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "segments" / "07_fw_demo"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
from common import spec  # noqa: E402
import fw_draw as fd  # noqa: E402  (read-only dependency: the layout standard)

Canvas = fd.Canvas
draw_graph = fd.draw_graph
cell_box = fd.cell_box
mix, ease, clamp01, fmt = fd.mix, fd.ease, fd.clamp01, fd.fmt

INF = spec.INF
NODES = spec.NODES
N = len(NODES)
IDX = {v: i for i, v in enumerate(NODES)}

# ---- Layout --------------------------------------------------------------------------
TITLE = "Edge by Edge"
FORMULA_TEXT = "L^(m)[i][j] = min over k ( L^(m−1)[i][k] + W[k][j] )"   # ^(..) = superscript
TITLE_LABEL_RIGHT = spec.ROUND_BOX[0] - 24     # "L(2) = shortest paths ..." ends here
CORNER = (spec.MATRIX_X0, spec.MATRIX_Y0, spec.MATRIX_X0 + spec.MATRIX_HEAD,
          spec.MATRIX_Y0 + spec.MATRIX_HEAD)
CAPTION_Y = 612            # above the n-1 pill (spec.CAPTION_Y = 636 would touch it)

# "<= n - 1 = 3 edges" reminder pill, bottom right of the right half (from segment 02 on).
N1_PILL_BOX = (spec.W - 40 - 300, spec.H - 30 - 44, spec.W - 40, spec.H - 30)  # 940,646-1240,690
N1_PILL_TEXT = f"≤ n − 1 = {N - 1} edges"

# Left-half panel used while the graph is faded out (worked-cell work table).
PANEL = (0, 140, 630, spec.H)                  # region crossfaded between graph and table
WT_TITLE_Y = 196
WT_COLS = (70, 210, 190, 100)                  # k | L(m-1)[i][k] | + W[k][j] | =
WT_W = sum(WT_COLS)
WT_X0 = (spec.GRAPH_BOX[0] + spec.GRAPH_BOX[2] - WT_W) // 2
WT_Y0 = 236
WT_HEAD = 56
WT_ROW = 60
WT_NOTE_Y = WT_Y0 + WT_HEAD + 4 * WT_ROW + 44  # note line under the table


def env(t, t_in, t_out=INF, fade=spec.FADE):
    """0 -> 1 fade starting at t_in, 1 -> 0 fade starting at t_out (spec.FADE long)."""
    return ease((t - t_in) / fade) * (1 - ease((t - t_out) / fade))


# ---- Algorithm -----------------------------------------------------------------------
def weight_matrix():
    return fd.initial_dist()


def min_plus(L, W):
    """One extension step: out[i][j] = min over k of L[i][k] + W[k][j].
    Returns (out, arg), arg[i][j] = the minimising k (first one on ties)."""
    out = [[INF] * N for _ in range(N)]
    arg = [[None] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            for k in range(N):
                v = L[i][k] + W[k][j]
                if v < out[i][j]:
                    out[i][j], arg[i][j] = v, k
    return out, arg


def extend_tables(mmax=N - 1):
    """([L1, ..., L_mmax], [None, arg2, ...])."""
    W = weight_matrix()
    Ls, args = [W], [None]
    for _ in range(2, mmax + 1):
        L, a = min_plus(Ls[-1], W)
        Ls.append(L)
        args.append(a)
    return Ls, args


def path_of(Ls, args, m, i, j):
    """Vertex names of a shortest i->j path with at most m edges."""
    if Ls[m - 1][i][j] == INF:
        return None
    if i == j:
        return [NODES[i]]
    if m == 1:
        return [NODES[i], NODES[j]]
    k = args[m - 1][i][j]
    if k == j:                                   # k = j: no extra edge, the old value
        return path_of(Ls, args, m - 1, i, j)
    return path_of(Ls, args, m - 1, i, k) + [NODES[j]]


def changed_cells(prev, cur):
    """Row-major list of (i, j, old, new) where cur differs from prev."""
    return [(i, j, prev[i][j], cur[i][j]) for i in range(N) for j in range(N)
            if cur[i][j] != prev[i][j]]


W_MATRIX = weight_matrix()


# ---- Text with real superscripts -------------------------------------------------------
def math_runs(expr, color, font, px, sup_color=None, sup_px=spec.MIN_TEXT_PX, sup_font=None):
    """'L^(2)[B][k]' -> runs (text, colour, font, px, raise); '^(...)' becomes a superscript
    drawn with real parentheses at >= MIN_TEXT_PX (not tiny Unicode superscript glyphs)."""
    sup_color = sup_color or color
    sup_font = sup_font or font
    out, rest = [], expr
    while "^(" in rest:
        a, b = rest.split("^(", 1)
        inner, rest = b.split(")", 1)
        if a:
            out.append((a, color, font, px, 0))
        out.append((f"({inner})", sup_color, sup_font, sup_px, 0.36 * px))
    if rest:
        out.append((rest, color, font, px, 0))
    return out


def draw_runs(c, xy, runs, anchor="m"):
    """Runs (text, colour, font, px[, raise]) on one baseline; xy = (x, visual line centre).
    anchor 'm' centres, 'l' starts at x, 'r' ends at x. Returns the width."""
    runs = [r if len(r) > 4 else (*r, 0) for r in runs]
    total = sum(c.text_w(t, f, p) for t, _, f, p, _ in runs)
    x = {"m": xy[0] - total / 2, "l": xy[0], "r": xy[0] - total}[anchor]
    base_px = max(p for _, _, _, p, r in runs if not r)
    base = xy[1] + 0.36 * base_px
    for t, col, f, p, rz in runs:
        c.text((x, base - rz), t, col, f, p, anchor="ls")
        x += c.text_w(t, f, p)
    return total


# ---- Title bar, m pill, formula strip --------------------------------------------------
def draw_title(c, m=None, label_mix=None):
    """fw_draw title bar with TITLE, plus 'L(m) = shortest paths, at most m edges'
    right-aligned before the round pill. label_mix=(m0, m1, a) crossfades the text."""
    fd.draw_title(c, TITLE)
    if label_mix:
        m0, m1, a = label_mix
        _title_label(c, m0, 1 - ease(a))
        _title_label(c, m1, ease(a))
    elif m is not None:
        _title_label(c, m, 1.0)


def _title_label(c, m, alpha):
    if alpha <= 0.01:
        return
    fg, ac = mix(spec.BG, spec.FG, alpha), mix(spec.BG, spec.ACCENT, alpha)
    edges = "edge" if m == 1 else "edges"
    runs = math_runs(f"L^({m})", fg, spec.FONT_SANS_BOLD, 32, sup_color=ac) + [
        (" = shortest paths, at most ", fg, spec.FONT_SANS, 28),
        (str(m), ac, spec.FONT_SANS_BOLD, 28),
        (f" {edges}", fg, spec.FONT_SANS, 28)]
    draw_runs(c, (TITLE_LABEL_RIGHT, (spec.TITLE_BAR[1] + spec.TITLE_DIVIDER_Y) / 2), runs,
              anchor="r")


def draw_m(c, m, alpha=1.0, box_alpha=None):
    """Round 'm = 2' pill in spec.ROUND_BOX (same look as fw_draw's 'k = A' pill).
    Draw twice (box_alpha 1 / 0) with complementary alphas to crossfade the number."""
    box_alpha = alpha if box_alpha is None else box_alpha
    if box_alpha > 0.01:
        c.rect(spec.ROUND_BOX, outline=mix(spec.BG, spec.ACCENT, box_alpha), width=3, radius=23)
    if alpha > 0.01:
        b = spec.ROUND_BOX
        c.text(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2), f"m = {m}",
               mix(spec.BG, spec.ACCENT, alpha), spec.FONT_MONO_BOLD, 34)


def draw_formula_strip(c, alpha=1.0, text=FORMULA_TEXT):
    """spec.FORMULA_BOX with the edge-by-edge recurrence, mono 30 px."""
    if alpha <= 0.01:
        return
    b = spec.FORMULA_BOX
    c.rect(b, outline=mix(spec.BG, spec.GRID, alpha), width=2, radius=10)
    draw_runs(c, (spec.W / 2, (b[1] + b[3]) / 2),
              math_runs(text, mix(spec.BG, spec.FG, alpha), spec.FONT_MONO, 30))


def draw_n1_pill(c, pulse=0.0, alpha=1.0):
    """'<= n - 1 = 3 edges' pill; pulse 0..1 lights it up in ACCENT with a thicker frame."""
    if alpha <= 0.01:
        return
    p = clamp01(pulse)
    g = 4 * p
    b = N1_PILL_BOX
    c.rect((b[0] - g, b[1] - g, b[2] + g, b[3] + g),
           outline=mix(spec.BG, mix(spec.MUTED, spec.ACCENT, p), alpha), width=2 + 2 * p,
           radius=22)
    c.text(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2), N1_PILL_TEXT,
           mix(spec.BG, mix(spec.FG, spec.ACCENT, p), alpha), spec.FONT_SANS_BOLD, 28)


# ---- Matrix ----------------------------------------------------------------------------
def matrix_cells(values, overrides=None):
    """fw_draw cell dicts from a value table; overrides {(i, j): dict(old=num, new=num,
    strike, swap, color, mark)} turn a cell into an old -> new transition."""
    cells = fd.matrix_cells(values)
    for (i, j), st in (overrides or {}).items():
        d = {"text": fmt(st.get("new", values[i][j])), "color": st.get("color", spec.FG)}
        if "old" in st:
            d.update(old=fmt(st["old"]), strike=st.get("strike", 0), swap=st.get("swap", 0))
        if st.get("mark"):
            d["mark"] = st["mark"]
        cells[i][j] = d
    return cells


def _corner_label(c, m, alpha):
    if alpha <= 0.01:
        return
    runs = math_runs(f"L^({m})", mix(spec.BG, spec.MUTED, alpha), spec.FONT_SANS_BOLD, 34,
                     sup_color=mix(spec.BG, spec.ACCENT, alpha))
    draw_runs(c, (CORNER[2] - 4, (CORNER[1] + CORNER[3]) / 2 + 4), runs, anchor="r")


def draw_matrix(c, values, m=None, label_mix=None, overrides=None, bands=None,
                outlines=None, header_hl=None):
    """values: 4x4 numbers.  m: corner label 'L(m)'; label_mix=(m0, m1, a) crossfades it.
       overrides: see matrix_cells.  bands: [('r'|'c', idx, colour, alpha)] tinted row /
       column with a frame (like fw_draw's pivot cross).  outlines: [(i, j, colour, alpha,
       width[, inset])].  header_hl: fw_draw header colouring {('r'|'c', idx): (col, a)}."""
    bands = bands or []
    for kind, idx, col, a in bands:
        if a <= 0.01:
            continue
        for t in range(N):
            i, j = (idx, t) if kind == "r" else (t, idx)
            c.rect(cell_box(i, j), fill=mix(spec.BG, col, 0.16 * a))
    fd.draw_matrix(c, matrix_cells(values, overrides), header_hl=header_hl, label=None)
    if label_mix:
        m0, m1, a = label_mix
        _corner_label(c, m0, 1 - ease(a))
        _corner_label(c, m1, ease(a))
    elif m is not None:
        _corner_label(c, m, 1.0)
    for kind, idx, col, a in bands:
        if a <= 0.01:
            continue
        b0 = cell_box(idx, 0) if kind == "r" else cell_box(0, idx)
        b1 = cell_box(idx, N - 1) if kind == "r" else cell_box(N - 1, idx)
        c.rect((b0[0], b0[1], b1[2], b1[3]), outline=mix(spec.BG, col, a), width=3)
    for o in outlines or []:
        i, j, col, a, width = o[:5]
        inset = o[5] if len(o) > 5 else 0
        if a <= 0.01:
            continue
        b = cell_box(i, j)
        ins = width / 2 + 1 + inset
        c.rect((b[0] + ins, b[1] + ins, b[2] - ins, b[3] - ins),
               outline=mix(spec.BG, col, a), width=width, radius=6)


def draw_caption(c, runs, alpha=1.0, y=CAPTION_Y):
    fd.draw_caption(c, runs, alpha, y)


# ---- Work table (left half, while the graph is faded out) ------------------------------
def wt_cell(r, col):
    x = WT_X0 + sum(WT_COLS[:col])
    y = WT_Y0 if r < 0 else WT_Y0 + WT_HEAD + r * WT_ROW
    return (x, y, x + WT_COLS[col], y + (WT_HEAD if r < 0 else WT_ROW))


def draw_work_table(c, i, j, mprev, rows, alpha=1.0, min_row=None, min_alpha=0.0,
                    note=None, note_alpha=0.0):
    """Worked cell L(mprev+1)[i][j] = min over k of L(mprev)[i][k] + W[k][j].
       rows: one dict per k (NODES order): a=L value, w=W value, alphas 'am' ([k, a]),
             'aw' ([+ w]), 'as' ([= sum]), 'dim' 0..1.
       min_row: row framed + circled in GOOD (min_alpha).  note: INFO line under the table."""
    if alpha <= 0.01:
        return
    fg = mix(spec.BG, spec.FG, alpha)
    ac = mix(spec.BG, spec.ACCENT, alpha)
    title = math_runs(f"L^({mprev + 1})[{NODES[i]}][{NODES[j]}]", fg, spec.FONT_MONO_BOLD, 32,
                      sup_color=ac)
    title += [("  =  min over k of", fg, spec.FONT_SANS, 30)]
    draw_runs(c, ((spec.GRAPH_BOX[0] + spec.GRAPH_BOX[2]) / 2, WT_TITLE_Y), title)
    hc = mix(spec.BG, spec.MUTED, alpha)
    heads = ["k", f"L^({mprev})[{NODES[i]}][k]", f"+ W[k][{NODES[j]}]", "="]
    for col, h in enumerate(heads):
        b = wt_cell(-1, col)
        draw_runs(c, ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2),
                  math_runs(h, hc, spec.FONT_MONO, 30))
    yl = WT_Y0 + WT_HEAD - 2
    c.line([(WT_X0, yl), (WT_X0 + WT_W, yl)], mix(spec.BG, spec.GRID, alpha), 2)
    for r, row in enumerate(rows):
        base = mix(spec.FG, spec.MUTED, row.get("dim", 0))
        parts = [(0, NODES[r], row.get("am", 0), spec.FONT_SANS_BOLD),
                 (1, fmt(row["a"]), row.get("am", 0), spec.FONT_MONO_BOLD),
                 (2, "+ " + fmt(row["w"]), row.get("aw", 0), spec.FONT_MONO_BOLD),
                 (3, "= " + fmt(row["a"] + row["w"]), row.get("as", 0), spec.FONT_MONO_BOLD)]
        for col, txt, a, font in parts:
            a *= alpha
            if a <= 0.01:
                continue
            b = wt_cell(r, col)
            colr = base
            if col == 3 and r == min_row:
                colr = mix(base, spec.GOOD, min_alpha)
            cc = mix(spec.BG, colr, a)
            cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            if "∞" in txt:                       # mono ∞ is tiny: use the bold sans glyph
                pre = txt.replace("∞", "")
                runs = ([(pre, cc, font, 34)] if pre else []) + [("∞", cc, spec.FONT_SANS_BOLD, 42)]
                draw_runs(c, (cx, cy), runs)
            else:
                draw_runs(c, (cx, cy), [(txt, cc, font, 34)])
    if min_row is not None and min_alpha * alpha > 0.01:
        a = min_alpha * alpha
        b = wt_cell(min_row, 3)
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        c.d.ellipse([v * c.SS for v in (cx - 50, cy - 24, cx + 50, cy + 24)],
                    outline=mix(spec.BG, spec.GOOD, a), width=4 * c.SS)
        r0, r2 = wt_cell(min_row, 0), wt_cell(min_row, 2)
        c.rect((r0[0] + 4, r0[1] + 6, r2[2] - 4, r0[3] - 6),
               outline=mix(spec.BG, spec.GOOD, a), width=3, radius=8)
    if note and note_alpha * alpha > 0.01:
        draw_runs(c, ((spec.GRAPH_BOX[0] + spec.GRAPH_BOX[2]) / 2, WT_NOTE_Y),
                  math_runs(note, mix(spec.BG, spec.INFO, note_alpha * alpha),
                            spec.FONT_SANS_BOLD, 28))


def swap_panel(img, other, a):
    """Crossfade PANEL (left half below the formula strip) of img toward `other`
    (a = weight of `other`). Both are finished 1280x720 images drawn on BG."""
    if a <= 0.001:
        return img
    box = PANEL
    if a >= 0.999:
        img.paste(other.crop(box), box[:2])
    else:
        img.paste(Image.blend(img.crop(box), other.crop(box), a), box[:2])
    return img


# ---- Handoff frames -------------------------------------------------------------------
def rest_frame(values, m, show_m_pill):
    c = Canvas()
    draw_title(c, m=m)
    if show_m_pill:
        draw_m(c, m)
    draw_formula_strip(c)
    draw_graph(c)
    draw_matrix(c, values, m=m)
    draw_n1_pill(c)
    return c.finish()


def handoff_frame(m):
    """m=1: first frame of 04_extend_demo (03 must end on this picture: no m pill).
       m=3: last frame of 04_extend_demo (05 starts from it): L3 and the 'm = 3' pill."""
    Ls, _ = extend_tables()
    return rest_frame(Ls[m - 1], m, show_m_pill=(m != 1))
