"""Stitch short/segments/*/out/segment.mp4 in numeric order with xfade + acrossfade
of spec.XFADE seconds -> short/out/final.mp4 (CLAUDE.md continuity rule 3)."""
import subprocess
import sys
from pathlib import Path

SHORT = Path(__file__).resolve().parent
sys.path.insert(0, str(SHORT.parent))
from common import spec  # noqa: E402

segs = sorted(SHORT.glob("segments/[0-9][0-9]_*/out/segment.mp4"))
assert len(segs) == 7, segs


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(p)]).decode())


X = spec.XFADE
args, fv, fa = [], [], []
for s in segs:
    args += ["-i", str(s)]
off, v, a = 0.0, "[0:v]", "[0:a]"
for i in range(1, len(segs)):
    off += dur(segs[i - 1]) - X
    fv.append(f"{v}[{i}:v]xfade=transition=fade:duration={X:.3f}:offset={off:.3f}[v{i}]")
    fa.append(f"{a}[{i}:a]acrossfade=d={X:.3f}[a{i}]")
    v, a = f"[v{i}]", f"[a{i}]"
out = SHORT / "out" / "final.mp4"
out.parent.mkdir(exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", *args, "-filter_complex", ";".join(fv + fa),
                "-map", v, "-map", a, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                "-r", str(spec.FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(spec.SR), "-ac", "1",
                "-movflags", "+faststart", str(out)], check=True)
print(f"wrote {out} ({dur(out):.2f}s)")
