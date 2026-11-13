"""Draws the space behind every inner page (owner's requests, 13 Nov 2026): a grey nebula
and stars on black, in three depths that assets/site.js slides against each other.

    assets/space-cloud.webp        the nebula, far off (with the faintest star dust in it)
    assets/space-stars-far.webp    far stars, a clear square that repeats without a seam
    assets/space-stars-near.webp   near stars, the same, with the few bright ones
    assets/space.webp              the three together, still: reduced motion and no JavaScript

The nebula's broad shape comes from tools/space_cloud.png, a small map of the cloud in the
owner's reference (brightness times four); everything finer is drawn here. Run by hand; the
results are committed.

    python3 tools/make_space.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
W, H = 2400, 2292
T = 2048
rng = np.random.default_rng(20261113)


def lattice(w, h, cell, periodic=False):
    gw, gh = max(2, round(w / cell)), max(2, round(h / cell))
    g = rng.random((gh, gw)).astype(np.float32)
    if periodic:
        big = Image.fromarray((np.tile(g, (3, 3)) * 255).astype(np.uint8)).resize((w * 3, h * 3), Image.BICUBIC)
        return np.asarray(big.crop((w, h, w * 2, h * 2)), np.float32) / 255
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255


def fbm(w, h, cell, octaves=6, fall=0.52, periodic=False):
    total, amp, norm = np.zeros((h, w), np.float32), 1.0, 0.0
    for _ in range(octaves):
        total += lattice(w, h, cell, periodic) * amp
        norm += amp
        amp *= fall
        cell = max(3, cell / 2)
    return total / norm


def smooth(x, lo, hi):
    t = np.clip((x - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def blur(a, r, scale=1.0):
    im = Image.fromarray(np.clip(a * scale, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im, np.float32) / scale


def sample(a, x, y):
    """`a` read at the (fractional) places x, y; black outside."""
    h, w = a.shape
    x0, y0 = np.floor(x).astype(np.int32), np.floor(y).astype(np.int32)
    fx, fy = x - x0, y - y0
    out = np.zeros_like(x, dtype=np.float32)
    for dy, wy in ((0, 1 - fy), (1, fy)):
        for dx, wx in ((0, 1 - fx), (1, fx)):
            xi, yi = x0 + dx, y0 + dy
            ok = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
            out += np.where(ok, a[np.clip(yi, 0, h - 1), np.clip(xi, 0, w - 1)], 0) * wx * wy
    return out


def save(name, img, alpha=None, quality=86):
    p = ASSETS / name
    g = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    if alpha is None:
        Image.merge("RGB", [g] * 3).save(p, "WEBP", quality=quality, method=6)
    else:
        a = Image.fromarray(np.clip(alpha, 0, 255).astype(np.uint8))
        Image.merge("RGBA", [g, g, g, a]).save(p, "WEBP", quality=quality, alpha_quality=92, method=6, exact=True)
    print(p.name, p.stat().st_size // 1024, "KB")


# --- nebula ------------------------------------------------------------------------------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
src = Image.open(HERE / "space_cloud.png").convert("L").resize((W, H), Image.BICUBIC)
base = blur(np.asarray(src, np.float32), 9) / 4 / 26.0        # 0..1, the reference's masses

# bend the masses so no edge is a smooth blob: one broad warp, one fine
wx, wy = fbm(W, H, 520, 5) - 0.5, fbm(W, H, 520, 5) - 0.5
vx, vy = fbm(W, H, 110, 4) - 0.5, fbm(W, H, 110, 4) - 0.5
X, Y = xx + wx * 260 + vx * 70, yy + wy * 260 + vy * 70
mass = sample(base, X, Y)
# it dissolves towards the edges of the picture
rad = np.hypot((xx - W * 0.5) / (W * 0.5), (yy - H * 0.52) / (H * 0.5)) + (fbm(W, H, 320, 3) - 0.5) * 0.6
mass *= 1 - smooth(rad, 0.72, 1.12)

# gas: fractal detail read through the same warp, so the wisps follow the masses
detail = sample(fbm(W, H, 300, 7, 0.56), X, Y)
ridge = 1 - np.abs(sample(fbm(W, H, 420, 6, 0.55), X + 400, Y + 250) * 2 - 1)   # bright filaments
lanes = 1 - np.abs(sample(fbm(W, H, 360, 6, 0.55), X - 300, Y + 600) * 2 - 1)   # dark dust lanes
gas = smooth(mass, 0.06, 0.90) * (0.30 + 1.25 * smooth(detail, 0.30, 0.78))
gas *= 0.70 + 0.75 * ridge ** 3
gas *= 1 - 0.80 * smooth(lanes, 0.80, 0.97)
gas = np.clip(gas, 0, 1.6) ** 1.25
# light spreads a little inside the gas
gas = 0.80 * gas + 0.30 * blur(gas, 28, 150) + 0.12 * blur(gas, 110, 150)
# the gas never passes 40 of 255 (#282828): the greyest text of the site (--ink-3) still reads
# on it at 4.5 to 1
neb = 40.0 * np.tanh(gas * 34.0 / 40.0)

# unresolved stars inside the gas, the faintest dust
dust = np.zeros((H, W), np.float32)
n = 60000
ys, xs = rng.integers(0, H, n), rng.integers(0, W, n)
keep = rng.random(n) < np.clip(gas[ys, xs] * 1.1 + 0.04, 0, 1)
np.maximum.at(dust, (ys[keep], xs[keep]), (10 + 70 * rng.random(keep.sum()) ** 3).astype(np.float32))
neb = neb + blur(dust, 0.6, 2.0) * 1.6

vig = 1 - 0.40 * smooth(np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)), 0.72, 1.35)
neb *= vig
# a breath of grain, so the dark gradients do not band
neb += (rng.random((H, W), dtype=np.float32) - 0.5) * 1.4
save("space-cloud.webp", neb, quality=88)


# --- stars -------------------------------------------------------------------------------
def kernel(sigma, halo=0.0, spike=0.0):
    k = int(np.ceil(sigma * 3.2)) if not (halo or spike) else 30
    ax = np.arange(-k, k + 1, dtype=np.float32)
    dx, dy = ax[None, :], ax[:, None]
    d2 = dx ** 2 + dy ** 2
    kern = np.exp(-d2 / (2 * sigma * sigma))
    if halo:
        kern += halo * np.exp(-d2 / (2 * 7.0 ** 2)) + halo * 0.35 * np.exp(-np.sqrt(d2) / 9.0)
    if spike:   # the glint a lens gives the brightest stars: four thin rays
        ray = np.exp(-np.abs(dx) / 8.0) * np.exp(-dy ** 2 / (2 * 0.6 ** 2)) + np.exp(-np.abs(dy) / 8.0) * np.exp(-dx ** 2 / (2 * 0.6 ** 2))
        kern += spike * ray
    return np.clip(kern, 0, 1), k


def field(groups):
    """A T by T square of stars that repeats without a seam; gathered here, sparse there."""
    a = np.zeros((T, T), np.float32)
    dens = 0.25 + 0.75 * smooth(fbm(T, T, 520, 4, periodic=True), 0.32, 0.70)
    for count, sigma, lo, hi, power, halo, spike in groups:
        ys, xs = rng.integers(0, T, count * 3), rng.integers(0, T, count * 3)
        keep = rng.random(count * 3) < dens[ys, xs]
        ys, xs = ys[keep][:count], xs[keep][:count]
        v = lo + (hi - lo) * rng.random(len(ys)) ** power
        for y, x, b in zip(ys, xs, v):
            kern, k = kernel(sigma * (0.85 + 0.3 * rng.random()), halo, spike)
            iy = (np.arange(y - k, y + k + 1) % T)[:, None]
            ix = (np.arange(x - k, x + k + 1) % T)[None, :]
            a[iy, ix] = np.maximum(a[iy, ix], kern * b)
    return a


#               count sigma  lo   hi  power halo spike
far = field([(5200, 0.75, 22, 150, 3.0, 0, 0),
             (900, 1.00, 70, 220, 2.4, 0, 0)])
near = field([(420, 1.05, 60, 215, 2.6, 0, 0),
              (150, 1.45, 140, 255, 1.8, 0, 0),
              (26, 1.9, 225, 255, 1.0, 0.11, 0),
              (9, 2.2, 255, 255, 1.0, 0.16, 0.42)])
white = np.full((T, T), 255, np.float32)
save("space-stars-far.webp", white, far)
save("space-stars-near.webp", white, near)

# --- the three together, still -----------------------------------------------------------
def spread(a, size):
    """The square as the page shows it (`size` picture pixels to a side), over the picture."""
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)
    t = np.asarray(im, np.float32)
    return np.tile(t, (H // size + 1, W // size + 1))[:H, :W]


still = np.maximum(neb, np.maximum(spread(far, 1830), spread(near, 2500)))
save("space.webp", still, quality=84)
