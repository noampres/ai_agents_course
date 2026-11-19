"""SHORT 03_edge_by_edge: TABLE DEMO 1, a trim of segments/04_extend_demo plus its idea.

Kept from 04: the worked cell L(2)[B][D] in full (bands, work table, min, path, write).
Cut: individual flashes of the other L(2) cells (they all change at once with one line),
the A->D walk-through in L(3) (L(3) changes at once too).
Added (v4): W fades in already filled, the idea line (path grows by one edge) and the
formula-strip line. Drawing is imported read-only from 04's extend_draw.py.
"""
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import shortlib as sl  # noqa: E402
from shortlib import spec, xd  # noqa: E402
from extend_draw import INF, NODES, IDX, ease, env, mix  # noqa: E402

TS = spec.TIME_SCALE
STRIKE, SWAP, FLASH, PATH, LABEL = 0.3 * TS, 0.4 * TS, 0.9 * TS, 0.8 * TS, 0.4 * TS

# ---- algorithm (checked against SCRIPT_OUTLINE.md, as in 04) ---------------------------
Ls, ARGS = xd.extend_tables(3)
L1, L2, L3 = Ls
assert L2 == [[0, 3, 5, 7], [7, 0, 2, 3], [3, 8, 0, 1], [2, 5, INF, 0]]
assert L3 == [[0, 3, 5, 6], [5, 0, 2, 3], [3, 6, 0, 1], [2, 5, 7, 0]]
WI, WJ = IDX["B"], IDX["D"]
WORK = [(L1[WI][k], L1[k][WJ]) for k in range(4)]
assert [a + b for a, b in WORK] == [15, INF, 3, INF]
WMIN = min(range(4), key=lambda k: WORK[k][0] + WORK[k][1])
W_PATH = xd.path_of(Ls, ARGS, 2, WI, WJ)
assert W_PATH == ["B", "C", "D"]
CH2 = xd.changed_cells(L1, L2)
CH3 = xd.changed_cells(L2, L3)
CH2_REST = [c for c in CH2 if (c[0], c[1]) != (WI, WJ)]
WORDS = {0: "zero", 1: "one", 2: "two", 3: "three", 7: "seven", 8: "eight", 15: "fifteen",
         INF: "infinity"}
w = WORDS.__getitem__

LINES = [
    ("w", "Start with the direct roads: ^w this table W is the best using at most one edge."),
    ("idea", "Natural idea: allow one more edge at a time. ^p A path with at most m edges "
             "is a shorter one, ^e plus a last edge from k to j."),
    ("formula", "^f Try every last stop k, and keep the cheapest."),
    ("intro", "Let's build L two, ^target starting with one cell: from B to D."),
    ("bands", "Row B of L one gives the best path from B to each stop k. "
              "^col Column D of W adds the last edge, from k to D."),
    ("row0", f"^hdr Through A: ^r {w(WORK[0][0])} plus ^w {w(WORK[0][1])} is ^s {w(sum(WORK[0]))}."),
    ("row1", f"^r Through B: {w(WORK[1][0])} plus ^w {w(WORK[1][1])} ^s is still infinity."),
    ("row2", f"^r Through C: {w(WORK[2][0])} plus ^w {w(WORK[2][1])} is ^s {w(sum(WORK[2]))}."),
    ("row3", f"^r And k equals D ^old just keeps the old value: {w(WORK[3][0])} "
             f"^w plus {w(WORK[3][1])}, ^s still infinity."),
    ("min", f"The smallest is ^min {w(sum(WORK[WMIN]))}, through {NODES[WMIN]}."),
    ("write", "^path That's the route " + ", then ".join(W_PATH)
              + f". So ^write {w(L2[WI][WJ])} replaces infinity ^lab in L two."),
    ("all", "Doing that for every cell ^all gives the rest of L two, ^m3 and once more "
            "^l3 gives L three, ^pill the answer, since a shortest path needs at most "
            "n minus one edges."),
]


def transition(old, new, t0, t, good):
    return dict(old=old, new=new, strike=(t - t0) / STRIKE, swap=(t - t0 - STRIKE) / SWAP,
                color=mix(spec.FG, spec.GOOD, good), mark=min(ease((t - t0 - STRIKE) / SWAP), good))


def grow(nodes, col, t0, t, alpha):
    out = []
    segs = list(zip(nodes, nodes[1:]))
    for s, (u, v) in enumerate(segs):
        a = ease((t - t0) / PATH * len(segs) - s) * alpha
        if a > 0.01:
            out.append(([u, v], col, a, False))
    return out


