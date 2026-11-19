"""Segment 02_problem: the all-pairs shortest-paths problem, stated precisely.

Run:  ../../../kokoro-video/.venv/bin/python render.py        (from this folder)
      add --frames to also dump PNG check frames (one per cue / beat end) into frames/

Outputs: out/segment.mp4, first_frame.png, last_frame.png, script.txt
Drawing helpers (Canvas, edge geometry, matrix cell geometry, value glyphs, title) are imported
from segments/07_fw_demo/fw_draw.py, which is not modified.
"""
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "segments" / "07_fw_demo"))
from common import spec  # noqa: E402
import fw_draw as fd  # noqa: E402
from fw_draw import INF, NODES, IDX, ease, mix  # noqa: E402

OUT = HERE / "out"
TTS_CACHE = OUT / "tts"
FRAMES = HERE / "frames"

TS = spec.TIME_SCALE
FADE = spec.FADE
MOVE = spec.MOVE
LEAD = 0.12                    # silence before the first word (< 0.3 s)
PAD = 0.02                     # silence kept on each side of a trimmed clip
GAP = round(0.22 * TS, 3)      # silence between beats; GAP + 2*PAD must be <= MAX_GAP
assert GAP + 2 * PAD <= spec.MAX_GAP
CUE = "^"
TITLE = "All-Pairs Shortest Paths"

# ---- Layout (all in final 1280x720 px) ----------------------------------------------
RX = 670                                   # left edge of right-half text (beats 1-2)
MCX = (spec.MATRIX_BOX[0] + spec.MATRIX_BOX[2]) / 2       # 940: matrix / caption centre
TOP_Y = 120                                # top band line (free in 02: no formula strip)
CARD_BOX = (650, 80, 1230, 160)            # assumption card, above the matrix headers
PILL_BOX = (740, 12, 1040, 58)             # "<= n - 1 = 3 edges" pill, in the title bar
BASE_Y = spec.CAPTION_Y                    # baseline-cost pill sits on the caption line
CAP_FONT, CAP_PX = spec.FONT_SANS, 30      # final caption "at most 1 edge"
LABEL_FONT, LABEL_PX = spec.FONT_MONO, 28  # corner label (same as 07's "dist")
FLY = 0.5 * TS                             # weight fly duration
PULSE = 0.6 * TS                           # hold of a pulse
X0 = spec.MATRIX_X0 + spec.MATRIX_HEAD     # 794
Y0 = spec.MATRIX_Y0 + spec.MATRIX_HEAD     # 226
assert (fd.MAT_X0, fd.MAT_Y0, fd.CELL, fd.HEAD) == (spec.MATRIX_X0, spec.MATRIX_Y0,
                                                    spec.MATRIX_CELL, spec.MATRIX_HEAD)

# ---- Data -------------------------------------------------------------------------------
W_TABLE = fd.initial_dist()
assert W_TABLE == [[0, 3, INF, 7], [8, 0, 2, INF], [5, INF, 0, 1], [2, INF, INF, 0]]
EDGE_ORDER = [(u, v) for (u, v) in spec.EDGES]            # row-major: A->B, A->D, B->A, ...
assert spec.EDGES[("B", "A")] + spec.EDGES[("A", "D")] == 15
assert spec.EDGES[("B", "C")] + spec.EDGES[("C", "D")] == 3
N = len(NODES)

# ---- Beats ------------------------------------------------------------------------------
BEATS = [
    dict(name="input",
         text="We're given a directed graph with ^n vertices, here ^four, and a ^weight on every edge."),
    dict(name="length",
         text="A path's length is the sum of its weights. From B to D, ^going through A costs "
              "eight plus seven, which is fifteen, ^but going through C costs only two plus one, "
              "which is three."),
    dict(name="output",
         text="The goal is an ^n by n table: the entry in ^row i, ^column j, is the shortest "
              "distance ^from i to j."),
    dict(name="assume",
         text="Weights may even be ^negative, as long as ^no cycle has a negative total. "
              "^Otherwise you could loop forever, and shortest would have no meaning."),
    dict(name="baseline",
         text="The obvious fix is to run Bellman-Ford from ^every vertex, which costs up to "
              "^theta of n to the fourth."),
    dict(name="keyfact",
         text="Also, a shortest path never ^repeats a vertex, so it uses at most ^n minus one, "
              "here three, edges."),
    dict(name="start",
         text="What do we know for sure? The direct roads: ^zero from a city to itself, "
              "^the edge weight where a road exists, and ^infinity where there's none yet."),
    dict(name="w",
         text="This table, ^W, is the best we can do using ^at most one edge."),
]
B = {b["name"]: b for b in BEATS}
for b in BEATS:
    assert "\n" not in b["text"]
