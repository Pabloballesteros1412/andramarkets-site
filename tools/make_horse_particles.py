"""Make the particle map for the homepage hero from andra-horse.png.

The hero draws the horse with one particle per inked pixel (assets/hero-horse.js).
Since 1 Nov 2026 the drawing they settle into is the horse as the header's mark shows
it (owner: "the small horse beside Andra Markets", tools/make_mark.py): the engraving's
own light becomes ink, so the horse prints in ink on white and in light on black. The
mark's tones are kept with the faintest shading dropped and a gentle curve (TONE), since
particles add up where they overlap and a light wash of them reads as haze. Until then
it was the light theme's pencil look (invert, grayscale, contrast 3). The source is
upsampled 1.5x so the strokes stay crisp at hero size.

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
TONE = (28, 165, 1.35)        # luminance that starts ink, that is full ink, and the curve


def main():
    x0, y0, x1, y1 = BOX
    im = Image.open(SRC).convert("RGB").crop(BOX)
    im = im.resize((round((x1 - x0) * SCALE), round((y1 - y0) * SCALE)), Image.LANCZOS)
    rgb = np.asarray(im).astype(np.float64) / 255

    # the mark's look: the engraving's light is the ink (tools/make_mark.py), its faintest
    # shading dropped and the rest on a gentle curve
    lo, hi, curve = TONE
    ink = np.clip(((rgb @ LUMA) * 255 - lo) / (hi - lo), 0, 1) ** curve

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
