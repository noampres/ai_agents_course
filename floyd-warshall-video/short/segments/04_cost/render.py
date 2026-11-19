"""SHORT 04_cost (static, 2 keyframes + handoff): 03's last frame stays, the formula
strip text swaps to the cost of edge by edge, then to repeated squaring. No table."""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import shortlib as sl  # noqa: E402
from shortlib import spec, xd  # noqa: E402

LINES = [
    ("n4", "Each table costs n cubed, and we need about n of them: n to the fourth."),
    ("sq", "Squaring the tables instead gets n cubed log n. Can we reach n cubed?"),
]
SANS, BOLD, MONO = spec.FONT_SANS, spec.FONT_SANS_BOLD, spec.FONT_MONO


def frame(parts):
    Ls, _ = xd.extend_tables()
    c = xd.Canvas()
    xd.draw_title(c, m=3)
    xd.draw_m(c, 3)
    sl.strip(c, parts)
    xd.draw_graph(c)
    xd.draw_matrix(c, Ls[2], m=3)
    xd.draw_n1_pill(c)
    return c.finish()


def main():
    t0 = time.time()
    sl.write_script(HERE, LINES)
    audio, tl, total, n = sl.layout(LINES)
    k1 = frame([("n tables × n^3 each  =  ", spec.FG, SANS, 32),
                ("Θ(n^4)", spec.BAD, BOLD, 34)])
    k2 = frame([("squaring: log n tables  →  ", spec.FG, SANS, 32),
                ("Θ(n^3 log n)", spec.ACCENT, BOLD, 34)])
    prev = sl.prev_last("03_edge_by_edge") or xd.handoff_frame(3)
    kf = [(prev, 0.0), (k1, sl.LEAD), (k2, tl["sq"]["start"])]
    sl.render_static(HERE, kf, audio, total)
    print(f"render time {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
