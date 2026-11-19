"""SHORT 02_problem (static, 3 keyframes + handoff): graph left, one text card per line."""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import shortlib as sl  # noqa: E402
from shortlib import spec, fd  # noqa: E402

LINES = [
    ("io", "We get a directed graph with n vertices and a weight on every edge, "
           "and we want the shortest distance from every i to every j."),
    ("neg", "Weights may be negative, but no cycle may have a negative total. "
            "Then shortest paths never repeat a vertex, so they use at most n minus one edges."),
    ("bf", "Running Bellman-Ford from every vertex would cost up to n to the fourth."),
]
X = 690          # left edge of the card text (right half)
CARD = (660, 160, 1240, 640)
SANS, BOLD, MONO, MONOB = spec.FONT_SANS, spec.FONT_SANS_BOLD, spec.FONT_MONO, spec.FONT_MONO_BOLD


def card(rows):
    """rows = [(y, parts[, (boxed part index, colour)])]; the box is the shape cue."""
    c = sl.base_canvas("aps")
    c.rect(CARD, outline=spec.GRID, width=2, radius=16)
    for row in rows:
        y, parts = row[:2]
        if len(row) > 2:
            sl.spans_box(c, (X, y), parts, row[2][0], row[2][1], anchor="l")
        else:
            sl.spans(c, (X, y), parts, anchor="l")
    return c.finish()


def main():
    t0 = time.time()
    sl.write_script(HERE, LINES)
    audio, tl, total, n = sl.layout(LINES)
    k1 = card([
        (210, [("INPUT", spec.MUTED, BOLD, 28)]),
        (260, [("directed graph,  n = 4", spec.FG, SANS, 32)]),
        (305, [("a weight on every edge", spec.FG, SANS, 32)]),
        (400, [("OUTPUT", spec.MUTED, BOLD, 28)]),
        (452, [("dist(i → j)", spec.INFO, MONOB, 34)]),
        (500, [("for every pair i, j", spec.FG, SANS, 32)]),
    ])
    k2 = card([
        (215, [("✓ ", spec.GOOD, BOLD, 32), ("negative weights allowed", spec.FG, SANS, 30)]),
        (275, [("✗ ", spec.BAD, BOLD, 32), ("no negative cycles", spec.FG, SANS, 30)]),
        (360, [("⇒  shortest paths never", spec.FG, SANS, 30)]),
        (405, [("     repeat a vertex", spec.FG, SANS, 30)]),
        (500, [("⇒  ", spec.FG, SANS, 32), ("≤ n − 1", spec.ACCENT, BOLD, 36),
               ("  edges", spec.FG, SANS, 32)], (1, spec.ACCENT)),
    ])
    k3 = card([
        (240, [("n × Bellman–Ford", spec.FG, BOLD, 36)]),
        (295, [("one run per start vertex", spec.MUTED, SANS, 30)]),
        (420, [("≈  ", spec.FG, SANS, 44), ("Θ(n^4)", spec.BAD, BOLD, 48)], (1, spec.BAD)),
    ])
    prev = sl.prev_last("01_hook") or sl.base_canvas("aps").finish()
    kf = [(prev, 0.0), (k1, sl.LEAD), (k2, tl["neg"]["start"]), (k3, tl["bf"]["start"])]
    sl.render_static(HERE, kf, audio, total)
    print(f"render time {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
