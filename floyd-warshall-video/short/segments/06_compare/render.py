"""SHORT 06_compare: TABLE DEMO 3 (the last table), static: 2 keyframes + handoff.
Keyframe 1 = full comparison table, keyframe 2 = same table, Floyd–Warshall column outlined GOOD."""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import shortlib as sl  # noqa: E402
from shortlib import spec, fd  # noqa: E402

LINES = [
    ("diff", "The difference: one comparison per cell, instead of a min over every vertex."),
    ("factor", "That's a factor of n: a thousand times fewer steps when n is a thousand."),
]
SANS, BOLD = spec.FONT_SANS, spec.FONT_SANS_BOLD
X0, Y0 = 40, 130
COLS = [220] + [245] * 4          # = 1200 px = stage width
HEAD_H, ROW_H = 120, 118
HEADS = [["n ×", "Bellman–Ford"], ["Edge", "by edge"], ["Squaring"], ["Floyd–", "Warshall"]]
ROWS = [
    ("per round", [("—", spec.MUTED), ("n^3", spec.FG), ("n^3", spec.FG), ("n^2", spec.GOOD)]),
    ("time", [("up to Θ(n^4)", spec.BAD), ("Θ(n^4)", spec.BAD), ("Θ(n^3 log n)", spec.ACCENT),
              ("Θ(n^3)", spec.GOOD)]),
    ("n = 1000", [("~10^{12}", spec.FG), ("~10^{12}", spec.FG), ("~10^{10}", spec.FG),
                  ("~10^9", spec.GOOD)]),
]


def col_x(k):
    return X0 + sum(COLS[:k])


def table(highlight):
    c = fd.Canvas()
    fd.draw_title(c, sl.TITLES["h2h"])
    y_end = Y0 + HEAD_H + len(ROWS) * ROW_H
    # grid
    for r in range(len(ROWS) + 1):
        y = Y0 + HEAD_H + r * ROW_H
        c.line([(X0, y), (X0 + sum(COLS), y)], spec.GRID, 2)
    for k in range(1, len(COLS)):
        c.line([(col_x(k), Y0 + 10), (col_x(k), y_end - 10)], spec.GRID, 2)
    # headers
    for k, lines in enumerate(HEADS, start=1):
        cx = col_x(k) + COLS[k] / 2
        for n, ln in enumerate(lines):
            cy = Y0 + HEAD_H / 2 + (n - (len(lines) - 1) / 2) * 38
            c.text((cx, cy), ln, spec.FG, BOLD, 30)
    for r, (head, cells) in enumerate(ROWS):
        cy = Y0 + HEAD_H + r * ROW_H + ROW_H / 2
        c.text((X0 + 14, cy), head, spec.MUTED, BOLD, 30, anchor="lm")
        for k, (txt, col) in enumerate(cells, start=1):
            sl.spans(c, (col_x(k) + COLS[k] / 2, cy), [(txt, col, BOLD if "Θ" in txt else SANS, 34)])
    if highlight:
        c.rect((col_x(4) + 4, Y0 + 4, col_x(5) - 4, y_end - 4), outline=spec.GOOD, width=5, radius=14)
        c.text((col_x(4) + COLS[4] / 2, y_end + 50), "✓ fastest", spec.GOOD, BOLD, 32)
    return c.finish()


def main():
    t0 = time.time()
    sl.write_script(HERE, LINES)
    audio, tl, total, n = sl.layout(LINES)
    prev = sl.prev_last("05_floyd_warshall") or table(False)
    kf = [(prev, 0.0), (table(False), sl.LEAD), (table(True), tl["factor"]["start"])]
    sl.render_static(HERE, kf, audio, total)
    print(f"render time {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
