"""Make the transparent header marks from andra-horse.png.

The source is a light engraved horse on a black ground. Its luminance becomes
the alpha channel, so the grey shading survives as partial transparency, and
the empty ground is trimmed away. Two files, one per theme:

    assets/andra-mark-light.png   ink horse (#0e1215) for the light theme
    assets/andra-mark-dark.png    light horse (#e9eceb) for the dark theme

The horse's shapes and proportions are untouched; only the ground is removed
and the colour set to each theme's ink. Run: python3 tools/make_mark.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "andra-horse.png"
HEIGHT = 160          # px; shown at 32 to 36 px, so sharp up to 4x screens
FLOOR = 6             # luminance at or below this is ground (JPEG-style noise)
WHITE = 160           # ~99th percentile of the horse's luminance -> fully opaque
INKS = {"light": (0x0E, 0x12, 0x15), "dark": (0xE9, 0xEC, 0xEB)}


def alpha(lum):
    a = np.clip((lum - FLOOR) / (WHITE - FLOOR), 0, 1)
    return (a * 255).round().astype(np.uint8)


def main():
    lum = np.asarray(Image.open(SRC).convert("L")).astype(float)
    a = alpha(lum)
    ys, xs = np.nonzero(a)
    pad = 6
    box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0),
           min(xs.max() + 1 + pad, a.shape[1]), min(ys.max() + 1 + pad, a.shape[0]))
    mask = Image.fromarray(a).crop(box)
    w = round(mask.width * HEIGHT / mask.height)
    mask = mask.resize((w, HEIGHT), Image.LANCZOS)
    mask = mask.point(lambda v: 0 if v <= 2 else v)  # no faint resampling halo
    for theme, ink in INKS.items():
        out = Image.new("RGBA", mask.size, ink + (0,))
        out.putalpha(mask)
        out.save(ROOT / "assets" / f"andra-mark-{theme}.png", optimize=True)
        print(theme, out.size)


if __name__ == "__main__":
    main()
