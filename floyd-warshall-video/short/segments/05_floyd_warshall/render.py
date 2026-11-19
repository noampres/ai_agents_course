"""SHORT 05_floyd_warshall: TABLE DEMO 2, a trim of segments/07_fw_demo plus its idea.

Kept from 07: round A's three improvements (B->D 15, C->B 8, D->B 5) with pivot cross,
operand outlines, detour path and caption. Cut: the 3 rejected checks of round A and
the narrated k = B detail. Rounds B, C, D: each one short line, its updates flash
together. Added (v4): the FW idea line and the formula-strip line.
Drawing is imported read-only from 07's fw_draw.py.
"""
import sys
import time
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import shortlib as sl  # noqa: E402
from shortlib import spec, fd  # noqa: E402
from fw_draw import INF, NODES, IDX, env, ease, mix  # noqa: E402

S = spec.TIME_SCALE
EXPECTED = {
    "A": {("B", "D"): 15, ("C", "B"): 8, ("D", "B"): 5},
    "B": {("A", "C"): 5, ("D", "C"): 7},
    "C": {("A", "D"): 6, ("B", "A"): 7, ("B", "D"): 3},
    "D": {("B", "A"): 5, ("C", "A"): 3, ("C", "B"): 6},
}
FINAL = [[0, 3, 5, 6], [5, 0, 2, 3], [3, 6, 0, 1], [2, 5, 7, 0]]
ROUNDS, final, _ = fd.floyd_warshall(fd.INITIAL)
for k, ups in enumerate(ROUNDS):
    assert {(NODES[i], NODES[j]): new for i, j, _, new, _, _ in ups} == EXPECTED[NODES[k]]
assert final == FINAL

# round-A updates with detour path (k = A, so the path is i -> A -> j)
A_UPS = {NODES[i] + NODES[j]: (i, j, old, new, a, b) for i, j, old, new, a, b in ROUNDS[0]}

LINES = [
    ("idea", "Floyd-Warshall asks a different question: not how many edges, "
             "but which vertices a path may pass through."),
    ("formula", "^f Round k: is going through k shorter? One comparison per cell."),
    ("rA", "Start with ^k k equals A."),
    ("BD", "B to D: ^a eight plus seven is fifteen, ^v better than infinity."),
    ("CB", "C to B: ^a five plus three is eight, ^v also better."),
    ("DB", "D to B: ^a two plus three is five, ^v better again."),
    ("rB", "^k Round B finds two more shortcuts at once."),
    ("rC", "^k Round C finds three more at once."),
    ("rD", "^k And round D fixes the last three."),
    ("final", "And we land on ^same exactly the same table, in n cubed time."),
]
FLASH_ROUNDS = {"rB": 1, "rC": 2, "rD": 3}


def plan(B):
    P = dict(pivots=[], focus=[], captions=[], paths=[], changes={})
    starts = {"rA": B["rA"]["cues"]["k"], "rB": B["rB"]["start"], "rC": B["rC"]["start"],
              "rD": B["rD"]["start"]}
    order = ["rA", "rB", "rC", "rD"]
    ends = {r: (starts[order[n + 1]] if n + 1 < 4 else B["final"]["start"])
            for n, r in enumerate(order)}
    for n, r in enumerate(order):
        P["pivots"].append(dict(k=n, t_in=starts[r], t_out=ends[r], pill_in=starts[r] - 0.25 * S))
    for name in ("BD", "CB", "DB"):
        b = B[name]
        i, j, old, new, a, bb = A_UPS[name]
        t_out = b["end"] - 0.05
        ca, cv = b["cues"]["a"], b["cues"]["v"]
        P["focus"].append(dict(i=i, j=j, k=0, t_in=b["start"] - 0.1 * S, t_out=t_out))
        P["captions"].append(dict(t_in=ca - 0.15 * S, t_out=t_out, runs=[
            (f"{name[0]}→{name[1]}", spec.INFO, spec.FONT_MONO_BOLD, 36, ca - 0.15 * S),
            ("  ", spec.FG, spec.FONT_MONO, 36, ca),
            (f"{fd.fmt(a)} + {fd.fmt(bb)} = {fd.fmt(new)}", spec.FG, spec.FONT_MONO, 36, ca),
            (f" < {fd.fmt(old)}  ", spec.GOOD, spec.FONT_MONO, 36, cv),
            ("✓", spec.GOOD, spec.FONT_SANS_BOLD, 40, cv)]))
        P["paths"].append(dict(nodes=[name[0], "A", name[1]], t_in=cv, t_out=t_out))
        P["changes"].setdefault((i, j), []).append(
            dict(t=cv + 0.3 * S, old=fd.fmt(old), new=fd.fmt(new), end=ends["rA"]))
    for r, k in FLASH_ROUNDS.items():
        b = B[r]
        tc = b["cues"]["k"] + 0.35 * S
        t_out = b["end"] - 0.05
        runs = []
        for n, (i, j, old, new, _, _) in enumerate(ROUNDS[k]):
            P["changes"].setdefault((i, j), []).append(
                dict(t=tc, old=fd.fmt(old), new=fd.fmt(new), end=ends[r]))
            P["focus"].append(dict(i=i, j=j, k=None, t_in=tc, t_out=t_out, good=True))
            if n:
                runs.append(("   •   ", spec.MUTED, spec.FONT_SANS_BOLD, 30, tc))
            runs.append((f"{NODES[i]}→{NODES[j]}", spec.INFO, spec.FONT_MONO_BOLD, 32, tc))
            runs.append((f" {fd.fmt(new)}", spec.GOOD, spec.FONT_MONO_BOLD, 32, tc))
        P["captions"].append(dict(runs=runs, t_in=tc, t_out=t_out))
    bf = B["final"]
    P["frame"] = dict(t_in=bf["cues"]["same"], t_out=bf["end"] - 0.3 * S)
    return P


