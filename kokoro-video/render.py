"""Render a 5-second video: apple picture + Kokoro TTS voiceover."""
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline
from PIL import Image, ImageDraw

OUT = Path(__file__).parent
TEXT = "test, test"
VOICE = "af_heart"
SR = 24000
DURATION = 5

# 1. Voiceover
pipeline = KPipeline(lang_code="a")  # American English
audio = np.concatenate([a for _, _, a in pipeline(TEXT, voice=VOICE)])
sf.write(OUT / "voiceover.wav", audio, SR)
print(f"voiceover: {len(audio) / SR:.2f}s")

# 2. Apple image (drawn, 1280x720)
W, H = 1280, 720
img = Image.new("RGB", (W, H), (245, 240, 230))
d = ImageDraw.Draw(img)
cx, cy = W // 2, H // 2 + 30
RED = (200, 25, 35)
d.ellipse([cx - 230, cy - 190, cx + 50, cy + 190], fill=RED)             # left lobe
d.ellipse([cx - 50, cy - 190, cx + 230, cy + 190], fill=RED)             # right lobe
d.ellipse([cx - 170, cy - 40, cx + 170, cy + 220], fill=RED)             # rounded bottom
d.ellipse([cx - 25, cy - 200, cx + 25, cy - 150], fill=(150, 15, 25))    # top dimple
d.ellipse([cx - 170, cy - 120, cx - 100, cy - 30], fill=(235, 90, 95))   # highlight
d.rounded_rectangle([cx - 8, cy - 270, cx + 10, cy - 170], radius=8, fill=(100, 60, 25))  # stem
d.ellipse([cx + 10, cy - 280, cx + 130, cy - 225], fill=(60, 150, 50))   # leaf
img.save(OUT / "apple.png")

# 3. Combine: still image + audio padded with silence to exactly 5s
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error",
    "-loop", "1", "-i", str(OUT / "apple.png"),
    "-i", str(OUT / "voiceover.wav"),
    "-af", "apad", "-t", str(DURATION),
    "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "30",
    "-c:a", "aac", "-b:a", "192k",
    str(OUT / "apple_test.mp4"),
], check=True)
print("wrote", OUT / "apple_test.mp4")
