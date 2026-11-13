"""Draws assets/space.webp, the ground of every inner page: black space with a grey cloud
and fine stars (owner's request, 13 Nov 2026).

The cloud's shapes come from tools/space_cloud.png, a small map of the cloud in the owner's
reference (brightness times four). This script enlarges it, gives it back the edges and
fine structure the small map cannot hold, and scatters the stars. It also writes the same
space in three depths (space-cloud.webp, space-stars-far.webp, space-stars-near.webp), which
assets/site.js moves a little against each other. Run by hand; the results are committed.

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


def smooth(x, lo, hi):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def blur(a, r):
    return np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32)


# --- cloud -------------------------------------------------------------------------------
src = Image.open(HERE / "space_cloud.png").convert("L").resize((W, H), Image.BICUBIC)
sharp = blur(np.asarray(src, np.float32), 3)
soft = blur(sharp, 60)
# towards the edges the map is only the rim of the cloud: let it dissolve there
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rad = np.hypot((xx - W * 0.5) / (W * 0.5), (yy - H * 0.52) / (H * 0.5)) + (noise(300, 3) - 0.5) * 0.5
edge = smooth(rad, 0.70, 1.05)
cloud = (sharp * (1 - edge) + soft * edge * 0.8) / 4

# crisper holes: push the mid greys apart, then eat the edges with fine noise
c = cloud / 27.0
c = np.clip(c + (noise(34, 4) - 0.5) * 0.30 * smooth(c, 0.05, 0.5), 0, 1.2)
c = 0.35 * c + 0.65 * smooth(c, 0.16, 0.74) * np.maximum(c, 0.35)
# wisps inside the cloud, and a fine speckle (blurred, so it is powder and not static)
c *= 0.78 + 0.44 * noise(90, 5)
speck = blur(rng.random((H, W), dtype=np.float32) * 255, 0.7) / 255
c *= 0.80 + 0.40 * (speck - 0.5) * 2.4 + 0.20
img = c * 48.0

# --- stars -------------------------------------------------------------------------------
dens = 0.35 + 0.65 * smooth(noise(420, 3), 0.3, 0.75)
dens *= 0.75 + 0.5 * np.clip(c, 0, 1)
stars = np.zeros((H + 40, W + 40), np.float32)


def stamp(n, sigma, lo, hi, halo=0.0):
    k = int(max(2, np.ceil(sigma * 3 if not halo else 16)))
    ax = np.arange(-k, k + 1, dtype=np.float32)
    d2 = ax[:, None] ** 2 + ax[None, :] ** 2
    kern = np.exp(-d2 / (2 * sigma * sigma)) + halo * np.exp(-d2 / (2 * 5.0 ** 2))
    ys, xs = rng.integers(0, H, n * 3), rng.integers(0, W, n * 3)
    keep = rng.random(n * 3) < dens[ys, xs]
    ys, xs = ys[keep][:n], xs[keep][:n]
    # most stars are dim, a few are bright
    v = lo + (hi - lo) * rng.random(len(ys)) ** 2.2
    for y, x, b in zip(ys, xs, v):
        patch = stars[y + 20 - k:y + 21 + k, x + 20 - k:x + 21 + k]
        np.maximum(patch, kern * b, out=patch)


stamp(15000, 0.55, 26, 120)        # dust
stamp(3600, 0.80, 80, 215)         # small stars
stamp(520, 1.15, 150, 255)         # stars
stamp(70, 1.6, 230, 255, 0.10)     # the few bright ones, with a breath of light
img = np.maximum(img, stars[20:-20, 20:-20])

# a little darker towards the corners, so the page's edges and the header sit on black
img *= 1 - 0.35 * smooth(np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)), 0.75, 1.35)

out = np.clip(img, 0, 255).astype(np.uint8)
Image.merge("RGB", [Image.fromarray(out)] * 3).save(OUT, "WEBP", quality=80, method=6)
print(OUT, OUT.stat().st_size // 1024, "KB")


# --- the same space in three depths (assets/site.js moves them a little) -------------------
# Far: the cloud alone. Middle and near: stars on a clear ground, in squares that repeat
# without a seam, so they can slide as far as a page scrolls.
vig = 1 - 0.35 * smooth(np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)), 0.75, 1.35)
far = np.clip(c * 48.0 * vig, 0, 255).astype(np.uint8)
p = OUT.with_name("space-cloud.webp")
Image.merge("RGB", [Image.fromarray(far)] * 3).save(p, "WEBP", quality=76, method=6)
print(p, p.stat().st_size // 1024, "KB")

T = 1600


def tile(name, groups):
    a = np.zeros((T, T), np.float32)
    for n, sigma, lo, hi, halo in groups:
        k = int(max(2, np.ceil(sigma * 3 if not halo else 16)))
        ax = np.arange(-k, k + 1, dtype=np.float32)
        d2 = ax[:, None] ** 2 + ax[None, :] ** 2
        kern = np.exp(-d2 / (2 * sigma * sigma)) + halo * np.exp(-d2 / (2 * 5.0 ** 2))
        ys, xs = rng.integers(0, T, n), rng.integers(0, T, n)
        v = lo + (hi - lo) * rng.random(n) ** 2.2
        for y, x, b in zip(ys, xs, v):
            iy = (np.arange(y - k, y + k + 1) % T)[:, None]
            ix = (np.arange(x - k, x + k + 1) % T)[None, :]
            a[iy, ix] = np.maximum(a[iy, ix], kern * b)
    alpha = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    white = Image.new("L", (T, T), 255)
    q = OUT.with_name(name)
    Image.merge("RGBA", [white, white, white, alpha]).save(q, "WEBP", quality=82, alpha_quality=90, method=6, exact=True)
    print(q, q.stat().st_size // 1024, "KB")


tile("space-stars-far.webp", [(11000, 0.6, 26, 120, 0), (2300, 0.85, 80, 205, 0)])
tile("space-stars-near.webp", [(700, 0.95, 90, 215, 0), (380, 1.35, 150, 255, 0), (46, 1.9, 230, 255, 0.10)])