assert "fifteen" in B["length"]["text"] and "three" in B["length"]["text"]
assert B["baseline"]["text"].count(".") == 1       # baseline stays ONE sentence

# ---- TTS (same approach as 07_fw_demo; cache keyed by voice + speed + text) -------------
_pipe = None


def tts(text):
    global _pipe
    clean = text.replace(CUE, "")
    key = hashlib.sha1(f"{spec.VOICE}|{spec.SPEED}|{clean}".encode()).hexdigest()[:16]
    wav, meta = TTS_CACHE / f"{key}.wav", TTS_CACHE / f"{key}.json"
    if not wav.exists():
        if _pipe is None:
            from kokoro import KPipeline
            _pipe = KPipeline(lang_code=spec.LANG)
        chunks, toks, off = [], [], 0.0
        for r in _pipe(clean, voice=spec.VOICE, speed=spec.SPEED):
            a = np.asarray(r.audio, dtype=np.float32)
            for t in (r.tokens or []):
                if t.start_ts is not None:
                    toks.append((t.text, off + t.start_ts))
            chunks.append(a)
            off += len(a) / spec.SR
        TTS_CACHE.mkdir(parents=True, exist_ok=True)
        sf.write(wav, np.concatenate(chunks), spec.SR)
        meta.write_text(json.dumps(toks))
    audio, sr = sf.read(wav, dtype="float32")
    assert sr == spec.SR
    toks = json.loads(meta.read_text())
    loud = np.where(np.abs(audio) > 0.006)[0]
    s0 = max(0, loud[0] - int(PAD * sr))
    s1 = min(len(audio), loud[-1] + int(PAD * sr))
    audio = audio[s0:s1]
    t0 = s0 / sr
    marks, pos = [], 0
    for part in text.split(CUE)[:-1]:
        pos += len(part)
        marks.append(pos)
    tokpos, p = [], 0
    for tt, ts in toks:
        f = clean.find(tt, p)
        if f >= 0:
            tokpos.append((f, ts))
            p = f + len(tt)
    cues = []
    for m in marks:
        ts = next((ts for f, ts in tokpos if f >= m), None)
        if ts is None:
            ts = t0 + (len(audio) / sr) * m / len(clean)
        cues.append(max(0.0, ts - t0))
    return audio, cues


def build_timeline():
    t = LEAD
    clips = []
    for b in BEATS:
        a, cues = tts(b["text"])
        dur = len(a) / spec.SR
        b.update(t0=t, t1=t + dur, dur=dur, cues=[t + c for c in cues])
        clips.append((t, a))
        t += dur + GAP
    total = BEATS[-1]["t1"] - PAD + spec.TAIL
    n = int(round(total * spec.FPS))
    total = n / spec.FPS
    audio = np.zeros(int(round(total * spec.SR)), dtype=np.float32)
    for st, a in clips:
        i = int(round(st * spec.SR))
        audio[i:i + len(a)] += a[: len(audio) - i]
    return audio, n, total


# ---- Envelopes --------------------------------------------------------------------------
def env(t, t_in, t_out=INF, fade=FADE):
    return ease((t - t_in) / fade) * (1 - ease((t - t_out) / fade))


def pulse(t, t_in, hold=PULSE):
    return env(t, t_in, t_in + FADE + hold)


def prog(t, t_in, dur):
    return ease((t - t_in) / dur)


def lerp(a, b, p):
    return a + (b - a) * p


# ---- Graph ------------------------------------------------------------------------------
GEOM = {(u, v): fd._edge_geom(u, v) for (u, v) in spec.EDGES}


def path_polyline(nodes):
    pts = []
    for u, v in zip(nodes, nodes[1:]):
        pts += GEOM[(u, v)][0]
    return pts


def point_along(pts, f):
    seg = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    target = sum(seg) * max(0.0, min(1.0, f))
    for (a, b), L in zip(zip(pts, pts[1:]), seg):
        if target <= L:
            r = target / L if L else 0
            return (a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r)
        target -= L
    return pts[-1]


