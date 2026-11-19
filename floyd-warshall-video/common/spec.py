"""Shared spec for every segment of the Floyd-Warshall video. Import, never copy values."""
from pathlib import Path

# Video
W, H = 1280, 720
FPS = 30
VCODEC_ARGS = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-r", str(FPS)]

# Audio
SR = 24000  # Kokoro native sample rate, mono
ACODEC_ARGS = ["-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-ac", "1"]
LUFS = -16

# Voice
LANG = "a"          # American English
VOICE = "af_heart"
SPEED = 1.0

# Continuity
XFADE = 0.4         # seconds of crossfade between segments
MAX_GAP = 0.35      # max silence between narration lines inside a segment
TAIL = 0.5          # hold after the last word of a segment

# Palette (dark theme, high contrast)
BG = (18, 22, 33)
FG = (235, 238, 245)
MUTED = (130, 140, 160)
GRID = (60, 68, 88)
ACCENT = (255, 196, 61)    # current k / focus
GOOD = (80, 200, 120)      # improved distance
BAD = (235, 90, 90)        # rejected / no improvement
INFO = (90, 160, 255)      # i/j cursor

# Fonts
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
FONT_SANS = FONT_DIR / "DejaVuSans.ttf"
FONT_SANS_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
FONT_MONO = FONT_DIR / "DejaVuSansMono.ttf"
FONT_MONO_BOLD = FONT_DIR / "DejaVuSansMono-Bold.ttf"
MIN_TEXT_PX = 28

# Shared layout (persistent elements keep these positions across segments)
TITLE_BAR = (0, 0, W, 70)          # top bar with section title
STAGE = (40, 90, W - 40, H - 30)   # main drawing area
GRAPH_BOX = (40, 90, 600, H - 30)  # left half: graph
MATRIX_BOX = (640, 90, W - 40, H - 30)  # right half: distance matrix

# Running example graph (shared by ALL segments, see SCRIPT_OUTLINE.md)
INF = float("inf")
NODES = ["A", "B", "C", "D"]
EDGES = {  # (from, to): weight
    ("A", "B"): 3, ("A", "D"): 7,
    ("B", "A"): 8, ("B", "C"): 2,
    ("C", "A"): 5, ("C", "D"): 1,
    ("D", "A"): 2,
}
# Node centers inside GRAPH_BOX (top band y<170 reserved for the formula strip).
# A<->B and A<->D are two-way: draw those pairs as two curved arrows.
NODE_POS = {"A": (170, 300), "B": (470, 300), "C": (470, 590), "D": (170, 590)}
NODE_R = 36
