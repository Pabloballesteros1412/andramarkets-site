"""Make the particle map for the homepage hero from andra-horse.png.

The hero draws the horse with one particle per inked pixel (assets/hero-horse.js).
The drawing they settle into is the horse as the light theme shows it today
(--horse-filter: invert, grayscale, brightness .85, contrast 3; --horse-opacity
.92), the pencil look the owner approved on 31 Oct 2026. The source is upsampled
1.5x before the filter so the strokes stay crisp at hero size.

    assets/horse-particles.png   (and a lossless .webp copy)
                                 R: ink density of each pixel (0 = none)
                                 G: 255 on the outline (inked pixels within 11px
                                    of the ground outside the horse), so the
                                    cloud can sketch the silhouette first
                                 B: 0

Nothing is redrawn: every value comes from the original engraving.
Run: python3 tools/make_horse_particles.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "andra-horse.png"
OUT = ROOT / "assets" / "horse-particles.png"
BOX = (278, 258, 732, 774)    # the horse in the 1024px source, with a small margin
SCALE = 1.5
EDGE = 11                     # px at 1.5x; the light theme leaves the dark outline blank
LUMA = np.array([0.2126, 0.7152, 0.0722])


def main():
    x0, y0, x1, y1 = BOX
    im = Image.open(SRC).convert("RGB").crop(BOX)
    im = im.resize((round((x1 - x0) * SCALE), round((y1 - y0) * SCALE)), Image.LANCZOS)
    rgb = np.asarray(im).astype(np.float64) / 255

    # --horse-filter, then --horse-opacity: what the light theme prints on paper
    g = (1 - rgb) @ LUMA
    g = np.clip((g * 0.85 - 0.5) * 3 + 0.5, 0, 1)
    ink = (1 - g) * 0.92

    # silhouette from the engraving itself: flood the ground in from the corner
    lit = (rgb @ LUMA) > 14 / 255
    ground = Image.fromarray(np.where(lit, 0, 255).astype(np.uint8)).copy()
    ImageDraw.floodfill(ground, (0, 0), 128)
    outside = np.asarray(ground) == 128
    near = np.zeros_like(outside)
    for dy in range(-EDGE, EDGE + 1):
        for dx in range(-EDGE, EDGE + 1):
            if dx * dx + dy * dy <= EDGE * EDGE:
                near |= np.roll(np.roll(outside, dy, 0), dx, 1)

    r = np.round(ink * 255).astype(np.uint8)
    edge = ((r > 10) & near).astype(np.uint8) * 255
    out = np.dstack([r, edge, np.zeros_like(r)])
    Image.fromarray(out, "RGB").save(OUT, optimize=True)
    # The hero loads the lossless WebP copy (same pixels, about a third lighter) and falls
    # back to the PNG where WebP does not decode.
    Image.fromarray(out, "RGB").save(OUT.with_suffix(".webp"), lossless=True, quality=100, method=6)
    print(f"{OUT.relative_to(ROOT)}: {out.shape[1]}x{out.shape[0]}, "
          f"{int((r > 10).sum())} particles, {int((edge > 0).sum())} on the outline")


if __name__ == "__main__":
    main()