def draw_graph(c, rings=None, edge_hl=None, label_hl=None, spokes=None, dots=None):
    """Same look as fd.draw_graph when called without highlights.
    edge_hl: list of (u, v, color, alpha, dashed); label_hl: {(u, v): alpha} ACCENT label pulse;
    spokes: list of (src, dst, alpha) dashed ACCENT straight arrows; dots: list of (xy, color)."""
    rings, edge_hl, label_hl = rings or {}, edge_hl or [], label_hl or {}
    spokes, dots = spokes or [], dots or []
    for (u, v) in spec.EDGES:
        body = fd._arrow(c, GEOM[(u, v)][0], spec.MUTED, 3)
        c.line(body, spec.MUTED, 3)
    for src, dst, a in spokes:
        if a <= 0.01:
            continue
        (x0, y0), (x1, y1) = spec.NODE_POS[src], spec.NODE_POS[dst]
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        r = spec.NODE_R + 8
        pts = [(x0 + ux * (r + s * (L - 2 * r) / 30), y0 + uy * (r + s * (L - 2 * r) / 30))
               for s in range(31)]
        if a < 0.12:
            continue
        col = mix(spec.MUTED, spec.ACCENT, a)
        body = fd._arrow(c, pts, col, 3)
        c.dashed(body, col, 3, dash=12, gap=9)
    for u, v, col, a, dashed in edge_hl:
        if a <= 0.01:
            continue
        cc = mix(spec.MUTED, col, a)
        width = 3 + 4 * a
        body = fd._arrow(c, GEOM[(u, v)][0], cc, width)
        (c.dashed if dashed else c.line)(body, cc, width)
    for (u, v), w in spec.EDGES.items():
        lab = GEOM[(u, v)][1]
        a = label_hl.get((u, v), 0.0)
        c.circle(lab, 19, fill=spec.BG)
        if a > 0.01:
            c.circle(lab, 23, outline=mix(spec.BG, spec.ACCENT, a), width=3)
        c.text(lab, str(w), mix(spec.FG, spec.ACCENT, a), spec.FONT_SANS_BOLD, 30)
    for xy, col in dots:
        c.circle(xy, 8, fill=col, outline=spec.BG, width=2)
    for n, (x, y) in spec.NODE_POS.items():
        c.circle((x, y), spec.NODE_R, fill=spec.BG, outline=spec.FG, width=3)
        r = spec.NODE_R
        for col, a in rings.get(n, []):
            if a <= 0.06:
                continue
            r += 7
            c.circle((x, y), r, outline=mix(spec.BG, col, a), width=5)
        c.text((x, y + 1), n, spec.FG, spec.FONT_SANS_BOLD, 36)


# ---- Matrix -----------------------------------------------------------------------------
def draw_grid(c, sweep, head_a, header_hl):
    if sweep <= 0.001:
        return
    span = 4 * spec.MATRIX_CELL
    xe = X0 + span * sweep
    for t in range(5):
        y = Y0 + t * spec.MATRIX_CELL
        c.line([(X0, y), (xe, y)], spec.GRID, 2)
        x = X0 + t * spec.MATRIX_CELL
        va = ease((xe - x) / 40 + 1) if t else ease(sweep * 8)
        if va > 0.01:
            c.line([(x, Y0), (x, Y0 + span * va)], spec.GRID, 2)
    if head_a > 0.01:
        for t, n in enumerate(NODES):
            for kind in ("r", "c"):
                col = spec.FG
                if (kind, t) in header_hl:
                    hc, ha = header_hl[(kind, t)]
                    col = mix(col, hc, ha)
                col = mix(spec.BG, col, head_a)
                if kind == "c":
                    pos = (X0 + t * spec.MATRIX_CELL + spec.MATRIX_CELL / 2,
                           spec.MATRIX_Y0 + spec.MATRIX_HEAD / 2 + 4)
                else:
                    pos = (spec.MATRIX_X0 + spec.MATRIX_HEAD / 2,
                           Y0 + t * spec.MATRIX_CELL + spec.MATRIX_CELL / 2)
                c.text(pos, n, col, spec.FONT_SANS_BOLD, 36)


CORNER_XY = (spec.MATRIX_X0 + spec.MATRIX_HEAD / 2 - 2, spec.MATRIX_Y0 + spec.MATRIX_HEAD / 2 + 4)


