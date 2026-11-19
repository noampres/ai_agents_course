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
SPEED = 1.2         # narration read 1.2x faster (user request); script text unchanged
TIME_SCALE = 1 / SPEED  # multiply EVERY fixed duration (fades, moves, gaps, holds) by this

# Continuity
XFADE = round(0.4 * TIME_SCALE, 3)     # crossfade between segments (~0.33 s)
MAX_GAP = round(0.35 * TIME_SCALE, 3)  # max silence between narration lines (~0.29 s)
TAIL = round(0.5 * TIME_SCALE, 3)      # hold after the last word of a segment (~0.42 s)
FADE = round(0.25 * TIME_SCALE, 3)     # default fade (~0.21 s)
MOVE = round(0.5 * TIME_SCALE, 3)      # default move/slide (~0.42 s)

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
EDGE_CURVE = 34            # sideways bulge of each arc of a two-way pair (px)

# Standard demo layout (set by segments/07_fw_demo, which was finished first). Every segment
# that shows the matrix / formula / round pill uses exactly these values.
TITLE_FONT_PX = 38         # bold, at x=40; no filled bar, just a GRID divider line at y=69
TITLE_DIVIDER_Y = 69
FORMULA_BOX = (40, 82, W - 40, 138)   # rounded GRID frame, mono 30 px
MATRIX_CELL = 88
MATRIX_HEAD = 60           # header row/column size
MATRIX_X0 = 734            # left edge of the header column
MATRIX_Y0 = 166            # top of the column-header row -> cells span x 794-1146, y 226-578
ROUND_BOX = (W - 220, 12, W - 40, 58)  # "k = A" / "m = 2" pill in the title bar
CAPTION_Y = 636            # one arithmetic caption line under the matrix
