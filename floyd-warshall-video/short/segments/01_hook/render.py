"""SHORT 01_hook (static, 2 keyframes): highway photo + title -> title bar + graph."""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import shortlib as sl  # noqa: E402
from shortlib import spec, fd  # noqa: E402

LINES = [
    ("app", "A navigation app needs the cheapest route between every pair of cities."),
    ("name", "That's the all-pairs shortest-paths problem."),
]
PHOTO = sl.PROJ / "assets" / "images" / "cars_highway.jpg"


def photo_frame():
    if PHOTO.exists():
        from PIL import Image
        img = sl.photo_full(PHOTO)
        # extra darkening band behind the title for contrast
        # soft vertical gradient (no hard edges): strongest at the title, 0 at y=200/520
        mask = Image.new("L", (1, spec.H), 0)
        for y in range(spec.H):
            d = abs(y - 365) / 160
            mask.putpixel((0, y), int(150 * max(0.0, 1 - d) ** 0.7))
        img = Image.composite(Image.new("RGB", img.size, spec.BG), img,
                              mask.resize((spec.W, spec.H)))
        c = fd.Canvas()
        c.img = img.resize((spec.W * c.SS, spec.H * c.SS), Image.LANCZOS)
        from PIL import ImageDraw
        c.d = ImageDraw.Draw(c.img)
    else:   # TODO fallback: drawn road (no photo found)
        c = fd.Canvas()
        c.polygon([(560, 300), (720, 300), (1100, 720), (180, 720)], spec.GRID)
        for y in range(330, 720, 70):
            c.rect((636, y, 644, y + 30), fill=spec.ACCENT)
    c.text((spec.W / 2, 330), "All-Pairs Shortest Paths", spec.FG, spec.FONT_SANS_BOLD, 60)
    c.text((spec.W / 2, 405), "the cheapest route between every pair", spec.FG,
           spec.FONT_SANS, 32)
    return c.finish()


def main():
    t0 = time.time()
    sl.write_script(HERE, LINES)
    audio, tl, total, n = sl.layout(LINES)
    kf = [(photo_frame(), 0.0), (sl.base_canvas("aps").finish(), tl["name"]["start"])]
    sl.render_static(HERE, kf, audio, total)
    print(f"render time {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