def draw_corner(c, kind, a):
    if a <= 0.01:
        return
    col = mix(spec.BG, spec.MUTED, a)
    if kind == "ij":   # classic "row i / column j" corner: diagonal with i bottom-left, j top-right
        x0, y0 = spec.MATRIX_X0, spec.MATRIX_Y0
        c.line([(x0 + 10, y0 + 10), (x0 + spec.MATRIX_HEAD - 6, y0 + spec.MATRIX_HEAD - 6)],
               mix(spec.BG, spec.GRID, a), 2)
        c.text((x0 + 14, y0 + 45), "i", col, LABEL_FONT, LABEL_PX)
        c.text((x0 + 47, y0 + 16), "j", col, LABEL_FONT, LABEL_PX)
    elif kind == "L1":
        runs_line(c, CORNER_XY, L1_RUNS, a, anchor="m", base=spec.MUTED)
    else:
        c.text(CORNER_XY, kind, col, LABEL_FONT, LABEL_PX)


def draw_cell_value(c, i, j, txt, col, a, dy=0.0):
    if a > 0.01:
        fd._value(c, fd.cell_box(i, j), txt, mix(spec.BG, col, a), dy)


def draw_outline(c, i, j, col, a, width):
    if a <= 0.1:
        return
    b = fd.cell_box(i, j)
    ins = width / 2 + 1
    c.rect((b[0] + ins, b[1] + ins, b[2] - ins, b[3] - ins), outline=mix(spec.BG, col, a),
           width=width, radius=6)


# ---- Text helpers -----------------------------------------------------------------------
def runs_line(c, xy, runs, a, anchor="l", base=None):
    """runs: (text, color, font, px[, run_alpha])."""
    if a <= 0.01:
        return
    out = []
    for r in runs:
        ra = r[4] if len(r) > 4 else 1.0
        out.append((r[0], mix(spec.BG, base or r[1], a * ra), r[2], r[3]))
    return c.runs(xy, out, anchor="m" if anchor == "m" else "l")


def runs_width(c, runs):
    return sum(c.text_w(r[0], r[2], r[3]) for r in runs)


S, SB, M, MB = spec.FONT_SANS, spec.FONT_SANS_BOLD, spec.FONT_MONO, spec.FONT_MONO_BOLD
LINE_PX = 30
TAG_PX = 28
INPUT_LINES = [
    [("•  directed graph", spec.FG, S, LINE_PX)],
    [("•  ", spec.FG, S, LINE_PX), ("n = 4", spec.ACCENT, MB, LINE_PX), (" vertices", spec.FG, S, LINE_PX)],
    [("•  a weight on every edge", spec.FG, S, LINE_PX)],
]
LEN_TAG = [("PATH LENGTH", spec.MUTED, SB, TAG_PX), ("  = sum of its weights", spec.FG, S, LINE_PX)]
LEN_BAD = [("B→A→D", spec.BAD, MB, 32), ("   8 + 7 = 15", spec.FG, M, 32)]
LEN_GOOD = [("B→C→D", spec.GOOD, MB, 32), ("   2 + 1 = 3  ", spec.FG, M, 32),
            ("✓", spec.GOOD, SB, 34)]
OUT_LINE = [("OUTPUT", spec.MUTED, SB, TAG_PX), ("   shortest distance  i → j", spec.FG, S, LINE_PX)]
CARD_ICON = (700, 120)
CARD_TX = 748
CARD_L1 = [("negative weights: ", spec.FG, S, TAG_PX), ("allowed ", spec.GOOD, SB, TAG_PX),
           ("✓", spec.GOOD, SB, TAG_PX)]
CARD_L2 = [("negative cycles: ", spec.FG, S, TAG_PX), ("forbidden ", spec.BAD, SB, TAG_PX),
           ("✗", spec.BAD, SB, TAG_PX)]
CARD_FACT = [("no repeats  ⇒  ≤ ", spec.FG, S, TAG_PX), ("n − 1", spec.ACCENT, SB, TAG_PX),
             (" = 3 edges", spec.FG, S, TAG_PX)]
PILL_TEXT = [("≤ ", spec.FG, S, TAG_PX), ("n − 1", spec.ACCENT, SB, TAG_PX),
             (" = 3 edges", spec.FG, S, TAG_PX)]
BASE_RUNS = [("n × Bellman–Ford  ≈  ", spec.FG, M, LINE_PX), ("Θ(n⁴)", spec.BAD, MB, LINE_PX)]
L1_RUNS = [("L", spec.MUTED, S, 32), ("⁽¹⁾", spec.MUTED, S, 40)]   # superscript glyphs of a 40 px font
CAPTION = [("at most 1 edge", spec.FG, CAP_FONT, CAP_PX)]


