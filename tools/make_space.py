"""Draws assets/space.webp, the ground of every inner page: black space with faint grey
cloud and fine stars (owner's request, 13 Nov 2026). Run by hand; the result is committed.

    python3 tools/make_space.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

W, H = 2400, 1500
OUT = Path(__file__).resolve().parent.parent / "assets" / "space.webp"
rng = np.random.default_rng(20261113)


def noise(cell, octaves=5, fall=0.55):
    """Fractal value noise in 0..1; `cell` is the size in pixels of the largest feature."""
    total = np.zeros((H, W), np.float32)
    amp, norm = 1.0, 0.0
    for _ in range(octaves):
        gw, gh = max(2, W // cell + 2), max(2, H // cell + 2)
        grid = Image.fromarray((rng.random((gh, gw)) * 255).astype(np.uint8))
        layer = np.asarray(grid.resize((W, H), Image.BICUBIC), np.float32) / 255
        total += layer * amp
        norm += amp
        amp *= fall
        cell = max(2, cell // 2)
    return total / norm


def smooth(x, lo, hi):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


# cloud: broad masses, eaten by darker holes, mottled at a finer scale
mass = smooth(noise(620, 4), 0.38, 0.66)
holes = smooth(noise(150, 5), 0.44, 0.58)
mottle = 0.55 + 0.45 * noise(42, 4)
cloud = mass * holes * mottle
grain = 0.8 + 0.4 * rng.random((H, W), dtype=np.float32)
img = cloud * grain * 34.0  # the brightest cloud is about 13% grey

# stars: finer and denser where a second field says so, with a few brighter ones
stars = np.zeros((H, W), np.float32)
dens = 0.25 + 0.75 * smooth(noise(380, 3), 0.35, 0.75)


def scatter(n, lo, hi, weight=None):
    if weight is None:
        ys, xs = rng.integers(0, H, n), rng.integers(0, W, n)
    else:
        ys, xs = rng.integers(0, H, n * 3), rng.integers(0, W, n * 3)
        keep = rng.random(n * 3) < weight[ys, xs]
        ys, xs = ys[keep][:n], xs[keep][:n]
    np.maximum.at(stars, (ys, xs), rng.uniform(lo, hi, len(ys)).astype(np.float32))
    return ys, xs


scatter(9000, 26, 80, dens)       # dust
scatter(1700, 80, 150, dens)      # small stars
ys, xs = scatter(260, 150, 235)   # bright stars
soft = np.asarray(Image.fromarray(stars.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), np.float32)
big = np.zeros((H, W), np.float32)
big[ys, xs] = 255
halo = np.asarray(Image.fromarray(big.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6)), np.float32)
img = np.maximum(img, np.maximum(stars * 0.75, soft * 1.9)) + halo * 5.0

out = np.clip(img, 0, 255).astype(np.uint8)
Image.merge("RGB", [Image.fromarray(out)] * 3).save(OUT, "WEBP", quality=72, method=6)
print(OUT, OUT.stat().st_size // 1024, "KB")
