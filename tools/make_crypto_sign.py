"""The picture for Crypto on the homepage: Bitcoin's sign with its walls built of a golden nebula
(owner, 28 Nov 2026: "only the sign, the B, with a golden nebula", "more real", "the walls built with the
nebula"). Generated, not a photograph: warped fractal noise for the gas, filaments and dust lanes, the sign as
a mass of that gas lit from the upper left, stars. Written with its own transparency (the light is the
alpha) so the homepage can add it over its sky.

    python3 tools/make_crypto_sign.py        writes assets/crypto-sign.webp
"""
import numpy as np, math, sys
from PIL import Image, ImageDraw, ImageFilter
S = 1600
rng = np.random.default_rng(7)
def fbm(base, octs, pers=0.5):
    out = np.zeros((S, S), np.float32); amp = 1; tot = 0; f = base
    for _ in range(octs):
        g = rng.random((f, f)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC)
        out += np.asarray(im, np.float32) / 255 * amp; tot += amp; amp *= pers; f *= 2
    return out / tot
def warp(a, wx, wy, k):
    yy, xx = np.mgrid[0:S, 0:S]
    x = np.clip(xx + (wx - 0.5) * k, 0, S - 1).astype(np.int32); y = np.clip(yy + (wy - 0.5) * k, 0, S - 1).astype(np.int32)
    return a[y, x]
def blur(a, r):
    return np.asarray(Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32) / 255
wx, wy = fbm(3, 5), fbm(3, 5)
n1 = warp(fbm(4, 8, 0.55), wx, wy, 520)
n2 = warp(fbm(6, 8, 0.6), wy, wx, 420)
n3 = warp(fbm(5, 7, 0.55), wx, wy, 300)
fil = np.clip(1 - np.abs(2 * n2 - 1) * 2.4, 0, 1) ** 1.6            # filaments
yy, xx = np.mgrid[0:S, 0:S]; u = (xx - S / 2) / (S / 2); v = (yy - S / 2) / (S / 2)
ang = 0.35; ur = u * math.cos(ang) + v * math.sin(ang); vr = -u * math.sin(ang) + v * math.cos(ang)
rad = np.sqrt((ur / 0.95) ** 2 + (vr / 0.72) ** 2) + (fbm(3, 4) - 0.5) * 0.7
env = np.clip(1 - rad, 0, 1) ** 1.25
edge = np.clip(1 - np.sqrt(u * u + v * v) / 0.98, 0, 1) ** 0.7        # nothing reaches the picture's edge
# the sign
m = Image.new("L", (S, S), 0); d = ImageDraw.Draw(m); K = S * 0.36; tilt = 0.24; ct, st = math.cos(tilt), math.sin(tilt)
def G(x, y): return (S / 2 + (x * ct + y * st) * K, S / 2 - (-x * st + y * ct) * K)
def bez(p0, p1, p2, p3, n=40): return [tuple((1 - t) ** 3 * p0[i] + 3 * (1 - t) ** 2 * t * p1[i] + 3 * (1 - t) * t * t * p2[i] + t ** 3 * p3[i] for i in (0, 1)) for t in np.linspace(0, 1, n)]
paths = [[(-0.3, 0.4), (0.06, 0.4)] + bez((0.06, 0.4), (0.36, 0.4), (0.36, 0.02), (0.06, 0.02)) + [(-0.18, 0.02)],
         [(0.06, 0.02), (0.1, 0.02)] + bez((0.1, 0.02), (0.44, 0.02), (0.44, -0.4), (0.1, -0.4)) + [(-0.3, -0.4)],
         [(-0.18, 0.4), (-0.18, -0.4)], [(-0.08, 0.4), (-0.08, 0.55)], [(0.08, 0.4), (0.08, 0.55)], [(-0.08, -0.4), (-0.08, -0.55)], [(0.08, -0.4), (0.08, -0.55)]]
W = int(K * 0.115)
for p in paths:
    pts = [G(*q) for q in p]; d.line(pts, fill=255, width=W, joint="curve")
    for q in (pts[0], pts[-1]): d.ellipse((q[0] - W / 2, q[1] - W / 2, q[0] + W / 2, q[1] + W / 2), fill=255)
