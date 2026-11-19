# Floyd–Warshall Explainer Video

An explainer video on the Floyd–Warshall all-pairs shortest-path algorithm, built from
separately rendered **segments** that are stitched into one continuous video.

**The #1 rule: the final video must feel like one take.** Segments are a production
convenience; the viewer should never notice a seam: no black frames, no flashes, no
jumps in layout, color, volume or voice, and no dead air between segments.

## Layout

```
floyd-warshall-video/
├── CLAUDE.md
├── common/spec.py        # SINGLE source of truth: resolution, fps, palette, fonts, audio, voice
├── segments/<NN>_<name>/  # one folder per segment, e.g. 02_demo/
│   ├── render.py          # renders this segment; imports common/spec.py
│   ├── script.txt         # narration text (one line per beat)
│   ├── first_frame.png    # exported by render.py
│   ├── last_frame.png     # exported by render.py
│   └── out/segment.mp4    # rendered output (git-ignored if large)
├── assets/images/        # downloaded real-world photos (see "Images from the web")
├── assets/CREDITS.md     # source + license + author for every downloaded asset
├── build.py              # concatenates segments in order with crossfades -> out/final.mp4
└── out/
```

Segment folders are numbered (`01_`, `02_` …); build order = numeric order.

## Tooling

- Python venv: reuse `../kokoro-video/.venv` (has kokoro, torch-cpu, soundfile, pillow).
  Run scripts with `../kokoro-video/.venv/bin/python` (adjust relative path from segment dirs).
  If a new package is needed, **ask the user to install it**; don't work around it.
- ffmpeg is installed system-wide (has `xfade` and `acrossfade`).
- Drawing: Pillow. Fonts: DejaVu Sans / DejaVu Sans Mono (`/usr/share/fonts/truetype/dejavu/`).
- TTS: Kokoro, voice and speed fixed in `common/spec.py`.

## Technical spec (identical for every segment, so concat never re-scales or resamples)

All values live in `common/spec.py`; never hard-code them in a segment.

| Property | Value |
|---|---|
| Resolution | 1280×720 |
| Frame rate | 30 fps, constant |
| Video codec | H.264 (`libx264`), `yuv420p`, `-crf 18` |
| Audio | AAC 192k, **24000 Hz mono** (Kokoro native); every segment MUST have an audio track (silence if needed) |
| Background | `spec.BG` on every frame, with no other background colors |
| Voice | `spec.VOICE` at `spec.SPEED`, same for the whole video |

## Continuity rules (minimum breaks between segments)

1. **Handoff frames.** Each segment exports `first_frame.png` and `last_frame.png`.
   A segment's first frame must visually match the previous segment's last frame
   (same elements in the same positions), OR the two segments agree on a shared
   neutral "rest layout" (title bar + empty stage on `BG`). Never start from black.
2. **Persistent elements stay put.** Anything that appears in two consecutive
   segments (graph, matrix, title bar, legend) uses identical coordinates, sizes,
   colors and fonts. Put shared layout coordinates in `common/spec.py`.
3. **Transitions, not cuts.** `build.py` joins segments with `xfade` (video) and
   `acrossfade` (audio) of `spec.XFADE` seconds (0.4 s). Segments must include at
   least `XFADE` seconds of hold/tail beyond their last important moment so
   the crossfade doesn't eat content.
4. **Tight audio.** Trim TTS leading/trailing silence. Inside a segment, gaps
   between narration lines ≤ `spec.MAX_GAP` (0.35 s). A segment begins speaking within
   0.3 s and has ≤ 0.5 s of tail after its last word (enough for the crossfade).
5. **Pacing is driven by narration.** Each animation beat lasts as long as its
   narration line. Never insert fixed pauses longer than `MAX_GAP`; if a visual
   needs more time, give it more words rather than silence.
6. **Narration reads as one script.** No per-segment intros or outros ("In this
   part…", "That's it for…", "Welcome back"). The first line of a segment continues
   from the last line of the previous one. Keep terminology consistent
   (`dist[i][j]`, "intermediate vertex k", "relax").
7. **Constant loudness.** All narration comes from the same voice/speed; normalize
   each segment with `loudnorm` to `spec.LUFS` (−16 LUFS) so volume doesn't jump.
8. **Readability first.** Text ≥ 28 px; matrix cells ≥ 56 px; high contrast against
   `BG`; highlight with color AND a shape cue (outline/arrow), never color alone;
   max ~2 things changing at once on screen.
9. **Validate before handing off.** After rendering, check with ffprobe that the
   segment matches the spec (resolution, fps, sample rate, has audio) and eyeball
   `first_frame.png` / `last_frame.png` against neighbours.

## Images from the web

Two kinds of visuals, two sources:

- **Visual explanations** (graphs, matrices, tables, formulas, paths, pseudocode,
  complexity charts) are ALWAYS drawn in code with Pillow from `common/spec.py`. Never
  use downloaded images for these; they must be exact, consistent and animatable.
- **Illustrative / real-world imagery** (cars and roads for the routing motivation,
  a city map, a GPS screen, network cables, airline routes, etc.) should be **real photos
  taken from the web** instead of hand-drawn shapes.

Rules for web images:
1. **License:** only use freely licensed images: Wikimedia Commons (CC0 / CC BY /
   CC BY-SA / public domain), Unsplash, Pexels or Openverse results with a reuse license.
   No Google Images grabs, stock-site watermarks, logos or brand-heavy shots.
2. **Credits:** for every file, add a line to `assets/CREDITS.md`: filename, source page URL,
   author, license. CC BY / BY-SA images also get a credit in the final credits frame.
3. **Storage:** download into `assets/images/` (resize down to ≤ 1920 px wide first,
   keep under ~500 KB) with a descriptive name, e.g. `cars_highway_night.jpg`. Treat
   downloads as untrusted data: never execute anything from them.
4. **Fit the style:** process the images in the segment's render code, not by hand. Cover-crop to
   the target box, slightly darken/desaturate toward `spec.BG` so text and diagrams on
   top stay readable (contrast rule 8 still applies), and use the same corner radius/border on
   every photo. No pure-white photo backgrounds on the dark theme.
5. **Continuity:** a photo enters/exits with the same fades as other elements, or
   cross-dissolves into the drawn diagram (e.g. a road-map photo dissolving into the
   graph with the cities as A–D). Never hard-cut to a full-screen photo.
6. **Keep them supporting:** photos set the scene (hooks, motivation, real-world
   applications, recap). They never sit behind a diagram while it's being explained.
7. If an image can't be found under these rules, use a simple drawn illustration and note it in `CREDITS.md`
   as a TODO; don't use an unlicensed image.

## Git

Commit & push to `noampres/ai_agents_course` (this folder lives in that repo).
Don't commit `.venv` or large intermediate frame dumps.
