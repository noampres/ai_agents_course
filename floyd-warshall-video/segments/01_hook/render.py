"""Segment 01_hook: motivation. Highway photo -> city map photo with four city markers and
traced roads -> markers become the graph A-D, title bar slides in.

Run from this folder: ../../../kokoro-video/.venv/bin/python render.py [--frames]
"""
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from common import spec  # noqa: E402
from common import fwlib as L  # noqa: E402
from common.fwlib import S, env, ease, fd  # noqa: E402

BEATS = [
    dict(id="map", text="Imagine a map of cities with one-way roads, each with a travel cost."),
    dict(id="nav", text="A navigation app doesn't just need one route; "
                        "^it may need the cheapest route between every pair of cities."),
    dict(id="name", text="That's called the all-pairs shortest-paths problem. "
                         "^Let's state it precisely."),
]
seg = L.Segment(HERE, BEATS)
B = seg.B

# Photos, prepared once (full frame, no radius: the only allowed non-BG frames)
ZMAX = 1.06
HWY = L.photo("cars_highway.jpg", (0, 0, round(spec.W * ZMAX), round(spec.H * ZMAX)),
              focus=(0.5, 0.55)).convert("RGB")
CITY = L.photo("city_road_map.jpg", (0, 0, spec.W, spec.H), darken=0.45).convert("RGBA")

T_X1 = B["nav"]["t0"]                       # highway -> city crossfade start
T_MARK = B["nav"]["cues"][0]               # markers pop in
T_TRACE = T_MARK + 4 * 0.3 * S             # roads trace
T_MORPH = B["name"]["t0"]                  # photo dims, markers become nodes
T_TITLE = B["name"]["cues"][0] - 0.2 * S
EDGES = list(spec.EDGES)


def highway(t):
    z = 1 + (ZMAX - 1) * ease(t / (T_X1 + 0.8 * S))
    w, h = min(HWY.width, spec.W * ZMAX / z), min(HWY.height, spec.H * ZMAX / z)
    x0, y0 = (HWY.width - w) / 2, (HWY.height - h) / 2
    return HWY.resize((spec.W, spec.H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h)).convert("RGBA")


def markers_fn(t):
    def fn(c):
        # traced roads
        for n, (u, v) in enumerate(EDGES):
            x = (t - (T_TRACE + n * 0.2 * S)) / (0.4 * S)
            if x > 0:
                pts = L.partial(fd._edge_geom(u, v)[0], ease(x))
                if len(pts) > 1:
                    c.line(pts, spec.ACCENT, 4)
        for n, node in enumerate(spec.NODES):
            a = ease((t - (T_MARK + n * 0.3 * S)) / (0.2 * S))
            if a > 0:
                p = spec.NODE_POS[node]
                c.circle(p, 26 * a, outline=fd.mix(spec.BG, spec.ACCENT, 0.5), width=4)
                c.circle(p, 14 * a, fill=spec.ACCENT)
    return fn


def draw(t):
    f = L.Frame()
    # photos
    city_a = ease((t - T_X1) / (0.8 * S))
    photo_out = 1 - ease((t - T_MORPH) / (1.0 * S))
    if photo_out > 0 and city_a < 1:
        f.image(highway(t), photo_out)
    if photo_out > 0 and city_a > 0:
        f.image(CITY, city_a * photo_out)
    # markers + traced roads, then crossfade into the drawn graph
    morph = ease((t - T_MORPH) / (0.6 * S))
    if t >= T_MARK and morph < 1:
        f.layer(markers_fn(t), 1 - morph)
    if morph > 0:
        L.graph(f, morph)
    # title bar slides down from y = -70
    ta = ease((t - T_TITLE) / (0.4 * S))
    if ta > 0:
        f.layer(L.divider, ta, key="divider", dy=-70 * (1 - ta))
        f.layer(L.title_text(spec.CHAPTER_TITLES["intro"]), ta,
                key=("title", spec.CHAPTER_TITLES["intro"]), dy=-70 * (1 - ta))
    return f.result()


if __name__ == "__main__":
    seg.render(draw)
