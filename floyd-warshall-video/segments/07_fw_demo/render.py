"""Segment 07_fw_demo: Floyd-Warshall walkthrough on the running example.

Run:  ../../../kokoro-video/.venv/bin/python render.py        (from this folder)
      add --frames to also dump a few PNG check frames into frames/

Outputs: out/segment.mp4, first_frame.png, last_frame.png, script.txt
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from common import spec  # noqa: E402
import fw_draw as fd  # noqa: E402
from fw_draw import INF, NODES, IDX, env, ease, mix  # noqa: E402

# Fixed node positions come from common/spec.py (shared with other segments):
#   A (170, 300)  B (470, 300)  C (470, 590)  D (170, 590), radius spec.NODE_R
NODE_POS = spec.NODE_POS

OUT = HERE / "out"
TTS_CACHE = OUT / "tts"
FRAMES = HERE / "frames"

LEAD = 0.12      # silence before the first word (must be < 0.3 s)
GAP = 0.22 * spec.TIME_SCALE       # silence between beats (< spec.MAX_GAP incl. trim padding)
PAD = 0.02       # silence kept on each side of a trimmed clip
S = spec.TIME_SCALE  # every fixed animation duration below is scaled by this (narration speed-up)
CUE = "^"        # cue marker inside narration text (stripped before TTS)

WORDS = {0: "zero", 1: "one", 2: "two", 3: "three", 5: "five", 6: "six", 7: "seven",
         8: "eight", 12: "twelve", 15: "fifteen", INF: "infinity"}

# ---------------------------------------------------------------------------------
# 1. Algorithm: compute, record every check, assert against SCRIPT_OUTLINE.md
# ---------------------------------------------------------------------------------
EXPECTED = {
    "A": {("B", "D"): 15, ("C", "B"): 8, ("D", "B"): 5},
    "B": {("A", "C"): 5, ("D", "C"): 7},
    "C": {("A", "D"): 6, ("B", "A"): 7, ("B", "D"): 3},
    "D": {("B", "A"): 5, ("C", "A"): 3, ("C", "B"): 6},
}
FINAL = [[0, 3, 5, 6], [5, 0, 2, 3], [3, 6, 0, 1], [2, 5, 7, 0]]

rounds, final, _ = fd.floyd_warshall(fd.INITIAL)
for k, ups in enumerate(rounds):
    got = {(NODES[i], NODES[j]): new for i, j, _, new, _, _ in ups}
    assert got == EXPECTED[NODES[k]], (NODES[k], got)
assert final == FINAL, final


def simulate_checks():
    """Every (k, i, j) check with the values and detour path at that moment."""
    d = [r[:] for r in fd.INITIAL]
    nxt = [[(j if d[i][j] < INF and i != j else None) for j in range(4)] for i in range(4)]
    checks = {}
    for k in range(4):
        for i in range(4):
            for j in range(4):
                if k in (i, j) or i == j:
                    continue
                a, b, old = d[i][k], d[k][j], d[i][j]
                path = None
                if a < INF and b < INF:
                    p1 = fd.path_nodes(nxt, i, k)
                    p2 = fd.path_nodes(nxt, k, j)
                    path = [NODES[x] for x in p1 + p2[1:]]
                better = a + b < old
                checks[(k, i, j)] = dict(a=a, b=b, old=old, new=a + b if better else old,
                                         better=better, path=path)
                if better:
                    d[i][j] = a + b
                    nxt[i][j] = nxt[i][k]
    assert d == FINAL
    return checks


CHECKS = simulate_checks()

# ---------------------------------------------------------------------------------
# 2. Beats (narration drives timing). '^' marks cue points used by the animation.
# ---------------------------------------------------------------------------------
BEATS = [
    dict(kind="round", k="A",
         text="Let's start with k equals A. ^Row A and column A form the pivot cross, "
              "since every detour through A uses one value from each."),
    dict(kind="check", k="A", ij="BC",
         text="B to C: ^eight plus infinity is still infinity, ^so the direct two stays."),
    dict(kind="check", k="A", ij="BD",
         text="B to D: ^eight plus seven is fifteen, ^less than infinity, ^so we write fifteen."),
    dict(kind="check", k="A", ij="CB",
         text="C to B: ^five plus three is eight, ^also better than infinity."),
    dict(kind="check", k="A", ij="CD",
         text="C to D: ^five plus seven is twelve, ^worse than the direct one."),
    dict(kind="check", k="A", ij="DB",
         text="D to B: ^two plus three is five, ^better than infinity."),
    dict(kind="check", k="A", ij="DC",
         text="D to C: ^two plus infinity is still infinity, ^so nothing changes."),
    dict(kind="round", k="B",
         text="Now k equals B, so paths may pass through A and B."),
    dict(kind="check", k="B", ij="AC",
         text="A to C: ^three plus two ^gives five."),
    dict(kind="check", k="B", ij="DC",
         text="D to C: ^five plus two ^gives seven. "
              "Notice that this five already uses the detour through A."),
    dict(kind="fast", k="C", ups=["AD", "BA", "BD"],
         text="With k equals C, we find three more shortcuts: ^A to D drops to six, "
              "^B to A to seven, and ^B to D to three."),
    dict(kind="fast", k="D", ups=["BA", "CA", "CB"],
         text="Finally, k equals D: ^B to A becomes five, ^C to A three, and ^C to B six."),
    dict(kind="final",
         text="After the last round, every entry is now the true shortest distance, "
              "the same table the edge-by-edge method found."),
]


def validate_beats():
    for b in BEATS:
        txt = b["text"].lower()
        if b["kind"] == "check":
            k, i, j = IDX[b["k"]], IDX[b["ij"][0]], IDX[b["ij"][1]]
            c = CHECKS[(k, i, j)]
            b["c"] = c
            for v in (c["a"], c["b"]):
                assert WORDS[v] in txt, (b["text"], v)
            if c["better"]:
                assert WORDS[c["new"]] in txt, b["text"]
        elif b["kind"] == "fast":
            k = IDX[b["k"]]
            want = {(NODES[i], NODES[j]): new for i, j, _, new, _, _ in rounds[k]}
            assert {(u[0], u[1]) for u in b["ups"]} == set(want), b
            assert b["text"].count(CUE) == len(b["ups"])
            for u in b["ups"]:
                assert WORDS[want[(u[0], u[1])]] in txt, (b["text"], u)
    # every round-A check is narrated, and every k=B improvement
    nA = [b for b in BEATS if b["kind"] == "check" and b["k"] == "A"]
    assert len(nA) == sum(1 for (k, _, _) in CHECKS if k == 0)
    nB = {b["ij"] for b in BEATS if b["kind"] == "check" and b["k"] == "B"}
    assert nB == {NODES[i] + NODES[j] for i, j, *_ in rounds[1]}


validate_beats()


# ---------------------------------------------------------------------------------
# 3. TTS per beat, trimmed, with word timestamps for cue markers
# ---------------------------------------------------------------------------------
_pipe = None


def tts(text):
    """Return (audio float32 trimmed, cue_times relative to trimmed start)."""
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

    # trim silence
    loud = np.where(np.abs(audio) > 0.006)[0]
    s0 = max(0, loud[0] - int(PAD * sr))
    s1 = min(len(audio), loud[-1] + int(PAD * sr))
    audio = audio[s0:s1]
    t0 = s0 / sr

    # cue markers -> time of the first token at/after the marker
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
        if ts is None:                      # fallback: proportional position
            ts = t0 + (len(audio) / sr) * m / len(clean)
        cues.append(max(0.0, ts - t0))
    return audio, cues


# ---------------------------------------------------------------------------------
# 4. Timeline
# ---------------------------------------------------------------------------------
def build_timeline():
    t = LEAD
    clips = []
    for b in BEATS:
        a, cues = tts(b["text"])
        dur = len(a) / spec.SR
        b.update(t0=t, t1=t + dur, dur=dur, cues=[t + c for c in cues])
        clips.append((t, a))
        t += dur + GAP
    total = BEATS[-1]["t1"] - PAD + spec.TAIL   # t1 includes PAD of trailing silence
    n = int(round(total * spec.FPS))
    total = n / spec.FPS
    audio = np.zeros(int(round(total * spec.SR)), dtype=np.float32)
    for st, a in clips:
        i = int(round(st * spec.SR))
        audio[i:i + len(a)] += a[: len(audio) - i]
    return audio, n, total


# Animation events derived from beats --------------------------------------------
def plan():
    """Build per-element envelopes from the beat timings."""
    P = dict(pivots=[], focus=[], captions=[], paths=[], changes={}, frame=None)
    round_start = {}
    for b in BEATS:
        if b["kind"] in ("round", "fast"):
            round_start[b["k"]] = b["t0"]
    final_b = BEATS[-1]
    ks = list(round_start)
    round_end = {k: (round_start[ks[n + 1]] if n + 1 < len(ks) else final_b["t0"])
                 for n, k in enumerate(ks)}

    for n, k in enumerate(ks):
        rs = round_start[k]
        b = next(x for x in BEATS if x.get("k") == k and x["kind"] in ("round", "fast"))
        t_in = b["cues"][0] if (b["kind"] == "round" and k == "A") else rs + (0.25 * S if n else 0)
        P["pivots"].append(dict(k=IDX[k], t_in=t_in, t_out=round_end[k], pill_in=rs))

    for b in BEATS:
        if b["kind"] == "check":
            k, i, j = IDX[b["k"]], IDX[b["ij"][0]], IDX[b["ij"][1]]
            c = b["c"]
            t_out = b["t1"] - 0.05
            P["focus"].append(dict(i=i, j=j, k=k, t_in=b["t0"] - 0.1 * S, t_out=t_out))
            cue0, cue1 = b["cues"][0], b["cues"][1]
            ok = c["better"]
            rel = "<" if ok else "≥"
            runs = [
                (f"{NODES[i]}→{NODES[j]}", spec.INFO, spec.FONT_MONO_BOLD, 36, ("in", cue0 - 0.15 * S)),
                ("  ", spec.FG, spec.FONT_MONO, 36, ("in", cue0)),
                (f"{fd.fmt(c['a'])} + {fd.fmt(c['b'])} = {fd.fmt(c['a'] + c['b'])}",
                 spec.FG, spec.FONT_MONO, 36, ("in", cue0)),
                (f" {rel} {fd.fmt(c['old'])}  ", spec.GOOD if ok else spec.BAD,
                 spec.FONT_MONO, 36, ("in", cue1)),
                ("✓" if ok else "✗", spec.GOOD if ok else spec.BAD, spec.FONT_SANS_BOLD, 40,
                 ("in", cue1)),
            ]
            P["captions"].append(dict(runs=runs, t_in=cue0 - 0.15 * S, t_out=t_out))
            if c["path"]:
                P["paths"].append(dict(nodes=c["path"], color=spec.GOOD if ok else spec.BAD,
                                       dashed=not ok, t_in=cue1, t_out=t_out))
            if ok:
                tc = b["cues"][2] if len(b["cues"]) > 2 else cue1 + 0.3 * S
                P["changes"].setdefault((i, j), []).append(
                    dict(t=tc, old=fd.fmt(c["old"]), new=fd.fmt(c["new"]), end=round_end[b["k"]]))
        elif b["kind"] == "fast":
            k = IDX[b["k"]]
            info = {(NODES[i] + NODES[j]): (i, j, old, new) for i, j, old, new, _, _ in rounds[k]}
            runs = []
            t_out = b["t1"] - 0.05
            for n, (u, cue) in enumerate(zip(b["ups"], b["cues"])):
                i, j, old, new = info[u]
                P["focus"].append(dict(i=i, j=j, k=None, t_in=cue - 0.1 * S,
                                       t_out=min(cue + 1.0 * S, t_out)))
                P["changes"].setdefault((i, j), []).append(
                    dict(t=cue + 0.3 * S, old=fd.fmt(old), new=fd.fmt(new), end=round_end[b["k"]]))
                if n:
                    runs.append(("   •   ", spec.MUTED, spec.FONT_SANS_BOLD, 30, ("in", cue + 0.3 * S)))
                runs.append((f"{u[0]}→{u[1]}", spec.INFO, spec.FONT_MONO_BOLD, 32, ("in", cue + 0.3 * S)))
                runs.append((f" {fd.fmt(new)}", spec.GOOD, spec.FONT_MONO_BOLD, 32, ("in", cue + 0.3 * S)))
            P["captions"].append(dict(runs=runs, t_in=b["cues"][0], t_out=t_out))
        elif b["kind"] == "final":
            P["frame"] = dict(t_in=b["t0"] + 0.3 * S, t_out=b["t1"] - 0.3 * S)
    return P


def cell_state(P, i, j, t):
    base = fd.fmt(fd.INITIAL[i][j])
    ch = [c for c in P["changes"].get((i, j), []) if c["t"] <= t]
    if not ch:
        return {"text": base, "color": spec.FG}
    c = ch[-1]
    dt = t - c["t"]
    # (x TIME_SCALE) 0-0.25 s strike old value, hold, 0.4-0.8 s old out / new in
    good = env(t, c["t"] + 0.6 * S, c["end"])
    st = {"text": c["new"], "color": mix(spec.FG, spec.GOOD, good), "mark": good}
    if dt < 0.8:
        st["color"] = spec.GOOD
        st.update(old=c["old"], strike=dt / (0.25 * S), swap=(dt - 0.4 * S) / (0.4 * S))
    return st


def draw_frame(P, t):
    c = fd.Canvas()
    fd.draw_title(c)
    fd.draw_formula(c)

    # pivot cross + k pill (sequential crossfade between rounds)
    pivot, rings = None, {n: [] for n in NODES}
    pill_box = 0.0
    for pv in P["pivots"]:
        a = env(t, pv["t_in"], pv["t_out"])
        if a > 0.01:
            pivot = (pv["k"], a)
            rings[NODES[pv["k"]]].append((spec.ACCENT, a))
        pa = env(t, pv["pill_in"] + 0.25 * S, pv["t_out"])
        if pa > 0.01:
            fd.draw_k(c, NODES[pv["k"]], pa, box_alpha=0)
        pill_box = max(pill_box, env(t, P["pivots"][0]["pill_in"], P["pivots"][-1]["t_out"]))
    if pill_box > 0.01:
        fd.draw_k(c, "", 0, box_alpha=pill_box)

    outlines, header_hl = [], {}
    for f in P["focus"]:
        a = env(t, f["t_in"], f["t_out"])
        if a <= 0.01:
            continue
        i, j, k = f["i"], f["j"], f["k"]
        if k is not None:   # operand cells dist[i][k], dist[k][j]
            outlines.append((i, k, spec.ACCENT, a, 5))
            outlines.append((k, j, spec.ACCENT, a, 5))
        outlines.append((i, j, spec.INFO, a, 6))
        header_hl[("r", i)] = (spec.INFO, a)
        header_hl[("c", j)] = (spec.INFO, a)
        rings[NODES[i]].insert(0, (spec.INFO, a))
        rings[NODES[j]].insert(0, (spec.INFO, a))

    paths = [(p["nodes"], p["color"], env(t, p["t_in"], p["t_out"]), p["dashed"])
             for p in P["paths"]]
    fd.draw_graph(c, rings=rings, paths=paths)

    cells = [[cell_state(P, i, j, t) for j in range(4)] for i in range(4)]
    fd.draw_matrix(c, cells, pivot=pivot, outlines=outlines, header_hl=header_hl)

    if P["frame"]:
        fa = env(t, P["frame"]["t_in"], P["frame"]["t_out"], fade=0.3 * S)
        if fa > 0.01:
            b0, b1 = fd.cell_box(0, 0), fd.cell_box(3, 3)
            c.rect((b0[0] - 8, b0[1] - 8, b1[2] + 8, b1[3] + 8),
                   outline=mix(spec.BG, spec.GOOD, fa), width=4, radius=8)

    for cap in P["captions"]:
        a = env(t, cap["t_in"], cap["t_out"])
        if a <= 0.01:
            continue
        runs = [(tx, col, f, px, env(t, w[1])) for tx, col, f, px, w in cap["runs"]]
        fd.draw_caption(c, runs, a)
    return c.finish()


# ---------------------------------------------------------------------------------
# 5. Render
# ---------------------------------------------------------------------------------
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
    print(f"total {total:.2f}s, {n} frames")
    for b in BEATS:
        print(f"  {b['t0']:6.2f}-{b['t1']:6.2f} ({b['dur']:5.2f}s) {b['kind']:5s} "
              f"{b['text'].replace(CUE, '')}")
    (OUT / "timeline.json").write_text(json.dumps(
        [{k: b[k] for k in ("kind", "t0", "t1", "dur", "cues", "text")} for b in BEATS], indent=1))

    cmd = (["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{spec.W}x{spec.H}",
            "-r", str(spec.FPS), "-i", "-", "-i", str(OUT / "narration.wav")]
           + spec.VCODEC_ARGS + spec.ACODEC_ARGS
           + ["-t", f"{total:.3f}", "-movflags", "+faststart", str(OUT / "segment.mp4")])
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    if dump:
        FRAMES.mkdir(exist_ok=True)
    for f in range(n):
        t = f / spec.FPS
        img = draw_frame(P, t)
        if f == 0:
            img.save(HERE / "first_frame.png")
        if f == n - 1:
            img.save(HERE / "last_frame.png")
        if dump and f % (spec.FPS // 2) == 0:
            img.save(FRAMES / f"t{t:06.2f}.png")
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    assert proc.wait() == 0
    print("wrote", OUT / "segment.mp4")


if __name__ == "__main__":
    main()
