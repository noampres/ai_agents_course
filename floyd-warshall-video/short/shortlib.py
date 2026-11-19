"""Shared helpers for the SHORT version (SCRIPT_OUTLINE_v4_short.md).

- TTS (Kokoro, cached in short/out/tts), trimming, line layout with ^cue markers
- loudnorm, raw-frame encoding (animated segments) and keyframe holds (static segments)
- small drawing helpers (text with real superscripts, text cards, photo treatment)

All sizes/colours/timings come from common/spec.py; graph/matrix drawing is imported
read-only from segments/07_fw_demo/fw_draw.py and segments/04_extend_demo/extend_draw.py.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image, ImageEnhance

SHORT = Path(__file__).resolve().parent
PROJ = SHORT.parent
for p in (PROJ, PROJ / "segments" / "07_fw_demo", PROJ / "segments" / "04_extend_demo"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
from common import spec  # noqa: E402
import fw_draw as fd  # noqa: E402
import extend_draw as xd  # noqa: E402

SEGS = SHORT / "segments"
TTS_CACHE = SHORT / "out" / "tts"
TS = spec.TIME_SCALE
PAD = 0.02
LEAD = 0.15 * TS                        # silence before the first word (< 0.3 s)
GAP = spec.MAX_GAP - 2 * PAD - 0.01     # silence between lines (+ 2 PAD <= MAX_GAP)
TAIL = spec.TAIL - 0.02                 # hold after the last word (XFADE <= TAIL <= spec.TAIL)
KF_XFADE = spec.MOVE                    # crossfade between keyframes inside a static segment
assert LEAD < 0.3 and GAP + 2 * PAD <= spec.MAX_GAP and spec.XFADE <= TAIL <= spec.TAIL

CUE_RE = re.compile(r"\^(\w+)\s*")
TITLES = {"aps": "All-Pairs Shortest Paths", "ebe": "Edge by Edge",
          "fw": "Floyd–Warshall", "h2h": "Head to Head"}


def clean(text):
    return CUE_RE.sub("", text)


# ---------------------------------------------------------------------------------------
# TTS + layout
# ---------------------------------------------------------------------------------------
_pipe = None


def tts(text):
    """(audio float32, [(word, start, end)]) for text, cached by voice + speed + text."""
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
    thr = 0.02 * np.max(np.abs(audio))
    idx = np.nonzero(np.abs(audio) > thr)[0]
    p = int(PAD * spec.SR)
    s, e = max(0, idx[0] - p), min(len(audio), idx[-1] + p)
    return audio[s:e], s / spec.SR


def layout(lines, extra_tail=0.0):
    """lines = [(name, raw text with ^cue markers)]. Returns (audio, {name: entry}, total,
    nframes). entry = dict(start, end, text, cues={cue: time}). extra_tail = silent hold
    after TAIL (only used for the ending slide)."""
    pieces = [np.zeros(int(round(LEAD * spec.SR)), np.float32)]
    t = len(pieces[0]) / spec.SR
    tl = {}
    order = []
    for name, raw in lines:
        text = clean(raw)
        audio, words = tts(text)
        clip, cut = trim(audio)
        dur = len(clip) / spec.SR
        cues, n = {}, 0
        for tok in re.split(r"(\^\w+)", raw):
            if tok.startswith("^"):
                cues[tok[1:]] = n
            else:
                n += len([x for x in tok.split() if re.search(r"\w", x)])
        cue_t = {}
        for cname, wi in cues.items():
            if len(words) == n and wi < len(words):
                ct = words[wi][1] - cut
            else:
                before = clean(raw.split("^" + cname)[0])
                ct = dur * len(before) / max(1, len(text))
                print(f"  ! cue {name}.{cname}: {len(words)} tokens != {n} words, proportional")
            cue_t[cname] = t + min(max(ct, 0.0), dur)
        tl[name] = dict(name=name, text=text, start=t, end=t + dur, cues=cue_t)
        order.append(name)
        pieces.append(clip)
        t += dur
        g = np.zeros(int(round(GAP * spec.SR)), np.float32)
        pieces.append(g)
        t += len(g) / spec.SR
    t -= len(pieces.pop()) / spec.SR
    total = t + TAIL + extra_tail
    nframes = int(round(total * spec.FPS))
    total = nframes / spec.FPS
    audio = np.concatenate(pieces)
    n_s = int(round(total * spec.SR))
    audio = np.pad(audio, (0, max(0, n_s - len(audio))))[:n_s]
    for name in order:
        e = tl[name]
        print(f"  {e['start']:6.2f}-{e['end']:6.2f}  {name:9s} {e['text']}")
    print(f"  total {total:.2f}s ({nframes} frames)")
    return audio, tl, total, nframes


def loudnorm_filter(wav):
    base = f"loudnorm=I={spec.LUFS}:TP=-1.5:LRA=11"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(wav), "-af",
                        base + ":print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    return (f"{base}:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
            f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
            f":offset={m['target_offset']}:linear=true")


def write_script(seg_dir, lines):
    (seg_dir / "script.txt").write_text("\n".join(clean(t) for _, t in lines) + "\n")


# ---------------------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------------------
def encode_frames(seg_dir, audio, nframes, frame_fn):
    """Animated segment: pipe frame_fn(t) images into ffmpeg; saves first/last frame."""
    out = seg_dir / "out"
    out.mkdir(parents=True, exist_ok=True)
    wav = out / "narration.wav"
    sf.write(wav, audio, spec.SR)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{spec.W}x{spec.H}",
           "-r", str(spec.FPS), "-i", "-", "-i", str(wav),
           "-map", "0:v", "-map", "1:a", *spec.VCODEC_ARGS,
           "-af", loudnorm_filter(wav), *spec.ACODEC_ARGS,
           "-t", f"{nframes / spec.FPS:.3f}", "-movflags", "+faststart",
           str(out / "segment.mp4")]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(nframes):
        img = frame_fn(f / spec.FPS)
        if f == 0:
            img.save(seg_dir / "first_frame.png")
        if f == nframes - 1:
            img.save(seg_dir / "last_frame.png")
        proc.stdin.write(img.tobytes())
        if f % 300 == 0:
            print(f"  frame {f}/{nframes}", flush=True)
    proc.stdin.close()
    assert proc.wait() == 0
    print("wrote", out / "segment.mp4")


def render_static(seg_dir, keyframes, audio, total, xf=KF_XFADE):
    """Static segment: keyframes = [(PIL image, switch time)], first switch time = 0.
    Each keyframe is a PNG held by ffmpeg (-loop 1 -t d); neighbours are joined with
    xfades of length xf centred on the switch times. Narration is muxed + loudnormed."""
    out = seg_dir / "out"
    out.mkdir(parents=True, exist_ok=True)
    wav = out / "narration.wav"
    sf.write(wav, audio, spec.SR)
    n = len(keyframes)
    offs = [None] + [max(0.0, ts - xf / 2) for _, ts in keyframes[1:]]
    for k in range(2, n):
        offs[k] = max(offs[k], offs[k - 1] + xf + 0.05)
    durs = []
    for k in range(n):
        start = 0.0 if k == 0 else offs[k]
        end = (offs[k + 1] + xf) if k + 1 < n else total
        durs.append(round(end - start + 0.1, 3))
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for k, (img, _) in enumerate(keyframes):
        p = out / f"kf{k}.png"
        img.save(p)
        cmd += ["-loop", "1", "-framerate", str(spec.FPS), "-t", f"{durs[k]:.3f}", "-i", str(p)]
    cmd += ["-i", str(wav)]
    fl = [f"[{k}:v]fps={spec.FPS},format=yuv420p,settb=AVTB,setsar=1[v{k}]" for k in range(n)]
    last = "v0"
    for k in range(1, n):
        fl.append(f"[{last}][v{k}]xfade=transition=fade:duration={xf:.3f}:offset={offs[k]:.3f}[x{k}]")
        last = f"x{k}"
    fl.append(f"[{n}:a]{loudnorm_filter(wav)},aresample={spec.SR}[a]")
    cmd += ["-filter_complex", ";".join(fl), "-map", f"[{last}]", "-map", "[a]",
            *spec.VCODEC_ARGS, *spec.ACODEC_ARGS, "-t", f"{total:.3f}",
            "-movflags", "+faststart", str(out / "segment.mp4")]
    subprocess.run(cmd, check=True)
    keyframes[0][0].save(seg_dir / "first_frame.png")
    keyframes[-1][0].save(seg_dir / "last_frame.png")
    print("wrote", out / "segment.mp4", f"({total:.2f}s, {n} keyframes)")


def prev_last(seg_name):
    """Last frame of a previous short segment (for exact handoff)."""
    p = SEGS / seg_name / "last_frame.png"
    return Image.open(p).convert("RGB") if p.exists() else None


def blend_in(prev, img, t, dur=spec.MOVE):
    """Crossfade from the previous segment's last frame into this segment's own state."""
    if prev is None or t >= dur:
        return img
    return Image.blend(prev, img, fd.ease(t / dur))


# ---------------------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------------------
SUP_RE = re.compile(r"\^\{([^}]*)\}|\^(\S)")


def sup_runs(text, color, font, px):
    """'Θ(n^3 log n)' -> draw_runs runs with a real raised superscript (>= MIN_TEXT_PX
    when px >= 34, otherwise MIN_TEXT_PX itself)."""
    sp = max(spec.MIN_TEXT_PX, int(round(px * 0.72)))
    out, pos = [], 0
    for m in SUP_RE.finditer(text):
        if m.start() > pos:
            out.append((text[pos:m.start()], color, font, px, 0))
        out.append((m.group(1) or m.group(2), color, font, sp, 0.42 * px))
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], color, font, px, 0))
    return out


def spans(c, xy, parts, anchor="m"):
    """parts = [(text, colour, font, px)] with ^superscripts; drawn on one line."""
    runs = []
    for t, col, f, px in parts:
        runs += sup_runs(t, col, f, px)
    return xd.draw_runs(c, xy, runs, anchor=anchor)


def spans_width(c, parts):
    return sum(c.text_w(t, f, p) for tt, col, ff, px in parts
               for t, _, f, p, _ in sup_runs(tt, col, ff, px))


def spans_box(c, xy, parts, idx, color, anchor="m", pad=(8, 8), width=3):
    """Draw spans and a rounded outline (shape cue) around parts[idx]."""
    total = spans_width(c, parts)
    x0 = {"m": xy[0] - total / 2, "l": xy[0], "r": xy[0] - total}[anchor]
    a = x0 + spans_width(c, parts[:idx])
    b = a + spans_width(c, parts[idx:idx + 1])
    h = parts[idx][3] * 0.62 + pad[1]
    c.rect((a - pad[0], xy[1] - h, b + pad[0], xy[1] + h), outline=color, width=width, radius=10)
    spans(c, xy, parts, anchor)


def strip(c, parts):
    """Formula strip (spec.FORMULA_BOX) with custom spans."""
    b = spec.FORMULA_BOX
    c.rect(b, outline=spec.GRID, width=2, radius=10)
    spans(c, (spec.W / 2, (b[1] + b[3]) / 2), parts)


def photo_full(path):
    """Cover-crop to the frame, desaturate 20 %, darken 35 % toward spec.BG."""
    im = Image.open(path).convert("RGB")
    sc = max(spec.W / im.width, spec.H / im.height)
    im = im.resize((int(im.width * sc + 0.5), int(im.height * sc + 0.5)), Image.LANCZOS)
    x0, y0 = (im.width - spec.W) // 2, (im.height - spec.H) // 2
    im = im.crop((x0, y0, x0 + spec.W, y0 + spec.H))
    im = ImageEnhance.Color(im).enhance(0.8)
    return Image.blend(im, Image.new("RGB", im.size, spec.BG), 0.35)


def base_canvas(title_key="aps", graph=True):
    c = fd.Canvas()
    fd.draw_title(c, TITLES[title_key])
    if graph:
        fd.draw_graph(c)
    return c