def check_layout():
    c = fd.Canvas()
    assert RX + max(runs_width(c, r) for r in INPUT_LINES + [LEN_TAG, LEN_BAD, LEN_GOOD]) < 1230
    assert runs_width(c, OUT_LINE) < CARD_BOX[2] - CARD_BOX[0] - 20
    for r in (CARD_L1, CARD_L2):
        assert CARD_TX + runs_width(c, r) < CARD_BOX[2] - 14, runs_width(c, r)
    assert runs_width(c, CARD_FACT) < CARD_BOX[2] - CARD_BOX[0] - 28, runs_width(c, CARD_FACT)
    pw = runs_width(c, PILL_TEXT)
    assert pw < PILL_BOX[2] - PILL_BOX[0] - 24, pw
    assert c.text_w(TITLE, SB, spec.TITLE_FONT_PX) + 40 < PILL_BOX[0] - 30
    assert PILL_BOX[2] < spec.ROUND_BOX[0] - 10
    assert runs_width(c, L1_RUNS) < spec.MATRIX_HEAD + 10, runs_width(c, L1_RUNS)


check_layout()


# ---- Plan: every event time derived from the narration ----------------------------------
def plan():
    P = {}
    b1, b2, b3, b4, b5, b6, b7, b8 = BEATS
    P["input_in"] = [b1["t0"], b1["cues"][0], b1["cues"][2]]
    P["input_out"] = b3["t0"]
    P["nodes_pulse"] = b1["cues"][1]
    P["labels_pulse"] = b1["cues"][2]
    P["len_tag"] = b2["t0"]
    P["bad_path"] = b2["cues"][0]
    P["good_path"] = b2["cues"][1]
    P["right_clear"] = b3["t0"]                 # beats 1-2 content fades out here
    P["out_line"] = (b3["t0"] + FADE, b4["t0"])
    P["grid"] = b3["t0"] + FADE                 # grid strokes in after the old text left
    P["grid_dur"] = 0.5 * TS
    P["heads"] = P["grid"] + P["grid_dur"] * 0.6
    P["qmarks"] = max(b3["cues"][0], P["heads"])
    P["row_hl"] = b3["cues"][1]
    P["col_hl"] = b3["cues"][2]
    P["cell_hl"] = b3["cues"][3]
    P["hl_out"] = b3["t1"] - FADE
    P["corner_ij"] = (P["qmarks"] + FADE, b7["cues"][2])
    P["card_in"] = b4["t0"] + FADE * 0.5
    P["card_l1"] = b4["cues"][0]
    P["card_l2"] = b4["cues"][1]
    P["card_icon"] = b4["cues"][2]
    P["loop_dur"] = b4["t1"] - b4["cues"][2]
    P["base"] = (b5["t0"], b5["t1"] - FADE)
    P["base_theta"] = b5["cues"][1]
    sp = b5["cues"][0]
    P["spokes"] = [(n, sp + k * 0.3 * TS * 1.6, sp + k * 0.3 * TS * 1.6 + 0.55 * TS)
                   for k, n in enumerate(NODES)]
    P["fact"] = b6["cues"][0]
    P["fact_path"] = (b6["cues"][0], b6["t1"] - FADE)
    P["shrink"] = b6["t1"] - FADE
    # beat 7: diagonal, weight flights, infinities
    P["diag"] = b7["cues"][0]
    w0, winf = b7["cues"][1], b7["cues"][2]
    stagger = max(0.12, min(0.3 * TS, (winf - w0 - FLY) / (len(EDGE_ORDER) - 1)))
    P["fly_stagger"] = stagger
    P["max_concurrent_flights"] = math.ceil(FLY / stagger)
    P["flights"] = [(u, v, w0 + k * stagger) for k, (u, v) in enumerate(EDGE_ORDER)]
    last_land = P["flights"][-1][2] + FLY
    P["inf"] = max(winf, last_land - FADE)
    P["inf_late"] = P["inf"] - winf
    P["w_label"] = b8["cues"][0]
    P["l1_label"] = b8["cues"][1]
    P["caption"] = b8["cues"][1]
    # cell replacement times
    rep = {}
    for i in range(N):
        rep[(i, i)] = ("pop", P["diag"])
    for u, v, ts in P["flights"]:
        rep[(IDX[u], IDX[v])] = ("fly", ts + FLY)
    for i in range(N):
        for j in range(N):
            rep.setdefault((i, j), ("pop", P["inf"]))
    P["rep"] = rep
    return P


