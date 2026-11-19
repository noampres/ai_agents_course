"""Reusable drawing helpers for the Floyd-Warshall video (graph, matrix, formula strip).

Every helper takes explicit state, so other segments can import this module:

    sys.path.insert(0, "<project>/segments/07_fw_demo")
    import fw_draw as fd
    c = fd.Canvas()
    fd.draw_title(c)
    fd.draw_formula(c)
    fd.draw_graph(c)
    fd.draw_matrix(c, fd.matrix_cells(fd.INITIAL))
    img = c.finish()          # 1280x720 PIL RGB image

Drawing happens at SS x resolution and is downsampled for anti-aliasing.
All coordinates passed to Canvas methods are in final 1280x720 pixels.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from common import spec  # noqa: E402

# Running example graph: shared data lives in common/spec.py
INF = spec.INF
NODES = spec.NODES
IDX = {n: i for i, n in enumerate(NODES)}
EDGES = [(u, v, w) for (u, v), w in spec.EDGES.items()]   # list of (u, v, weight)
NODE_POS = spec.NODE_POS
NODE_R = spec.NODE_R

# ---- Layout constants local to this module (candidates for common/spec.py) ----
EDGE_CURVE = 34            # sideways bulge of the two arcs of a 2-way pair (px)

# Formula strip directly under the title bar, full stage width.
FORMULA_BOX = (40, 82, spec.W - 40, 138)
FORMULA_TEXT = "dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])"

# Distance matrix inside spec.MATRIX_BOX (640..1240).
CELL = 88                  # matrix cell size (px)
HEAD = 60                  # header row/column size (px)
MAT_W = HEAD + 4 * CELL    # 412
MAT_X0 = (spec.MATRIX_BOX[0] + spec.MATRIX_BOX[2] - MAT_W) // 2   # 734
MAT_Y0 = 166               # top of the column-header row
CAPTION_Y = MAT_Y0 + HEAD + 4 * CELL + 58   # centre line of the arithmetic/summary caption

# k-round indicator, right side of the title bar.
K_BOX = (spec.W - 220, 12, spec.W - 40, 58)

FADE = spec.FADE           # default fade length (s), scaled with narration speed

def initial_dist(nodes=NODES, edges=spec.EDGES):
    """Initial dist table from the edge dict: 0 on the diagonal, edge weight, else INF."""
    return [[0 if u == v else edges.get((u, v), INF) for v in nodes] for u in nodes]


INITIAL = initial_dist()
assert INITIAL == [[0, 3, INF, 7], [8, 0, 2, INF], [5, INF, 0, 1], [2, INF, INF, 0]]


# ---- Algorithm ---------------------------------------------------------------
def floyd_warshall(dist0):
    """Return (rounds, final, nxt). rounds[k] = list of (i, j, old, new, via_ik, via_kj)
    in loop order; nxt is the successor table of the final shortest paths."""
    n = len(dist0)
    d = [row[:] for row in dist0]
    nxt = [[(j if d[i][j] < INF and i != j else None) for j in range(n)] for i in range(n)]
    rounds = []
    for k in range(n):
        ups = []
        for i in range(n):
            for j in range(n):
                cand = d[i][k] + d[k][j]
                if cand < d[i][j]:
                    ups.append((i, j, d[i][j], cand, d[i][k], d[k][j]))
                    d[i][j] = cand
                    nxt[i][j] = nxt[i][k]
        rounds.append(ups)
    return rounds, d, nxt


def path_nodes(nxt, i, j):
    """Vertex indices of the path i -> j according to successor table nxt."""
    if nxt[i][j] is None:
        return None
    p = [i]
    while p[-1] != j:
        p.append(nxt[p[-1]][j])
    return p


def fmt(v):
    return "∞" if v == INF else str(int(v))


# ---- Easing / envelopes -------------------------------------------------------
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def ease(x):
    """Smoothstep-like ease in/out on [0, 1]."""
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def env(t, t_in, t_out=INF, fade=FADE):
    """Alpha that fades in starting at t_in and fades out starting at t_out."""
    return ease((t - t_in) / fade) * (1 - ease((t - t_out) / fade))


def mix(c0, c1, a):
    a = clamp01(a)
    return tuple(int(round(x + (y - x) * a)) for x, y in zip(c0, c1))


# ---- Canvas ---------------------------------------------------------------------
class Canvas:
    SS = 2  # supersampling factor

    def __init__(self, bg=spec.BG):
        self.img = Image.new("RGB", (spec.W * self.SS, spec.H * self.SS), bg)
        self.d = ImageDraw.Draw(self.img)
        self._fonts = {}

    def font(self, path, px):
        key = (str(path), px)
        if key not in self._fonts:
            self._fonts[key] = ImageFont.truetype(str(path), int(px * self.SS))
        return self._fonts[key]

    def _p(self, pts):
        s = self.SS
        return [(x * s, y * s) for x, y in pts]

    def rect(self, box, fill=None, outline=None, width=1, radius=0):
        s = self.SS
        b = [box[0] * s, box[1] * s, box[2] * s, box[3] * s]
        if radius:
            self.d.rounded_rectangle(b, radius=radius * s, fill=fill, outline=outline,
                                     width=int(width * s))
        else:
            self.d.rectangle(b, fill=fill, outline=outline, width=int(width * s))

    def line(self, pts, fill, width=2):
        self.d.line(self._p(pts), fill=fill, width=int(width * self.SS), joint="curve")

    def dashed(self, pts, fill, width=2, dash=14, gap=10):
        """Dashed polyline (pts densely sampled)."""
        acc, on = 0.0, True
        seg = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            L = math.dist(a, b)
            acc += L
            seg.append(b)
            if acc >= (dash if on else gap):
                if on:
                    self.line(seg, fill, width)
                seg, acc, on = [b], 0.0, not on
        if on and len(seg) > 1:
            self.line(seg, fill, width)

    def polygon(self, pts, fill):
        self.d.polygon(self._p(pts), fill=fill)

    def circle(self, c, r, fill=None, outline=None, width=1):
        s = self.SS
        self.d.ellipse([(c[0] - r) * s, (c[1] - r) * s, (c[0] + r) * s, (c[1] + r) * s],
                       fill=fill, outline=outline, width=int(width * s))

    def text(self, xy, txt, fill, path=spec.FONT_SANS, px=32, anchor="mm"):
        self.d.text((xy[0] * self.SS, xy[1] * self.SS), txt, fill=fill,
                    font=self.font(path, px), anchor=anchor)

    def text_w(self, txt, path, px):
        return self.font(path, px).getlength(txt) / self.SS

    def runs(self, xy, runs, anchor="m"):
        """Draw a sequence of (text, color, fontpath, px) runs; anchor 'm' centres the whole
        line on xy, 'l' starts it at xy. Vertical anchor: middle."""
        total = sum(self.text_w(t, f, p) for t, _, f, p in runs)
        x = xy[0] - total / 2 if anchor == "m" else xy[0]
        for t, col, f, p in runs:
            self.text((x, xy[1]), t, col, f, p, anchor="lm")
            x += self.text_w(t, f, p)
        return total

    def finish(self):
        return self.img.resize((spec.W, spec.H), Image.LANCZOS)


# ---- Title bar / k indicator / formula ----------------------------------------
def draw_title(c, title="Floyd–Warshall", k_label=None, k_alpha=0.0):
    """Title bar: title on the left, divider line, optional 'k = X' pill on the right."""
    x0, y0, x1, y1 = spec.TITLE_BAR
    c.text((40, (y0 + y1) / 2), title, spec.FG, spec.FONT_SANS_BOLD, 38, anchor="lm")
    c.line([(x0, y1 - 1), (x1, y1 - 1)], spec.GRID, 2)
    if k_label:
        draw_k(c, k_label, k_alpha)


def draw_k(c, k_label, alpha=1.0, box_alpha=None):
    """'k = X' round indicator pill in the title bar. Call several times with different
    labels/alphas to crossfade the letter; box_alpha (default alpha) controls the frame."""
    if box_alpha is None:
        box_alpha = alpha
    if box_alpha > 0.01:
        c.rect(K_BOX, outline=mix(spec.BG, spec.ACCENT, box_alpha), width=3, radius=23)
    if alpha > 0.01:
        cx, cy = (K_BOX[0] + K_BOX[2]) / 2, (K_BOX[1] + K_BOX[3]) / 2
        c.text((cx, cy), f"k = {k_label}", mix(spec.BG, spec.ACCENT, alpha),
               spec.FONT_MONO_BOLD, 34)


def draw_formula(c, alpha=1.0):
    if alpha <= 0.01:
        return
    c.rect(FORMULA_BOX, outline=mix(spec.BG, spec.GRID, alpha), width=2, radius=10)
    cy = (FORMULA_BOX[1] + FORMULA_BOX[3]) / 2
    c.text((spec.W / 2, cy), FORMULA_TEXT, mix(spec.BG, spec.FG, alpha), spec.FONT_MONO, 30)


# ---- Graph ------------------------------------------------------------------------
def _edge_geom(u, v):
    """Sampled points (from node boundary to node boundary) and label point of edge u->v."""
    pairs = {(a, b) for a, b, _ in EDGES}
    (x0, y0), (x1, y1) = NODE_POS[u], NODE_POS[v]
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    nx, ny = dy / L, -dx / L            # perpendicular (left of travel in screen coords)
    bulge = EDGE_CURVE if (v, u) in pairs else 0
    cx, cy = (x0 + x1) / 2 + nx * bulge * 2, (y0 + y1) / 2 + ny * bulge * 2
    pts = []
    for s in range(41):
        t = s / 40
        x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1
        y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1
        pts.append((x, y))
    # clip to node circles
    r = NODE_R + 2
    pts = [p for p in pts if math.dist(p, (x0, y0)) > r and math.dist(p, (x1, y1)) > r]
    mid = pts[len(pts) // 2]
    off = 30 if bulge else 0
    if not bulge:   # single edge: put label to the side of the straight line
        off = 26
    label = (mid[0] + nx * off, mid[1] + ny * off)
    return pts, label


def _arrow(c, pts, col, width):
    (xa, ya), (xb, yb) = pts[-3], pts[-1]
    ang = math.atan2(yb - ya, xb - xa)
    size = 10 + width * 1.6
    tip = (xb + math.cos(ang) * 2, yb + math.sin(ang) * 2)
    left = (tip[0] - size * math.cos(ang - 0.45), tip[1] - size * math.sin(ang - 0.45))
    right = (tip[0] - size * math.cos(ang + 0.45), tip[1] - size * math.sin(ang + 0.45))
    c.polygon([tip, left, right], col)
    return pts[:-2] + [(xb - math.cos(ang) * size * 0.7, yb - math.sin(ang) * size * 0.7)]


def draw_graph(c, rings=None, paths=None):
    """rings: {node: [(color, alpha), ...]} extra outline rings (outermost last).
    paths: list of (node_list, color, alpha, dashed) highlighted paths drawn over edges."""
    rings = rings or {}
    paths = paths or []
    # base edges
    for u, v, w in EDGES:
        pts, lab = _edge_geom(u, v)
        body = _arrow(c, pts, spec.MUTED, 3)
        c.line(body, spec.MUTED, 3)
    # highlighted paths
    for nodes, col, a, dashed in paths:
        if a <= 0.01 or not nodes:
            continue
        cc = mix(spec.MUTED, col, a)
        width = 3 + 4 * a
        for u, v in zip(nodes, nodes[1:]):
            pts, _ = _edge_geom(u, v)
            body = _arrow(c, pts, cc, width)
            if dashed:
                c.dashed(body, cc, width)
            else:
                c.line(body, cc, width)
    # weight labels (on top of lines, with BG backing)
    for u, v, w in EDGES:
        pts, lab = _edge_geom(u, v)
        c.circle(lab, 19, fill=spec.BG)
        c.text(lab, str(w), spec.FG, spec.FONT_SANS_BOLD, 30)
    # nodes
    for n, (x, y) in NODE_POS.items():
        c.circle((x, y), NODE_R, fill=spec.BG, outline=spec.FG, width=3)
        r = NODE_R
        for col, a in rings.get(n, []):
            if a <= 0.01:
                continue
            r += 7
            c.circle((x, y), r, outline=mix(spec.BG, col, a), width=5)
        c.text((x, y + 1), n, spec.FG, spec.FONT_SANS_BOLD, 36)


# ---- Matrix -------------------------------------------------------------------------
def cell_box(i, j):
    x = MAT_X0 + HEAD + j * CELL
    y = MAT_Y0 + HEAD + i * CELL
    return (x, y, x + CELL, y + CELL)


def matrix_cells(dist):
    """Plain cell state from a distance table (no transitions)."""
    return [[{"text": fmt(dist[i][j]), "color": spec.FG} for j in range(4)] for i in range(4)]


def _value(c, box, txt, col, dy=0.0):
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + dy
    if txt == "∞":
        c.text((cx, cy - 2), txt, col, spec.FONT_SANS_BOLD, 54)
    else:
        c.text((cx, cy), txt, col, spec.FONT_MONO_BOLD, 42)


def draw_matrix(c, cells, pivot=None, outlines=None, header_hl=None, label="dist"):
    """cells[i][j]: dict with
         text, color                     current value
         old (optional): text of the previous value, strike (0..1 strike line progress),
                         swap (0..1 crossfade old -> new)
         mark (optional): 0..1 alpha of a GOOD underline marking an improved value
       pivot: (k, alpha) pivot cross (row k + column k tinted, ACCENT frame)
       outlines: list of (i, j, color, alpha, width) cell outlines
       header_hl: {('r'|'c', idx): (color, alpha)} header label colouring
       label: text for the top-left corner cell (e.g. "dist"), or None"""
    outlines = outlines or []
    header_hl = header_hl or {}
    tint = mix(spec.BG, spec.ACCENT, 0.16)
    # pivot tint
    if pivot and pivot[1] > 0.01:
        k, a = pivot
        for t in range(4):
            for (i, j) in ((k, t), (t, k)):
                c.rect(cell_box(i, j), fill=mix(spec.BG, tint, a))
    # grid
    x0, y0 = MAT_X0 + HEAD, MAT_Y0 + HEAD
    for t in range(5):
        c.line([(x0 + t * CELL, y0), (x0 + t * CELL, y0 + 4 * CELL)], spec.GRID, 2)
        c.line([(x0, y0 + t * CELL), (x0 + 4 * CELL, y0 + t * CELL)], spec.GRID, 2)
    # headers
    if label:
        c.text((MAT_X0 + HEAD / 2 - 2, MAT_Y0 + HEAD / 2 + 4), label, spec.MUTED,
               spec.FONT_MONO, 28)
    for t, n in enumerate(NODES):
        for kind in ("r", "c"):
            col, wt = spec.FG, spec.FONT_SANS_BOLD
            if pivot and pivot[1] > 0.01 and pivot[0] == t:
                col = mix(spec.FG, spec.ACCENT, pivot[1])
            if (kind, t) in header_hl:
                hc, ha = header_hl[(kind, t)]
                col = mix(col, hc, ha)
            if kind == "c":
                pos = (x0 + t * CELL + CELL / 2, MAT_Y0 + HEAD / 2 + 4)
            else:
                pos = (MAT_X0 + HEAD / 2, y0 + t * CELL + CELL / 2)
            c.text(pos, n, col, wt, 36)
    # values
    for i in range(4):
        for j in range(4):
            cell = cells[i][j]
            box = cell_box(i, j)
            under = tint if (pivot and pivot[1] > 0.5 and pivot[0] in (i, j)) else spec.BG
            if "old" in cell:
                sw = ease(cell.get("swap", 0))
                # old value is struck through, then slides up and fades while the new
                # value slides in from below (never two values on top of each other)
                if sw < 1:
                    dy = -16 * sw
                    oc = mix(under, spec.MUTED, 1 - sw)
                    _value(c, box, cell["old"], oc, dy)
                    st = ease(cell.get("strike", 0))
                    if st > 0:
                        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + dy
                        xa, xb = cx - 28, cx + 28
                        c.line([(xa, cy + 14), (xa + (xb - xa) * st, cy + 14 - 28 * st)],
                               mix(under, spec.BAD, 1 - sw), 5)
                if sw > 0.5:
                    a = (sw - 0.5) * 2
                    _value(c, box, cell["text"], mix(under, cell["color"], a), 16 * (1 - a))
            else:
                _value(c, box, cell["text"], cell["color"])
            m = cell.get("mark", 0)
            if m > 0.01:
                cx = (box[0] + box[2]) / 2
                c.rect((cx - 22, box[3] - 16, cx + 22, box[3] - 11),
                       fill=mix(under, spec.GOOD, m))
    # pivot frame (shape cue for the cross)
    if pivot and pivot[1] > 0.01:
        k, a = pivot
        col = mix(spec.BG, spec.ACCENT, a)
        r0 = cell_box(k, 0)
        r1 = cell_box(k, 3)
        c.rect((r0[0], r0[1], r1[2], r1[3]), outline=col, width=3)
        c0 = cell_box(0, k)
        c1 = cell_box(3, k)
        c.rect((c0[0], c0[1], c1[2], c1[3]), outline=col, width=3)
    # cell outlines (current cell, operands)
    for i, j, col, a, width in outlines:
        if a <= 0.01:
            continue
        b = cell_box(i, j)
        ins = width / 2 + 1
        c.rect((b[0] + ins, b[1] + ins, b[2] - ins, b[3] - ins),
               outline=mix(spec.BG, col, a), width=width, radius=6)


def draw_caption(c, runs, alpha=1.0, y=CAPTION_Y):
    """Centered caption line under the matrix.
    runs = [(text, color, font, px[, run_alpha]), ...]; layout is fixed by all runs, so
    runs can fade in one by one without the line shifting."""
    if alpha <= 0.01 or not runs:
        return
    cx = (spec.MATRIX_BOX[0] + spec.MATRIX_BOX[2]) / 2
    out = []
    for r in runs:
        t, col, f, p = r[:4]
        ra = r[4] if len(r) > 4 else 1.0
        cc = mix(spec.BG, col, alpha * ra)
        # the mono font's ∞ is small: draw it with the bold sans glyph, a bit larger
        for n, piece in enumerate(t.split("∞")):
            if n:
                out.append(("∞", cc, spec.FONT_SANS_BOLD, p + 8))
            if piece:
                out.append((piece, cc, f, p))
    c.runs((cx, y), out)
