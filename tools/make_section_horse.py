"""Make the horse texture for the section pages' backdrop (assets/section-scene.js).

The section pages sit inside a black sphere of floating particles with the horse at its
far end, black, lit from behind so only its outline catches the light (owner-approved,
31 Oct 2026). This draws the silhouette from andra-horse.png: nothing is redrawn. It is
worked at 2x so the outline comes out smooth, then stored at 512x512 (a power of two, so
the scene can mipmap it; the scene keeps the horse's proportions).

    assets/section-horse.png   R: distance inside the outline (0 at the edge, 1 at 9
                                  source px in): the edge light fades with it
                               G: the body, anti-aliased
                               B: the engraving's own shading inside the body, softened:
                                  a faint modelling, not lines
                               A: distance outside the outline (0 at the edge, 1 at 14
                                  source px out): the light's spill

Run: python3 tools/make_section_horse.py
"""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "andra-horse.png"
OUT = ROOT / "assets" / "section-horse.png"
BOX = (250, 236, 760, 796)   # the horse in the 1024px source, with room for the light's spill
S = 2.0                      # working scale
SIZE = 512


def disc(r):
    d = max(3, int(r * S)) | 1
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (d, d))


def main():
    x0, y0, x1, y1 = BOX
    im = Image.open(SRC).convert("L").crop(BOX)
    lum = np.asarray(im.resize((round((x1 - x0) * S), round((y1 - y0) * S)), Image.LANCZOS)).astype(np.float32) / 255
    h, w = lum.shape

    # the engraving's strokes, closed up and filled from the outside in
    lit = cv2.morphologyEx((lum > 12 / 255).astype(np.uint8) * 255, cv2.MORPH_CLOSE, disc(4))
    flood = lit.copy()
    cv2.floodFill(flood, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 128)
    filled = (flood != 128).astype(np.uint8) * 255

    # the body's core (thin strokes such as the speed lines drop out) ...
    core = cv2.morphologyEx(filled, cv2.MORPH_OPEN, disc(9))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(core)
    core = np.isin(lab, [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] > 6000 * S * S]).astype(np.uint8) * 255
    # ... then the fine parts attached to it come back (ears, mane tips, tail), not the
    # loose speed lines further off
    body8 = core
    for _ in range(int(7 * S)):
        body8 = cv2.bitwise_and(cv2.dilate(body8, disc(1.5)), filled)
    # a smooth outline: blurred and cut at the middle, then lightly anti-aliased
    body8 = (cv2.GaussianBlur(body8.astype(np.float32) / 255, (0, 0), 1.6 * S) > 0.5).astype(np.uint8) * 255
    body = cv2.GaussianBlur(body8.astype(np.float32) / 255, (0, 0), 0.6 * S)

    inside = cv2.distanceTransform(body8, cv2.DIST_L2, 5) / (9 * S)
    outside = cv2.distanceTransform(255 - body8, cv2.DIST_L2, 5) / (14 * S)
    shade = cv2.GaussianBlur(lum, (0, 0), 2.2 * S) * body
    shade = shade / max(float(np.percentile(shade[body > 0.5], 99)), 1e-6)

    layers = [np.clip(inside, 0, 1), body, np.clip(shade, 0, 1), np.clip(outside, 0, 1)]
    # each channel resized on its own: an RGBA resize would treat A as transparency
    chans = [Image.fromarray(np.round(c * 255).astype(np.uint8)).resize((SIZE, SIZE), Image.LANCZOS) for c in layers]
    Image.merge("RGBA", chans).save(OUT, optimize=True)
    print(f"{OUT.relative_to(ROOT)}: {SIZE}x{SIZE} from a {x1 - x0}x{y1 - y0} source box")


if __name__ == "__main__":
    main()