# ---- Frame ------------------------------------------------------------------------------
def draw_frame(P, t):
    c = fd.Canvas()
    fd.draw_title(c, title=TITLE)
    b1, b2, b3, b4, b5, b6, b7, b8 = BEATS
    clear = 1 - ease((t - P["right_clear"]) / FADE)

    rings = {n: [] for n in NODES}
    edge_hl, label_hl, spokes, dots = [], {}, [], []

    # beat 1: nodes / weights pulse
    na = pulse(t, P["nodes_pulse"])
    for n in NODES:
        rings[n].append((spec.ACCENT, na))
    la = pulse(t, P["labels_pulse"])
    for e in spec.EDGES:
        label_hl[e] = la

    # beat 2: two paths with travelling dots
    for nodes, col, t_in, dashed in ((["B", "A", "D"], spec.BAD, P["bad_path"], True),
                                     (["B", "C", "D"], spec.GOOD, P["good_path"], False)):
        a = env(t, t_in) * clear
        if col == spec.BAD:   # dim the rejected path once the good one arrives
            a *= 1 - 0.55 * ease((t - P["good_path"]) / FADE)
        for u, v in zip(nodes, nodes[1:]):
            edge_hl.append((u, v, col, a, dashed))
        if a > 0.01 and t - t_in < MOVE * 2 + 0.1:
            f = (t - t_in) / (MOVE * 2)
            if f <= 1.0:
                dots.append((point_along(path_polyline(nodes), ease(f)), col))

    # beat 3: example cell B->D
    hl_a = env(t, P["cell_hl"], P["hl_out"])
    rows_a = env(t, P["row_hl"], P["hl_out"])
    cols_a = env(t, P["col_hl"], P["hl_out"])
    rings["B"].insert(0, (spec.INFO, hl_a))
    rings["D"].insert(0, (spec.INFO, hl_a))
    header_hl = {("r", IDX["B"]): (spec.INFO, rows_a), ("c", IDX["D"]): (spec.INFO, cols_a)}

    # beat 5: Bellman-Ford from every vertex (spokes)
    for n, s0, s1 in P["spokes"]:
        a = env(t, s0, s1)
        rings[n].append((spec.ACCENT, a))
        for m in NODES:
            if m != n:
                spokes.append((n, m, a))

    # beat 6: a shortest path, 3 edges, no repeated vertex
    fa = env(t, P["fact_path"][0], P["fact_path"][1])
    fp = ["A", "B", "C", "D"]
    for u, v in zip(fp, fp[1:]):
        edge_hl.append((u, v, spec.GOOD, fa, False))
    if fa > 0.01 and t - P["fact_path"][0] <= MOVE * 3:
        dots.append((point_along(path_polyline(fp), ease((t - P["fact_path"][0]) / (MOVE * 3))),
                     spec.GOOD))

    # beat 7: edge flashes during each weight flight
    for u, v, ts in P["flights"]:
        a = env(t, ts - 0.06, ts + FLY - 0.1, fade=0.08)
        if a > 0.01:
            edge_hl.append((u, v, spec.ACCENT, a, False))
            label_hl[(u, v)] = max(label_hl.get((u, v), 0), a)

    draw_graph(c, rings, edge_hl, label_hl, spokes, dots)

    # ---- right half, beats 1-2 ----
    if clear > 0.01:
        tag_a = env(t, P["input_in"][0]) * clear
        runs_line(c, (RX, TOP_Y), [("INPUT", spec.MUTED, SB, TAG_PX)], tag_a)
        for k, (ln, ti) in enumerate(zip(INPUT_LINES, P["input_in"])):
            runs_line(c, (RX, 178 + 50 * k), ln, env(t, ti) * clear)
        runs_line(c, (RX, 360), LEN_TAG, env(t, P["len_tag"]) * clear)
        ba = env(t, P["bad_path"]) * clear
        runs_line(c, (RX, 425), LEN_BAD, ba)
        runs_line(c, (RX, 485), LEN_GOOD, env(t, P["good_path"]) * clear)

    # ---- top band: OUTPUT line, then assumption card -> key fact -> pill ----
    runs_line(c, (MCX, TOP_Y), OUT_LINE, env(t, *P["out_line"]), anchor="m")
    draw_card(c, P, t)

    # ---- matrix ----
    sweep = prog(t, P["grid"], P["grid_dur"])
    head_a = ease((t - P["heads"]) / FADE)
    draw_grid(c, sweep, head_a, header_hl)
    draw_corner(c, "ij", env(t, *P["corner_ij"]))
    draw_corner(c, "W", env(t, P["w_label"], P["l1_label"]))
    draw_corner(c, "L1", ease((t - P["l1_label"] - FADE) / FADE))
    qa = ease((t - P["qmarks"]) / FADE)
    flying = []
    for i in range(N):
        for j in range(N):
            kind, tr = P["rep"][(i, j)]
            val = fd.fmt(W_TABLE[i][j])
            if kind == "pop":
                r = (t - tr) / (0.4 * TS)
                draw_cell_value(c, i, j, "?", spec.MUTED, qa * (1 - ease(r * 2)))
                draw_cell_value(c, i, j, val, spec.FG, ease(r * 2 - 1), dy=8 * (1 - ease(r * 2 - 1)))
            else:
                ts = tr - FLY
                draw_cell_value(c, i, j, "?", spec.MUTED, qa * (1 - ease((t - (tr - FADE)) / FADE)))
                if t >= tr:
                    k = ease((t - tr) / (0.6 * TS))
                    draw_cell_value(c, i, j, val, mix(spec.ACCENT, spec.FG, k), 1.0)
                    draw_outline(c, i, j, spec.ACCENT, 1 - k, 3)
                elif t >= ts:
                    flying.append((i, j, val, (t - ts) / FLY))
    draw_outline(c, IDX["B"], IDX["D"], spec.INFO, hl_a, 5)

    # flying weights (on top of everything in the matrix)
    for i, j, val, f in flying:
        u, v = NODES[i], NODES[j]
        sx, sy = GEOM[(u, v)][1]
        b = fd.cell_box(i, j)
        ex, ey = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        p = ease(f)
        cx, cy = (sx + ex) / 2, min(sy, ey) - 90
        x = (1 - p) ** 2 * sx + 2 * (1 - p) * p * cx + p * p * ex
        y = (1 - p) ** 2 * sy + 2 * (1 - p) * p * cy + p * p * ey
        px = int(round(lerp(30, 42, p)))
        c.circle((x, y), lerp(19, 26, p), fill=spec.BG, outline=spec.ACCENT, width=2)
        c.text((x, y), val, spec.ACCENT, SB, px)

    # ---- bottom: baseline pill, then caption ----
    draw_baseline(c, P, t)
    ca = ease((t - P["caption"]) / FADE)
    runs_line(c, (MCX, spec.CAPTION_Y), CAPTION, ca, anchor="m")
    return c.finish()


