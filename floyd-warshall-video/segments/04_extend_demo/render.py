"""Segment 04_extend_demo: the edge-by-edge algorithm on the running example
(L1 -> L2 -> L3 via the min-plus product), with the worked cell L2[B][D] in full.

Run (from anywhere):
    /home/noam_wsl_admin/claude_projects/kokoro-video/.venv/bin/python render.py [--frames]

Outputs: out/segment.mp4, first_frame.png, last_frame.png, script.txt, out/timeline.json
         (--frames also dumps check frames into frames/, git-ignored)
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
import extend_draw as xd  # noqa: E402
from extend_draw import INF, NODES, IDX, ease, env, mix  # noqa: E402

OUT = HERE / "out"
TTS_CACHE = OUT / "tts"
FRAMES = HERE / "frames"

TS = spec.TIME_SCALE           # every fixed duration below is scaled by this
LEAD = 0.15 * TS               # silence before the first word (< 0.3 s)
PAD = 0.02                     # silence kept on each side of a trimmed clip
GAP = spec.MAX_GAP - 2 * PAD - 0.01   # silence inserted between lines
TAIL = spec.TAIL - 0.02        # hold after the last word (>= XFADE, <= spec.TAIL)
STRIKE = 0.3 * TS              # strike-through of an old value
SWAP = 0.4 * TS                # old -> new value swap
FLASH = 0.9 * TS               # GOOD outline flash on a changed cell
PATH = 0.8 * TS                # time to grow a highlighted path
LABEL = 0.4 * TS               # label / pill crossfade
assert LEAD < 0.3 and GAP + 2 * PAD <= spec.MAX_GAP and spec.XFADE <= TAIL <= spec.TAIL

# ---------------------------------------------------------------------------------------
# 1. Algorithm: compute L1..L3 with the min-plus product and check against the outline
# ---------------------------------------------------------------------------------------
I_ = INF
OUTLINE_L1 = [[0, 3, I_, 7], [8, 0, 2, I_], [5, I_, 0, 1], [2, I_, I_, 0]]
OUTLINE_L2 = [[0, 3, 5, 7], [7, 0, 2, 3], [3, 8, 0, 1], [2, 5, I_, 0]]
OUTLINE_L3 = [[0, 3, 5, 6], [5, 0, 2, 3], [3, 6, 0, 1], [2, 5, 7, 0]]

Ls, ARGS = xd.extend_tables(3)
L1, L2, L3 = Ls
assert L1 == OUTLINE_L1, L1
assert L2 == OUTLINE_L2, L2
assert L3 == OUTLINE_L3, L3
assert xd.fd.floyd_warshall(L1)[1] == L3          # same answer as Floyd–Warshall
assert xd.min_plus(L3, L1)[0] == L3               # L4 = L3: three edges are enough

WI, WJ = IDX["B"], IDX["D"]                       # worked cell L2[B][D]
WORK = [(L1[WI][k], L1[k][WJ]) for k in range(4)]
assert [a + b for a, b in WORK] == [15, INF, 3, INF]
WMIN = min(range(4), key=lambda k: WORK[k][0] + WORK[k][1])
assert WORK[WJ][1] == 0 and WORK[WJ][0] == L1[WI][WJ]   # k = j row = the old value
W_PATH = xd.path_of(Ls, ARGS, 2, WI, WJ)
assert W_PATH == ["B", "C", "D"], W_PATH

CH2 = xd.changed_cells(L1, L2)                    # row-major
CH3 = xd.changed_cells(L2, L3)
assert {(NODES[i] + NODES[j], new) for i, j, _, new in CH2} == {
    ("AC", 5), ("BA", 7), ("BD", 3), ("CA", 3), ("CB", 8), ("DB", 5)}
assert {(NODES[i] + NODES[j], new) for i, j, _, new in CH3} == {
    ("AD", 6), ("BA", 5), ("CB", 6), ("DC", 7)}
CH2_REST = [c for c in CH2 if (c[0], c[1]) != (WI, WJ)]
FI, FJ = IDX["A"], IDX["D"]                       # featured L3 change A->D
F_PATH = xd.path_of(Ls, ARGS, 3, FI, FJ)
assert F_PATH == ["A", "B", "C", "D"], F_PATH
F_WEIGHTS = [spec.EDGES[(u, v)] for u, v in zip(F_PATH, F_PATH[1:])]
assert sum(F_WEIGHTS) == L3[FI][FJ]
CH3_REST = [c for c in CH3 if (c[0], c[1]) != (FI, FJ)]

WORDS = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
         7: "seven", 8: "eight", 15: "fifteen", INF: "infinity"}


def w(v):
    return WORDS[v]


# ---------------------------------------------------------------------------------------
# 2. Narration (one line per beat). "^name" marks a cue at the following word.
# ---------------------------------------------------------------------------------------
def rest2_line():
    parts = []
    for n, (i, j, old, new) in enumerate(CH2_REST):
        verb = " drops to " if n == 0 else " to "
        conj = "and " if n == len(CH2_REST) - 1 else ""
        parts.append(f"^c{n} {conj}{NODES[i]} to {NODES[j]}{verb}{w(new)}")
    return "The other cells work the same way: " + ", ".join(parts) + "."


def rest3_line():
    parts = []
    for n, (i, j, old, new) in enumerate(CH3_REST):
        verb = " becomes " if n == 0 else ", "
        conj = "and " if n == len(CH3_REST) - 1 else ""
        parts.append(f"^c{n} {conj}{NODES[i]} to {NODES[j]}{verb}{w(new)}")
    return f"{w(len(CH3_REST)).capitalize()} more cells improve: " + ", ".join(parts) + "."


a0, w0 = WORK[0]
LINES = [
    ("intro", "Let's build L two, the shortest paths with at most two edges, "
              "^target starting with one cell in full: from B to D."),
    ("bands", "Row B of L one, which is just W, gives the best path from B to each stop k. "
              "^col Column D of W adds one final edge, from k to D."),
    ("row0", f"^hdr Try every last stop k. ^r Through A: {w(a0)} plus ^w {w(w0)} is ^s {w(a0 + w0)}."),
    ("row1", f"^r Through B: {w(WORK[1][0])} plus ^w {w(WORK[1][1])} ^s is still infinity."),
    ("row2", f"^r Through C: {w(WORK[2][0])} plus ^w {w(WORK[2][1])} is ^s {w(sum(WORK[2]))}."),
    ("row3", f"^r And k equals D ^old just keeps the old value: {w(WORK[3][0])} "
             f"^w plus {w(WORK[3][1])}, ^s still infinity."),
    ("min", f"The smallest of the four is ^min {w(sum(WORK[WMIN]))}, through {NODES[WMIN]}."),
    ("write", "^path That's the route " + ", then ".join(W_PATH)
              + f". So ^write {w(L2[WI][WJ])} replaces infinity, ^lab the first entry of L two."),
    ("rest2", rest2_line()),
    ("m3", "^m3 Now m equals three: ^lab extend L two by one more edge, the same way."),
    ("featured", f"From A to D, the best so far is the direct edge, {w(L2[FI][FJ])}. "
                 f"^path But " + " to ".join(F_PATH) + " costs ^sum "
                 + " plus ".join(w(x) for x in F_WEIGHTS) + f", ^new which is {w(L3[FI][FJ])}."),
    ("rest3", rest3_line()),
    ("close", "Remember, a shortest path needs ^pill at most n minus one, here three, edges, "
              "so L three is our answer."),
]
CUE_RE = re.compile(r"\^(\w+)\s*")


def clean(text):
    return CUE_RE.sub("", text)


# ---------------------------------------------------------------------------------------
# 3. TTS (cached by voice + speed + text), trimming, word-level cue times
# ---------------------------------------------------------------------------------------
_pipe = None


def tts(text):
    """(audio float32, [(word, start, end)]) for text, cached on disk."""
    global _pipe
    key = hashlib.sha1(f"{spec.LANG}|{spec.VOICE}|{spec.SPEED}|{text}".encode()).hexdigest()[:16]
    wav, js = TTS_CACHE / f"{key}.wav", TTS_CACHE / f"{key}.json"
    if wav.exists() and js.exists():
        audio, _ = sf.read(wav, dtype="float32")
        return audio, json.loads(js.read_text())
    if _pipe is None:
        from kokoro import KPipeline
        _pipe = KPipeline(lang_code=spec.LANG, repo_id="hexgrad/Kokoro-82M")
    chunks, words, off = [], [], 0.0
    for res in _pipe(text, voice=spec.VOICE, speed=spec.SPEED):
        a = res.audio.numpy() if hasattr(res.audio, "numpy") else np.asarray(res.audio)
        for t in res.tokens or []:
            if t.start_ts is not None and re.search(r"\w", t.text):
                words.append((t.text, off + t.start_ts, off + (t.end_ts or t.start_ts)))
        chunks.append(a.astype(np.float32))
        off += len(a) / spec.SR
    audio = np.concatenate(chunks)
    TTS_CACHE.mkdir(parents=True, exist_ok=True)
    sf.write(wav, audio, spec.SR)
    js.write_text(json.dumps(words))
    return audio, words


def trim(audio):
    """Cut leading/trailing silence; returns (clip, seconds cut at the start)."""
    thr = 0.02 * np.max(np.abs(audio))
    idx = np.nonzero(np.abs(audio) > thr)[0]
    p = int(PAD * spec.SR)
    s, e = max(0, idx[0] - p), min(len(audio), idx[-1] + p)
    return audio[s:e], s / spec.SR


def build_audio():
    """Lay out all lines; returns (narration, timeline, total seconds)."""
    pieces = [np.zeros(int(round(LEAD * spec.SR)), np.float32)]
    t = len(pieces[0]) / spec.SR
    timeline = []
    for name, raw in LINES:
        text = clean(raw)
        audio, words = tts(text)
        clip, cut = trim(audio)
        dur = len(clip) / spec.SR
        cues, n = {}, 0                          # cue -> index of the following word
        for tok in re.split(r"(\^\w+)", raw):
            if tok.startswith("^"):
                cues[tok[1:]] = n
            else:
                n += len([x for x in tok.split() if re.search(r"\w", x)])
        cue_t = {}
        for cname, wi in cues.items():
            if len(words) == n:
                ct = words[wi][1] - cut
            else:                                # fallback: proportional to characters
                before = clean(raw.split("^" + cname)[0])
                ct = dur * len(before) / max(1, len(text))
                print(f"  ! cue {name}.{cname}: {len(words)} tokens != {n} words, proportional")
            cue_t[cname] = t + min(max(ct, 0.0), dur)
        timeline.append(dict(name=name, text=text, start=t, end=t + dur, cues=cue_t))
        pieces.append(clip)
        t += dur
        g = np.zeros(int(round(GAP * spec.SR)), np.float32)
        pieces.append(g)
        t += len(g) / spec.SR
    t -= len(pieces.pop()) / spec.SR
    tail = np.zeros(int(round(TAIL * spec.SR)), np.float32)
    pieces.append(tail)
    return np.concatenate(pieces), timeline, t + len(tail) / spec.SR


# ---------------------------------------------------------------------------------------
# 4. Frame state
# ---------------------------------------------------------------------------------------
def grow(nodes, col, t0, t, alpha):
    """fw_draw path entries that grow edge by edge from t0 over PATH seconds."""
    segs = list(zip(nodes, nodes[1:]))
    out = []
    for s, (u, v) in enumerate(segs):
        a = ease((t - t0) / PATH * len(segs) - s) * alpha
        if a > 0.01:
            out.append(([u, v], col, a, False))
    return out


def transition(old, new, t0, t, good):
    """Override dict for a changed cell: strike old, swap to new, GOOD colour + mark."""
    return dict(old=old, new=new, strike=(t - t0) / STRIKE, swap=(t - t0 - STRIKE) / SWAP,
                color=mix(spec.FG, spec.GOOD, good),
                mark=min(ease((t - t0 - STRIKE) / SWAP), good))


def frame(t, B):
    """Render the frame at time t. B = {beat name: timeline entry}."""
    def S(name):
        return B[name]["start"]

    def C(name, cue):
        return B[name]["cues"][cue]

    c = xd.Canvas()

    # --- title bar: label crossfades 1 -> 2 -> 3, m pill fades in, then 2 -> 3 ---------
    t_lab2, t_lab3 = C("write", "lab"), C("m3", "lab")
    if t < t_lab2:
        xd.draw_title(c, m=1)
    elif t < t_lab3:
        xd.draw_title(c, label_mix=(1, 2, (t - t_lab2) / LABEL))
    else:
        xd.draw_title(c, label_mix=(2, 3, (t - t_lab3) / LABEL))
    t_m3 = C("m3", "m3")
    if t < t_m3:
        xd.draw_m(c, 2, env(t, S("intro")))
    else:
        a = ease((t - t_m3) / LABEL)
        xd.draw_m(c, 2, 1 - a, box_alpha=1.0)
        xd.draw_m(c, 3, a, box_alpha=0.0)
    xd.draw_formula_strip(c)

    # --- graph (left half; swapped for the work table during the rows) ------------------
    paths, rings = [], {}
    t_tgt = C("intro", "target")
    a_tgt = env(t, t_tgt, S("rest2"))
    t_p = C("write", "path")
    a_p = env(t, t_p, S("rest2"))
    paths += grow(W_PATH, spec.GOOD, t_p, t, a_p)
    a_f = env(t, S("featured"), S("rest3"))
    t_fp = C("featured", "path")
    paths += grow(F_PATH, spec.GOOD, t_fp, t, env(t, t_fp, S("rest3")))
    for n in "ABCD":
        r = []
        if n in (NODES[WI], NODES[WJ]) and a_tgt > 0.01:
            r.append((spec.INFO, a_tgt))
        if n in (NODES[FI], NODES[FJ]) and a_f > 0.01:
            r.append((spec.INFO, a_f))
        if r:
            rings[n] = r
    xd.draw_graph(c, rings=rings, paths=paths)

    # --- matrix ----------------------------------------------------------------------------
    over, outlines, header_hl = {}, [], {}
    t_write = C("write", "write")
    values = L1 if t < t_lab3 else L2
    if t < t_lab3:
        l2_times = {(WI, WJ): t_write}
        l2_times.update({(i, j): C("rest2", f"c{n}") for n, (i, j, _, _) in enumerate(CH2_REST)})
        good = 1 - ease((t - S("m3")) / LABEL)
        for (i, j), t0 in l2_times.items():
            if t >= t0:
                over[(i, j)] = transition(L1[i][j], L2[i][j], t0, t, good)
                if (i, j) != (WI, WJ):
                    outlines.append((i, j, spec.GOOD, env(t, t0, t0 + FLASH), 4))
    l3_times = {(FI, FJ): C("featured", "new")}
    l3_times.update({(i, j): C("rest3", f"c{n}") for n, (i, j, _, _) in enumerate(CH3_REST)})
    good3 = 1 - ease((t - S("close")) / LABEL)
    for (i, j), t0 in l3_times.items():
        if t >= t0:
            over[(i, j)] = transition(L2[i][j], L3[i][j], t0, t, good3)
            if (i, j) != (FI, FJ):
                outlines.append((i, j, spec.GOOD, env(t, t0, t0 + FLASH), 4))

    # worked cell: row B / column D bands (ACCENT), target cell INFO, operands ACCENT
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
    a_ft = env(t, S("featured"), S("rest3"))
    outlines.append((FI, FJ, spec.INFO, a_ft, 4))
    if a_ft > 0.01:
        header_hl = {("r", FI): (spec.INFO, a_ft), ("c", FJ): (spec.INFO, a_ft)}

    if t < t_lab2:
        lab = dict(m=1)
    elif t < t_lab3:
        lab = dict(label_mix=(1, 2, (t - t_lab2) / LABEL))
    else:
        lab = dict(label_mix=(2, 3, (t - t_lab3) / LABEL))
    xd.draw_matrix(c, values, overrides=over, bands=bands, outlines=outlines,
                   header_hl=header_hl, **lab)

    # --- featured caption ---------------------------------------------------------------
    a_cap = env(t, C("featured", "sum"), S("rest3"))
    if a_cap > 0.01:
        a_eq = env(t, C("featured", "new"))
        xd.draw_caption(c, [
            ("→".join(F_PATH) + "   ", spec.INFO, spec.FONT_SANS_BOLD, 30),
            (" + ".join(map(str, F_WEIGHTS)), spec.FG, spec.FONT_MONO, 32),
            (f" = {L3[FI][FJ]}", mix(spec.BG, spec.GOOD, a_eq), spec.FONT_MONO_BOLD, 32),
            (f" < {L2[FI][FJ]}", mix(spec.BG, spec.FG, a_eq), spec.FONT_MONO, 32)], a_cap)

    # --- "<= n - 1" pill, pulsing once on the closing line --------------------------------
    t_pill = C("close", "pill")
    xd.draw_n1_pill(c, pulse=env(t, t_pill, t_pill + 1.2 * TS, fade=LABEL))
    img = c.finish()

    # --- work table, crossfaded with the graph in the left half -------------------------
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


def loudnorm_filter(wav):
    """Two-pass loudnorm: measure the narration, then normalise linearly to spec.LUFS."""
    base = f"loudnorm=I={spec.LUFS}:TP=-1.5:LRA=11"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(wav), "-af",
                        base + ":print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    return (f"{base}:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
            f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
            f":offset={m['target_offset']}:linear=true")


# ---------------------------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------------------------
def main():
    dump = "--frames" in sys.argv
    OUT.mkdir(exist_ok=True)
    (HERE / "script.txt").write_text("\n".join(clean(t) for _, t in LINES) + "\n")

    audio, timeline, total = build_audio()
    sf.write(OUT / "narration.wav", audio, spec.SR)
    B = {b["name"]: b for b in timeline}
    (OUT / "timeline.json").write_text(json.dumps(timeline, indent=1))
    for b in timeline:
        print(f"{b['start']:6.2f}-{b['end']:6.2f}  {b['name']:9s} {b['text']}")
    nframes = int(round(total * spec.FPS))
    print(f"total {total:.2f}s, {nframes} frames, speech {timeline[0]['start']:.2f}s, "
          f"tail {total - timeline[-1]['end']:.2f}s")

    first = frame(0.0, B)
    last = frame((nframes - 1) / spec.FPS, B)
    first.save(HERE / "first_frame.png")
    last.save(HERE / "last_frame.png")
    # handoff contract with segments 03 / 05 (they rebuild these frames via extend_draw)
    assert np.array_equal(np.asarray(first), np.asarray(xd.handoff_frame(1)))
    assert np.array_equal(np.asarray(last), np.asarray(xd.handoff_frame(3)))

    if dump:
        FRAMES.mkdir(exist_ok=True)
        for f in FRAMES.glob("*.png"):
            f.unlink()
        for b in timeline:
            for cname, ct in list(b["cues"].items()) + [("end", b["end"] - 0.03)]:
                tt = ct + 0.4 if cname != "end" else ct
                frame(tt, B).save(FRAMES / f"t{tt:06.2f}_{b['name']}_{cname}.png")

    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{spec.W}x{spec.H}",
           "-r", str(spec.FPS), "-i", "-",
           "-i", str(OUT / "narration.wav"),
           "-map", "0:v", "-map", "1:a",
           *spec.VCODEC_ARGS,
           "-af", loudnorm_filter(OUT / "narration.wav"), *spec.ACODEC_ARGS,
           "-t", f"{nframes / spec.FPS:.3f}",
           str(OUT / "segment.mp4")]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(nframes):
        proc.stdin.write(frame(f / spec.FPS, B).tobytes())
        if f % 300 == 0:
            print(f"  frame {f}/{nframes}")
    proc.stdin.close()
    assert proc.wait() == 0
    print("wrote", OUT / "segment.mp4")


if __name__ == "__main__":
    main()