def make_frame(B, prev):
    def S(n):
        return B[n]["start"]

    def C(n, c):
        return B[n]["cues"][c]

    t_w = C("w", "w")
    t_lab, t_m3, t_l3, t_pill = C("write", "lab"), C("all", "m3"), C("all", "l3"), C("all", "pill")
    t_all = C("all", "all")

    def draw(t, with_matrix=True):
        c = xd.Canvas()
        # title bar + label
        xd.draw_title(c)
        if t < t_lab:
            xd._title_label(c, 1, ease((t - t_w) / spec.FADE))
        elif t < t_m3:
            xd.draw_title(c, label_mix=(1, 2, (t - t_lab) / LABEL))
        else:
            xd.draw_title(c, label_mix=(2, 3, (t - t_m3) / LABEL))
        # m pill
        if t < t_m3:
            xd.draw_m(c, 2, env(t, S("intro")))
        else:
            a = ease((t - t_m3) / LABEL)
            xd.draw_m(c, 2, 1 - a, box_alpha=1.0)
            xd.draw_m(c, 3, a, box_alpha=0.0)
        xd.draw_formula_strip(c, env(t, C("formula", "f")))

        # graph
        paths, rings = [], {}
        a_idea = env(t, C("idea", "p"), S("formula"))
        paths += grow(["B", "C"], spec.INFO, C("idea", "p"), t, a_idea)
        paths += grow(["C", "D"], spec.ACCENT, C("idea", "e"), t, env(t, C("idea", "e"), S("formula")))
        t_tgt = C("intro", "target")
        a_tgt = env(t, t_tgt, t_all)
        t_p = C("write", "path")
        paths += grow(W_PATH, spec.GOOD, t_p, t, env(t, t_p, t_all))
        if a_tgt > 0.01:
            rings = {NODES[WI]: [(spec.INFO, a_tgt)], NODES[WJ]: [(spec.INFO, a_tgt)]}
        xd.draw_graph(c, rings=rings, paths=paths)

        if with_matrix:
            over, outlines, header_hl = {}, [], {}
            if t < t_l3:
                values = L1
                good = 1 - ease((t - t_m3) / LABEL)
                times = {(WI, WJ): C("write", "write")}
                times.update({(i, j): t_all for i, j, _, _ in CH2_REST})
                for (i, j), t0 in times.items():
                    if t >= t0:
                        over[(i, j)] = transition(L1[i][j], L2[i][j], t0, t, good)
                        if (i, j) != (WI, WJ):
                            outlines.append((i, j, spec.GOOD, env(t, t0, t0 + FLASH), 4))
            else:
                values = L2
                good3 = 1 - ease((t - t_pill) / LABEL)
                for i, j, _, _ in CH3:
                    over[(i, j)] = transition(L2[i][j], L3[i][j], t_l3, t, good3)
                    outlines.append((i, j, spec.GOOD, env(t, t_l3, t_l3 + FLASH), 4))
            bands = [("r", WI, spec.ACCENT, env(t, S("bands"), S("write"))),
                     ("c", WJ, spec.ACCENT, env(t, C("bands", "col"), S("write")))]
            outlines.append((WI, WJ, spec.INFO, a_tgt, 4))
            if a_tgt > 0.01:
                header_hl = {("r", WI): (spec.INFO, a_tgt), ("c", WJ): (spec.INFO, a_tgt)}
            rows_t = [C(f"row{k}", "r") for k in range(4)] + [C("min", "min")]
            for k in range(4):
                a = env(t, rows_t[k], rows_t[k + 1])
                outlines.append((WI, k, spec.ACCENT, a, 5, 5))
                outlines.append((k, WJ, spec.ACCENT, a, 5, 5))
            if t < t_lab:
                lab = dict(m=1)
            elif t < t_m3:
                lab = dict(label_mix=(1, 2, (t - t_lab) / LABEL))
            else:
                lab = dict(label_mix=(2, 3, (t - t_m3) / LABEL))
            xd.draw_matrix(c, values, overrides=over, bands=bands, outlines=outlines,
                           header_hl=header_hl, **lab)
        a_pill = env(t, t_pill)
        xd.draw_n1_pill(c, pulse=env(t, t_pill + spec.FADE, t_pill + 1.2 * TS, fade=LABEL),
                        alpha=a_pill)
        img = c.finish()

        # work table crossfaded with the graph (left half)
        a_wt = env(t, C("row0", "hdr"), t_p, fade=spec.MOVE)
        if a_wt > 0.001:
            tc = xd.Canvas()
            t_min = C("min", "min")
            rows = []
            for k in range(4):
                cu = B[f"row{k}"]["cues"]
                rows.append(dict(a=WORK[k][0], w=WORK[k][1], am=env(t, cu["r"]), aw=env(t, cu["w"]),
                                 dim=0.0 if k == WMIN else ease((t - t_min) / LABEL),
                                 **{"as": env(t, cu["s"])}))
            xd.draw_work_table(tc, WI, WJ, 1, rows, min_row=WMIN, min_alpha=env(t, t_min),
                               note=f"k = {NODES[WJ]}: + 0 keeps the old value",
                               note_alpha=env(t, C("row3", "old")))
            img = xd.swap_panel(img, tc.finish(), a_wt)
        return img

    def frame(t):
        a_m = ease((t - t_w) / spec.FADE)
        if a_m >= 0.999:
            img = draw(t, True)
        elif a_m <= 0.001:
            img = draw(t, False)
        else:
            img = Image.blend(draw(t, False), draw(t, True), a_m)
        return sl.blend_in(prev, img, t)

    return frame


def main():
    t0 = time.time()
    sl.write_script(HERE, LINES)
    audio, B, total, n = sl.layout(LINES)
    prev = sl.prev_last("02_problem")
    frame = make_frame(B, prev)
    last = frame((n - 1) / spec.FPS)
    same = np.array_equal(np.asarray(last), np.asarray(xd.handoff_frame(3)))
    print("last frame == extend_draw.handoff_frame(3):", same)
    if "--check" in sys.argv:
        out = HERE / "frames"
        out.mkdir(exist_ok=True)
        for name, b in B.items():
            for cn, ct in list(b["cues"].items()) + [("end", b["end"] - 0.05)]:
                tt = ct + 0.5 if cn != "end" else ct
                frame(tt).save(out / f"t{tt:06.2f}_{name}_{cn}.png")
        return
    sl.encode_frames(HERE, audio, n, frame)
    print(f"render time {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