def draw_baseline(c, P, t):
    a = env(t, *P["base"])
    if a <= 0.01:
        return
    w = runs_width(c, BASE_RUNS)
    box = (MCX - w / 2 - 22, BASE_Y - 27, MCX + w / 2 + 22, BASE_Y + 27)
    c.rect(box, outline=mix(spec.BG, spec.GRID, a), width=2, radius=27)
    th = ease((t - P["base_theta"]) / FADE)
    runs_line(c, (MCX, BASE_Y), [BASE_RUNS[0], BASE_RUNS[1] + (th,)], a, anchor="m")


def draw_card(c, P, t):
    a_in = ease((t - P["card_in"]) / FADE)
    if a_in <= 0.01:
        return
    sp = ease((t - P["shrink"]) / MOVE)
    box = tuple(lerp(x, y, sp) for x, y in zip(CARD_BOX, PILL_BOX))
    radius = lerp(12, 23, sp)
    frame = mix(spec.GRID, spec.MUTED, sp)
    c.rect(box, outline=mix(spec.BG, frame, a_in), width=2, radius=radius)
    cy = (box[1] + box[3]) / 2
    # stage 1: assumption lines + icon; stage 2: key fact; stage 3: pill text
    fact = ease((t - P["fact"]) / FADE)
    s1 = a_in * (1 - fact)
    if s1 > 0.01:
        runs_line(c, (CARD_TX, 102), CARD_L1, s1 * ease((t - P["card_l1"]) / FADE))
        runs_line(c, (CARD_TX, 140), CARD_L2, s1 * ease((t - P["card_l2"]) / FADE))
        ia = s1 * ease((t - P["card_l2"]) / FADE)
        if ia > 0.01:
            draw_cycle_icon(c, t, P, ia)
    long_a = fact * (1 - ease(sp * 2.5))
    runs_line(c, ((box[0] + box[2]) / 2, cy), CARD_FACT, long_a, anchor="m")
    runs_line(c, ((box[0] + box[2]) / 2, cy), PILL_TEXT, ease(sp * 2.2 - 0.9), anchor="m")


