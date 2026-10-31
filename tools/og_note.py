#!/usr/bin/env python3
"""The share image of each close note (owner-approved, 31 Oct 2026): 1200x630, the
approved social image's ground and horse (andra-horse.png, whole and untouched,
screen-blended at 0.62 on #0a0c0d with the radial vignette), the transparent dark
mark and "Andra Markets", the note's date, its headline and four daily changes,
signed and coloured as rises and falls (DESIGN.md, The Rise and Fall Rule).

tools/build_site.py writes one per note to reports/<date>/og.jpg. It needs Pillow
(the deploy installs it); without it the build keeps assets/og-image.png.

    python3 tools/og_note.py 2026-10-30 out.jpg    one note, for a look
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, features

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "assets" / "fonts" / "schibsted-grotesk-latin.woff2"
W, H = 1200, 630
GROUND = (10, 12, 13)
INK, INK2 = (233, 236, 235), (168, 176, 180)
RULE = (36, 39, 40)  # rgba(233, 236, 235, 0.13) on the ground
UP, DOWN = (31, 210, 122), (255, 75, 82)
MINUS = "−"
# (label, key): the first four with a figure are shown
FIGS = (("S&P 500", "spx"), ("Nasdaq 100", "ndx"), ("VIX", "vix"), ("Gold", "gold"),
        ("Euro Stoxx 50", "sx5e"), ("WTI crude", "wti"))
TNUM = ["tnum"] if features.check("raqm") else None

_base = None


def font(size, weight):
    f = ImageFont.truetype(str(FONT), size)
    f.set_variation_by_axes([weight])
    return f


def base():
    """The ground, the horse and the vignette, as in assets/og-image.png."""
    global _base
    if _base is None:
        img = Image.new("RGB", (W, H), GROUND)
        horse = Image.open(ROOT / "andra-horse.png").convert("RGB")
        layer = Image.new("RGB", (W, H), (0, 0, 0))
        layer.paste(horse.crop((0, 215, 780, 1024)), (420, 0))  # the black ground only is cut, never the horse
        screened = ImageChops.screen(img, layer)
        img = Image.blend(img, screened, 0.62)
        # radial vignette: clear in the middle right, the ground at 0.75 at the edges
        g = Image.radial_gradient("L").resize((int(W * 1.8), int(H * 2)))
        mask = Image.new("L", (W, H), 0)
        mask.paste(g, (int(W * 0.7 - g.width / 2), int(H * 0.5 - g.height / 2)))
        mask = mask.point(lambda v: 0 if v < 115 else min(191, int((v - 115) / (255 - 115) * 191)))
        img = Image.composite(Image.new("RGB", (W, H), GROUND), img, mask)
        mark = Image.open(ROOT / "assets" / "andra-mark-dark.png").convert("RGBA")
        mark = mark.resize((round(mark.width * 34 / mark.height), 34), Image.LANCZOS)
        img.paste(mark, (72, 64), mark)
        ImageDraw.Draw(img).text((72 + mark.width + 10, 81), "Andra Markets", font=font(26, 650), fill=INK, anchor="lm")
        _base = img
    return _base.copy()


def tracked(draw, text, f, track):
    """Width of text set with tracking (CSS letter-spacing), kerning kept."""
    return draw.textlength(text, font=f) + track * max(0, len(text) - 1)


def draw_tracked(draw, xy, text, f, track, fill):
    x, y = xy
    for i, ch in enumerate(text):
        if ch != " ":
            draw.text((x + draw.textlength(text[:i], font=f) + track * i, y), ch, font=f, fill=fill, anchor="ls")


def wrap(draw, text, f, width, track=0):
    """Lines no wider than width, as even as the words allow (text-wrap: balance)."""
    words = text.split()

    def greedy(w):
        lines, cur = [], ""
        for word in words:
            t = f"{cur} {word}".strip()
            if cur and tracked(draw, t, f, track) > w:
                lines.append(cur)
                cur = word
            else:
                cur = t
        return lines + [cur]

    best = greedy(width)
    w = width
    while w > width * 0.5:
        w -= 10
        trial = greedy(w)
        if len(trial) > len(best):
            break
        best = trial
    return best


def render(rec, out):
    img = base()
    draw = ImageDraw.Draw(img)
    d = rec["date"]
    import datetime as dt
    day = dt.date.fromisoformat(d)
    draw.text((72, 155), f"Close note, {day:%A} {day.day} {day:%b %Y}", font=font(22, 400), fill=INK2, anchor="lm")
    head = rec["note"]["headline"]
    for size in (54, 48, 42, 38):
        f = font(size, 560)
        track = -0.035 * size
        lines = wrap(draw, head, f, 700, track)
        if len(lines) <= 3:
            break
    lines = lines[:4]
    y = 190 + round(size * 0.82)
    for line in lines:
        draw_tracked(draw, (72, y), line, f, track, INK)
        y += round(size * 1.04)
    # four daily changes, ruled like the tape
    closes = rec.get("closes") or {}
    figs = []
    for label, key in FIGS:
        row = closes.get(key) or {}
        chg = row.get("chg")
        if row.get("stale") or not isinstance(chg, (int, float)):
            continue
        r = round(chg, 2)
        figs.append((label, f"{'+' if r > 0 else MINUS if r < 0 else ''}{abs(r):.2f}%", UP if r > 0 else DOWN if r < 0 else INK))
        if len(figs) == 4:
            break
    if figs:
        top = 494
        fn, fc = font(19, 400), font(30, 520)
        x = 72
        xs = []
        for i, (label, text, col) in enumerate(figs):
            if i:
                x += 24
            xs.append(x)
            wdt = max(draw.textlength(label, font=fn), draw.textlength(text, font=fc, features=TNUM))
            x += wdt + 32
        draw.line((72, top, max(x - 32, 700), top), fill=RULE, width=1)
        for i, ((label, text, col), x0) in enumerate(zip(figs, xs)):
            if i:
                draw.line((x0 - 24, top, x0 - 24, top + 80), fill=RULE, width=1)
            draw.text((x0, top + 18), label, font=fn, fill=INK2, anchor="la")
            draw.text((x0, top + 44), text, font=fc, fill=col, anchor="la", features=TNUM)
    img.save(out, "JPEG", quality=90, subsampling=0)


if __name__ == "__main__":
    rec = json.loads((ROOT / "data" / "notes" / f"{sys.argv[1]}.json").read_text(encoding="utf-8"))
    render(rec, sys.argv[2])
