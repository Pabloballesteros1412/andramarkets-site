"""Draws assets/space.webp, the ground of every inner page: black space with a grey cloud
and fine stars (owner's request, 13 Nov 2026).

The cloud's shapes come from tools/space_cloud.png, a small map of the cloud in the owner's
reference (brightness times four). This script enlarges it, gives it back the fine grain
the small map cannot hold, and scatters the stars. Run by hand; the result is committed.

    python3 tools/make_space.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "assets" / "space.webp"
W, H = 2400, 2292
rng = np.random.default_rng(20261113)


def noise(cell, octaves=4, fall=0.55):
    total = np.zeros((H, W), np.float32)
    amp, norm = 1.0, 0.0
    for _ in range(octaves):
        gw, gh = max(2, W // cell + 2), max(2, H // cell + 2)
        grid = Image.fromarray((rng.random((gh, gw)) * 255).astype(np.uint8))
        total += np.asarray(grid.resize((W, H), Image.BICUBIC), np.float32) / 255 * amp
        norm += amp
        amp *= fall
        cell = max(2, cell // 2)
    return total / norm


src = Image.open(HERE / "space_cloud.png").convert("L")
cloud = np.asarray(src.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2)), np.float32) / 4
# the fine structure the map is too small to hold: mottling, then the speckle of the cloud
cloud *= 0.72 + 0.56 * noise(26, 3)
cloud *= 0.55 + 0.9 * rng.random((H, W), dtype=np.float32)
img = cloud * 1.7

stars = np.zeros((H, W), np.float32)


def scatter(n, lo, hi):
    ys, xs = rng.integers(0, H, n), rng.integers(0, W, n)
    np.maximum.at(stars, (ys, xs), rng.uniform(lo, hi, n).astype(np.float32))
    return ys, xs


scatter(5200, 30, 90)            # dust
scatter(1300, 90, 170)           # small stars
ys, xs = scatter(240, 170, 245)  # bright stars
soft = np.asarray(Image.fromarray(stars.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32)
big = np.zeros((H, W), np.float32)
big[ys, xs] = 255
halo = np.asarray(Image.fromarray(big.astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.0)), np.float32)
img = np.maximum(img, np.maximum(stars * 0.7, soft * 2.2)) + halo * 7.0

out = np.clip(img, 0, 255).astype(np.uint8)
Image.merge("RGB", [Image.fromarray(out)] * 3).save(OUT, "WEBP", quality=74, method=6)
print(OUT, OUT.stat().st_size // 1024, "KB")