B = np.asarray(m, np.float32) / 255
Bw = warp(B, n1, n3, 20)                                               # the walls' edges torn by the gas
n4 = warp(fbm(10, 7, 0.62), wx, n2, 260); fine = np.clip(1 - np.abs(2 * n4 - 1) * 2.0, 0, 1) ** 1.3
soft = blur(Bw, 3); mid = blur(Bw, 16); wide = blur(Bw, 50); far = blur(Bw, 130)
n5 = warp(fbm(24, 6, 0.65), n2, wx, 160); hair = np.clip(1 - np.abs(2 * n5 - 1) * 1.8, 0, 1) ** 1.5
rim = np.clip(blur(Bw, 2) - blur(Bw, 9), 0, 1) * 2.2                   # the walls' faces, lit like a front of gas
shade = np.clip(0.55 + (blur(np.roll(Bw, (-14, -10), (0, 1)), 14) - blur(Bw, 14)) * 2.2, 0.25, 1.2)   # light from the upper left
wall = soft * (0.14 + 0.6 * fine * (0.3 + n1) + 0.3 * fil * n2 + 0.45 * hair * n3) * (0.5 + 0.8 * n3) * shade + rim * (0.25 + 0.6 * hair) * (0.4 + n1)   # the walls: gas, thick in places and thin in others
gas = env * (0.85 * n1 ** 2.0 + 0.6 * fil * n1 + 0.35 * hair * n1 * n1) * 1.8
dust = np.clip((n3 - 0.48) * 4.2, 0, 1) ** 1.3 * np.clip(1 - mid * 2.0, 0.1, 1)
gas *= 1 - 0.8 * dust
I = (gas * (1 - 0.45 * wide) + far * 0.3 * (0.5 + n1) + wide * 0.22 * (0.5 + fil) + mid * 0.16 * (0.4 + fine) + wall * 0.95) * edge
hot = np.clip(wall - 0.8, 0, 1) * 0.3; core = hot
# colour: ember, orange, gold, white-hot
stops = np.array([[0, 0, 0], [52, 20, 5], [140, 70, 14], [222, 146, 44], [255, 208, 116], [255, 244, 220]], np.float32); pos = np.array([0, 0.12, 0.3, 0.55, 0.8, 1.0])
t = np.clip(I * 0.95, 0, 1) ** 0.85
rgb = np.stack([np.interp(t, pos, stops[:, i]) for i in range(3)], -1)
cool = (np.clip(n3 - 0.52, 0, 1) * 2.4 * env * (1 - mid))[..., None]   # a little rose where the gas thins
rgb = rgb * (1 - 0.35 * cool) + np.array([190, 60, 50], np.float32) * 0.4 * cool * t[..., None] * 2
haze = (env * np.clip(n2 - 0.55, 0, 1) * 2.2 * (1 - wide) * np.clip(1 - t * 1.6, 0, 1))[..., None]
rgb += haze * np.array([40, 78, 92], np.float32) * 0.7
rgb += hot[..., None] * np.array([255, 236, 196], np.float32)
# stars: more of them where the gas is thin, a few with a soft halo
st_img = np.zeros((S, S), np.float32); n = 4200
sx, sy = rng.integers(2, S - 2, n), rng.integers(2, S - 2, n); br = rng.random(n) ** 7
for x, y, b in zip(sx, sy, br):
    if edge[y, x] < 0.05: continue
    st_img[y, x] += 0.2 + b * 2.4
    if b > 0.25: st_img[y - 1:y + 2, x - 1:x + 2] += b * 0.5
st_img = st_img + blur(np.clip(st_img, 0, 1), 1.2) * 1.3 + blur(np.clip(st_img - 0.9, 0, 1), 5) * 5
knots = np.zeros((S, S), np.float32); ky, kx = np.nonzero((soft > 0.6) & (rng.random((S, S)) < 0.0016)); knots[ky, kx] = rng.random(len(ky)) ** 3 * 2.5
st_img += knots + blur(np.clip(knots, 0, 1), 1.5) * 2 + blur(np.clip(knots - 1.2, 0, 1), 6) * 6
rgb += (st_img * edge * (1 - 0.6 * np.clip(I, 0, 1)))[..., None] * np.array([255, 240, 225], np.float32)
big = np.zeros((S, S, 3), np.float32)
for _ in range(9):
    x, y = int(rng.integers(120, S - 120)), int(rng.integers(120, S - 120)); b = 0.5 + rng.random() * 0.5; c = np.array([[255, 236, 214], [214, 228, 255], [255, 214, 170]][int(rng.integers(0, 3))], np.float32)
    if soft[y, x] > 0.2 or edge[y, x] < 0.25: continue
    L = int(26 + 50 * b)
    for k in range(-L, L + 1):
        f = (1 - abs(k) / L) ** 2.4 * b
        big[y, x + k] += c * f; big[y + k, x] += c * f
    yy2, xx2 = np.mgrid[-12:13, -12:13]; big[y - 12:y + 13, x - 12:x + 13] += (np.exp(-(xx2 ** 2 + yy2 ** 2) / 9.0) * b * 2.2)[..., None] * c
rgb += big
grain = (rng.random((S, S, 1)).astype(np.float32) - 0.5) * 2 * np.clip(t, 0, 1)[..., None]
out = np.clip(rgb + grain, 0, 255).astype(np.uint8)
al = out.max(-1).astype(np.float32) / 255
al = np.clip((al - 3 / 255) / (1 - 3 / 255), 0, 1) ** 1.15
al = np.asarray(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255 * 0.5 + al * 0.5
straight = np.where(al[..., None] > 0, np.clip(out / np.maximum(al, 1 / 255)[..., None], 0, 255), 0).astype(np.uint8)
rgba = np.dstack([straight, (al * 255).astype(np.uint8)])
from pathlib import Path
Image.fromarray(rgba, "RGBA").resize((1000, 1000), Image.LANCZOS).save(Path(__file__).resolve().parent.parent / "assets" / "crypto-sign.webp", quality=72, alpha_quality=100, method=6)