def draw_cycle_icon(c, t, P, a):
    """Small 3-vertex cycle with total -1; at 'loop forever' a dot circles it and it is struck out."""
    cx, cy = CARD_ICON
    R = 26
    col = mix(spec.BG, spec.BAD, a)
    pts = [(cx + R * math.cos(math.radians(-90 + 120 * k)), cy + R * math.sin(math.radians(-90 + 120 * k)))
           for k in range(3)]
    for k in range(3):
        p0, p1 = pts[k], pts[(k + 1) % 3]
        c.line([p0, p1], col, 3)
    for p in pts:
        c.circle(p, 6, fill=spec.BG, outline=col, width=2)
    loop_t = t - P["card_icon"]
    if 0 <= loop_t:
        f = (loop_t / (0.8 * TS)) % 1.0
        seg = int(f * 3)
        r = f * 3 - seg
        p0, p1 = pts[seg], pts[(seg + 1) % 3]
        da = a * (1 - ease((loop_t - P["loop_dur"] + FADE) / FADE))
        c.circle((lerp(p0[0], p1[0], r), lerp(p0[1], p1[1], r)), 6,
                 fill=mix(spec.BG, spec.ACCENT, da))


# ---- Render -----------------------------------------------------------------------------
def loudnorm(src, dst):
    af = f"loudnorm=I={spec.LUFS}:TP=-1.5:LRA=11"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(src), "-af",
                        af + ":print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, check=True)
    m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr).group(0))
    af2 = (af + f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
           f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
           f":offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
                    "-af", af2, "-ar", str(spec.SR), "-ac", "1", str(dst)], check=True)


def main():
    dump = "--frames" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    (HERE / "script.txt").write_text("\n".join(b["text"].replace(CUE, "") for b in BEATS) + "\n")
    audio, n, total = build_timeline()
    sf.write(OUT / "narration_raw.wav", audio, spec.SR)
    loudnorm(OUT / "narration_raw.wav", OUT / "narration.wav")
    P = plan()
    print(f"total {total:.2f}s, {n} frames; speed {spec.SPEED}")
    for b in BEATS:
        print(f"  {b['t0']:6.2f}-{b['t1']:6.2f} ({b['dur']:5.2f}s) {b['name']:8s} cues "
              f"{[round(x, 2) for x in b['cues']]}")
    print(f"  fly stagger {P['fly_stagger']:.3f}s, infinities late by {P["inf_late"]:.3f}s, max concurrent flights {P["max_concurrent_flights"]}")
    (OUT / "timeline.json").write_text(json.dumps(
        [{k: b[k] for k in ("name", "t0", "t1", "dur", "cues", "text")} for b in BEATS], indent=1))

    checks = {}
    if dump:
        FRAMES.mkdir(exist_ok=True)
        for b in BEATS:
            for k, cu in enumerate(b["cues"]):
                checks[int(round((cu + 0.35) * spec.FPS))] = f"{b['name']}_c{k}"
            checks[int(round((b["t1"] - 0.05) * spec.FPS))] = f"{b['name']}_end"
        for u, v, ts in P["flights"][2:4]:
            checks[int(round((ts + FLY * 0.6) * spec.FPS))] = f"fly_{u}{v}"
        checks[int(round((P["shrink"] + MOVE * 0.5) * spec.FPS))] = "shrink_mid"

    cmd = (["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{spec.W}x{spec.H}",
            "-r", str(spec.FPS), "-i", "-", "-i", str(OUT / "narration.wav")]
           + spec.VCODEC_ARGS + spec.ACODEC_ARGS
           + ["-t", f"{total:.3f}", "-movflags", "+faststart", str(OUT / "segment.mp4")])
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        t = f / spec.FPS
        img = draw_frame(P, t)
        if f == 0:
            img.save(HERE / "first_frame.png")
        if f == n - 1:
            img.save(HERE / "last_frame.png")
        if f in checks:
            img.save(FRAMES / f"t{t:06.2f}_{checks[f]}.png")
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    assert proc.wait() == 0
    print("wrote", OUT / "segment.mp4")


if __name__ == "__main__":
    main()