def cell_state(P, i, j, t):
    base = fd.fmt(fd.INITIAL[i][j])
    ch = [c for c in P["changes"].get((i, j), []) if c["t"] <= t]
    if not ch:
        return {"text": base, "color": spec.FG}
    c = ch[-1]
    dt = t - c["t"]
    good = env(t, c["t"] + 0.6 * S, c["end"])
    st = {"text": c["new"], "color": mix(spec.FG, spec.GOOD, good), "mark": good}
    if dt < 0.8 * S:
        st["color"] = spec.GOOD
        st.update(old=c["old"], strike=dt / (0.25 * S), swap=(dt - 0.4 * S) / (0.4 * S))
    return st


def make_frame(B, prev):
    P = plan(B)
    t_f = B["formula"]["cues"]["f"]

    def frame(t):
        c = fd.Canvas()
        fd.draw_title(c)
        fd.draw_formula(c, env(t, t_f))
        pivot, rings = None, {n: [] for n in NODES}
        for pv in P["pivots"]:
            a = env(t, pv["t_in"], pv["t_out"])
            if a > 0.01:
                pivot = (pv["k"], a)
                rings[NODES[pv["k"]]].append((spec.ACCENT, a))
            pa = env(t, pv["t_in"], pv["t_out"])
            if pa > 0.01:
                fd.draw_k(c, NODES[pv["k"]], pa, box_alpha=0)
        box = env(t, P["pivots"][0]["t_in"], P["pivots"][-1]["t_out"])
        if box > 0.01:
            fd.draw_k(c, "", 0, box_alpha=box)
        outlines, header_hl = [], {}
        for f in P["focus"]:
            a = env(t, f["t_in"], f["t_out"])
            if a <= 0.01:
                continue
            i, j, k = f["i"], f["j"], f["k"]
            if f.get("good"):
                outlines.append((i, j, spec.GOOD, a, 4))
                continue
            outlines.append((i, k, spec.ACCENT, a, 5))
            outlines.append((k, j, spec.ACCENT, a, 5))
            outlines.append((i, j, spec.INFO, a, 6))
            header_hl[("r", i)] = (spec.INFO, a)
            header_hl[("c", j)] = (spec.INFO, a)
            rings[NODES[i]].insert(0, (spec.INFO, a))
            rings[NODES[j]].insert(0, (spec.INFO, a))
        paths = [(p["nodes"], spec.GOOD, env(t, p["t_in"], p["t_out"]), False) for p in P["paths"]]
        fd.draw_graph(c, rings=rings, paths=paths)
        cells = [[cell_state(P, i, j, t) for j in range(4)] for i in range(4)]
        fd.draw_matrix(c, cells, pivot=pivot, outlines=outlines, header_hl=header_hl)
        fa = env(t, P["frame"]["t_in"], P["frame"]["t_out"], fade=0.3 * S)
        if fa > 0.01:
            b0, b1 = fd.cell_box(0, 0), fd.cell_box(3, 3)
            c.rect((b0[0] - 8, b0[1] - 8, b1[2] + 8, b1[3] + 8),
                   outline=mix(spec.BG, spec.GOOD, fa), width=4, radius=8)
            cx = (spec.MATRIX_BOX[0] + spec.MATRIX_BOX[2]) / 2
            sl.spans(c, (cx, fd.CAPTION_Y), [
                ("same as L", mix(spec.BG, spec.FG, fa), spec.FONT_SANS, 30),
                ("^{(3)}", mix(spec.BG, spec.ACCENT, fa), spec.FONT_SANS_BOLD, 30),
                ("   ·   ", mix(spec.BG, spec.MUTED, fa), spec.FONT_SANS, 30),
                ("Θ(n^3)", mix(spec.BG, spec.GOOD, fa), spec.FONT_SANS_BOLD, 34)])
        for cap in P["captions"]:
            a = env(t, cap["t_in"], cap["t_out"])
            if a <= 0.01:
                continue
            fd.draw_caption(c, [(tx, col, f, px, env(t, t0)) for tx, col, f, px, t0 in cap["runs"]], a)
        return sl.blend_in(prev, c.finish(), t)

    return frame


def main():
    t0 = time.time()
    sl.write_script(HERE, LINES)
    audio, B, total, n = sl.layout(LINES)
    frame = make_frame(B, sl.prev_last("04_cost"))
    if "--check" in sys.argv:
        out = HERE / "frames"
        out.mkdir(exist_ok=True)
        for name, b in B.items():
            for cn, ct in list(b["cues"].items()) + [("end", b["end"] - 0.05)]:
                tt = ct + 0.5 if cn != "end" else ct
                frame(tt).save(out / f"t{tt:06.2f}_{name}_{cn}.png")
        frame(0.1).save(out / "t000.10.png")
        frame((n - 1) / spec.FPS).save(out / "last.png")
        return
    sl.encode_frames(HERE, audio, n, frame)
    print(f"render time {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
