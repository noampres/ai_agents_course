"""Segment 03_extend_idea: grow paths one edge at a time; the min-plus recurrence.

Run from this folder: ../../../kokoro-video/.venv/bin/python render.py [--frames]
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from common import spec  # noqa: E402
from common import fwlib as L  # noqa: E402
from common.fwlib import S, env, ease, fd, mix, NODES  # noqa: E402

W = L.w_matrix()

BEATS = [
    dict(id="idea", text="The most natural idea: allow one more edge at a time. "
                         "^A path with at most two edges is a path with at most one edge, "
                         "^plus one final edge from some vertex k to j."),
    dict(id="try", text="So try every possible last stop k, and keep the cheapest. "
                        "^Picking k equals j costs nothing extra, "
                        "so paths that are already good enough survive."),
    dict(id="formula", text="In symbols: ^L m of i j is the minimum over k, "
                            "of L m minus one of i k, plus W of k j."),
    dict(id="mult", text="That's matrix multiplication, ^with plus instead of times, "
                         "^and min instead of sum."),
]
seg = L.Segment(HERE, BEATS)
B = seg.B
T_OLD, T_NEW = spec.CHAPTER_TITLES["intro"], spec.CHAPTER_TITLES["edge"]
GX = 320                                  # centre of the graph half for captions
CARD = (674, 236, 1206, 520)


def static_right(f, alpha=1.0):
    f.layer(L.matrix_fn(W), alpha, key="W")
    f.layer(L.corner_label("L^{(1)}"), alpha, key="cL1")
    f.layer(L.caption([("L^{(1)}", spec.FG, spec.FONT_MONO_BOLD, 30),
                       (" · at most 1 edge", spec.MUTED, spec.FONT_SANS, 28)]), alpha, key="cap1")


def card_fn(row2, row3):
    def fn(c):
        c.rect(CARD, outline=spec.GRID, width=2, radius=14, fill=spec.BG)
        cx = (CARD[0] + CARD[2]) / 2
        L.rich(c, (cx, 290), [("matrix product, two ways", spec.MUTED, spec.FONT_SANS_BOLD, 28)])
        L.rich(c, (CARD[0] + 40, 370), [("ordinary:  ", spec.MUTED, spec.FONT_SANS, 30),
                                        ("Σ", spec.FG, spec.FONT_MONO_BOLD, 34),
                                        ("ₖ", spec.FG, spec.FONT_MONO, 30),
                                        (" a·b", spec.FG, spec.FONT_MONO, 34)], "l")
        if row2 > 0:
            plus = mix(spec.BG, spec.ACCENT, row2)
            mn = mix(spec.BG, spec.ACCENT, row3) if row3 > 0 else mix(spec.BG, spec.FG, row2)
            mn_txt = "min" if row3 > 0.5 else "Σ"
            L.rich(c, (CARD[0] + 40, 450), [("min-plus:  ", mix(spec.BG, spec.MUTED, row2),
                                             spec.FONT_SANS, 30),
                                            (mn_txt, mn, spec.FONT_MONO_BOLD, 34),
                                            ("ₖ", mix(spec.BG, spec.FG, row2), spec.FONT_MONO, 30),
                                            (" a", mix(spec.BG, spec.FG, row2), spec.FONT_MONO, 34),
                                            ("+", plus, spec.FONT_MONO_BOLD, 34),
                                            ("b", mix(spec.BG, spec.FG, row2), spec.FONT_MONO, 34)],
                   "l")
    return fn


def draw(t):
    f = L.Frame()
    L.title_bar(f, T_NEW, prev=T_OLD, mix_a=ease((t - 0.1) / (0.3 * S)))
    f.layer(L.edge_pill_fn, key="edgepill")

    # ---- graph -------------------------------------------------------------------------
    rings = {n: [] for n in NODES}
    paths = []
    bi, bt = B["idea"], B["try"]
    paths.append((["B", "C"], spec.INFO, env(t, bi["cues"][0], bt["t0"]), False))
    grow = ease((t - bi["cues"][1]) / (0.6 * S))
    paths.append((["C", "D"], spec.ACCENT, env(t, bi["cues"][1], bt["t0"]) * grow, False))
    mid = (bt["t0"] + bt["cues"][0]) / 2
    for k, (a0, a1) in (("A", (bt["t0"], mid)), ("C", (mid, bt["cues"][0]))):
        a = env(t, a0, a1)
        paths.append((["B", k], spec.INFO, a, True))
        paths.append(([k, "D"], spec.ACCENT, a, True))
    ka = env(t, bt["cues"][0], B["formula"]["t0"])
    if ka > 0.01:
        rings["D"].append((spec.ACCENT, ka))
    L.graph(f, rings=rings, paths=[p for p in paths if p[2] > 0.01])
    if 0 < grow < 1:
        L.dot_on_path(f, ["C", "D"], grow, spec.ACCENT)
    # caption under the graph
    f.layer(L.caption([("≤ m−1 edges", spec.INFO, spec.FONT_SANS_BOLD, 28),
                       ("  +  one last edge k→j", spec.ACCENT, spec.FONT_SANS_BOLD, 28)],
                      y=spec.GRAPH_CAPTION_Y, cx=GX),
            env(t, bi["cues"][1], bt["t0"]), key="gcap")
    f.layer(L.caption([("k = j:  + 0  (stay put)", spec.ACCENT, spec.FONT_SANS_BOLD, 28)],
                      y=spec.GRAPH_CAPTION_Y, cx=GX),
            ka, key="kj")

    # ---- formula strip -----------------------------------------------------------------
    fa = ease((t - B["formula"]["cues"][0]) / spec.FADE)
    f.layer(L.formula_frame, fa, key="fframe")
    f.layer(L.formula_runs(L.EXT_FORMULA), fa, key="fext")

    # ---- matrix + min-plus card ---------------------------------------------------------
    bm = B["mult"]
    t_out = max(bm["cues"][1] + 0.6 * S, bm["t1"] - 0.3)
    card = env(t, bm["t0"], t_out, fade=0.3 * S)
    static_right(f, 1 - 0.75 * card)
    if card > 0.01:
        r2 = ease((t - bm["cues"][0]) / spec.FADE)
        r3 = ease((t - bm["cues"][1]) / spec.FADE)
        f.layer(card_fn(r2, r3), card)
    return f.result()


if __name__ == "__main__":
    seg.render(draw)
