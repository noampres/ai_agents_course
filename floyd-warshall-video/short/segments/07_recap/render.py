"""SHORT 07_recap (static): negative-cycle bonus card, summary card, then the 3 s ending
slide (VISUALS.md). The character slot assets/images/ending_character.png is
user-supplied; when it is absent the fallback layout (centred column) is used."""
import sys
import time
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import shortlib as sl  # noqa: E402
from shortlib import spec, fd  # noqa: E402

LINES = [
    ("neg", "Bonus: a negative number on the diagonal at the end reveals a negative cycle."),
    ("sum", "Grow paths edge by edge: n to the fourth. Choose the stepping stones: n cubed. "
            "That's Floyd-Warshall."),
]
END_HOLD = 3.0          # ending slide: deliberate rest, NOT scaled (VISUALS.md)
SANS, BOLD, MONO, MONOB = spec.FONT_SANS, spec.FONT_SANS_BOLD, spec.FONT_MONO, spec.FONT_MONO_BOLD
X = 690
CARD = (660, 160, 1240, 640)
CHARACTER = sl.PROJ / "assets" / "images" / "ending_character.png"
CREDITS = "Photo: PattayaPatrol / Wikimedia Commons (CC BY-SA 4.0)"


def card(rows):
    c = sl.base_canvas("aps")
    c.rect(CARD, outline=spec.GRID, width=2, radius=16)
    for row in rows:
        y, parts = row[:2]
        if len(row) > 2:
            sl.spans_box(c, (X, y), parts, row[2][0], row[2][1], anchor="l")
        else:
            sl.spans(c, (X, y), parts, anchor="l")
    return c.finish()


def mini_graph(c, x0, y0, s=0.5, r=24):
    """Graph A–D at scale s (no weight labels, letters 28 px), path A→B→C→D in GOOD."""
    saved = fd.NODE_POS, fd.NODE_R, fd.EDGE_CURVE
    ax, ay = spec.NODE_POS["A"]
    fd.NODE_POS = {n: (x0 + (x - ax) * s, y0 + (y - ay) * s) for n, (x, y) in spec.NODE_POS.items()}
    fd.NODE_R, fd.EDGE_CURVE = r, spec.EDGE_CURVE * s
    try:
        good = {("A", "B"), ("B", "C"), ("C", "D")}
        for u, v, _ in fd.EDGES:
            pts, _ = fd._edge_geom(u, v)
            col, wd = (spec.GOOD, 5) if (u, v) in good else (spec.MUTED, 3)
            c.line(fd._arrow(c, pts, col, wd), col, wd)
        for n, (x, y) in fd.NODE_POS.items():
            c.circle((x, y), r, fill=spec.BG, outline=spec.FG, width=3)
            c.text((x, y + 1), n, spec.FG, BOLD, 28)
    finally:
        fd.NODE_POS, fd.NODE_R, fd.EDGE_CURVE = saved


def ending_slide():
    c = fd.Canvas()
    fd.draw_title(c, sl.TITLES["aps"])
    has_char = CHARACTER.exists()
    cx = 330 if has_char else spec.W / 2
    anchor = "m"
    c.text((cx, 170), "Thanks for watching!", spec.FG, BOLD, 48)
    sl.spans(c, (cx, 270), [("Edge by edge     ", spec.FG, MONO, 32), ("Θ(n^4)", spec.BAD, BOLD, 34)], anchor)
    sl.spans(c, (cx, 330), [("Floyd–Warshall   ", spec.FG, MONO, 32), ("Θ(n^3)", spec.GOOD, BOLD, 34)], anchor)
    mini_graph(c, cx - 75, 420)
    c.text((spec.W / 2, 680), CREDITS, spec.MUTED, SANS, 20)   # credits: exempt from 28 px
    img = c.finish()
    if has_char:   # contain-fit, bottom-aligned in (800,120)-(1220,640); static (no effects)
        ch = Image.open(CHARACTER).convert("RGBA")
        bw, bh = 420, 520
        sc = min(bw / ch.width, bh / ch.height)
        ch = ch.resize((int(ch.width * sc), int(ch.height * sc)), Image.LANCZOS)
        img.paste(ch, (800 + (bw - ch.width) // 2, 640 - ch.height), ch)
    return img


def main():
    t0 = time.time()
    sl.write_script(HERE, LINES)
    audio, tl, total, n = sl.layout(LINES, extra_tail=END_HOLD + sl.KF_XFADE / 2)
    k1 = card([
        (215, [("BONUS", spec.MUTED, BOLD, 28)]),
        (300, [("dist[i][i] < 0", spec.BAD, MONOB, 36)], (0, spec.BAD)),
        (380, [("at the end", spec.FG, SANS, 30)]),
        (470, [("⇒  ", spec.FG, SANS, 32), ("negative cycle", spec.BAD, BOLD, 34)]),
    ])
    k2 = card([
        (215, [("Grow paths edge by edge", spec.FG, SANS, 30)]),
        (275, [("Θ(n^4)", spec.BAD, BOLD, 40)]),
        (395, [("Choose the stepping stones", spec.FG, SANS, 30)]),
        (455, [("Θ(n^3)", spec.GOOD, BOLD, 40)], (0, spec.GOOD)),
        (540, [("= Floyd–Warshall", spec.GOOD, BOLD, 32)]),
    ])
    prev = sl.prev_last("06_compare") or k1
    t_end = tl["sum"]["end"] + sl.TAIL
    kf = [(prev, 0.0), (k1, sl.LEAD), (k2, tl["sum"]["start"]), (ending_slide(), t_end)]
    sl.render_static(HERE, kf, audio, total)
    print("ending slide:", "with character" if CHARACTER.exists() else "fallback layout (no character)")
    print(f"render time {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
