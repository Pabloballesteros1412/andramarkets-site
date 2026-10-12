"""Recover the note text from the agent's report PDF.

Before 15 September 2026 the agent saved no note_YYYYMMDD.json, so for those
runs the text exists only inside AndraMarkets_Close_YYYYMMDD.pdf. The report
template sets each kind of text at its own size, which is what this relies on:

    headline                 ~19 pt, top of page one
    standfirst               ~9 pt, straight after the headline
    section number / title   6.2 pt / 8.3 pt ("3.0", "US EQUITIES")
    prose and takeaways      8.0 pt
    "What we are watching"   7.2 pt items, numbered at 6.2 pt

Tables, exhibits, the methodology and the disclaimer use other sizes and are
ignored. tools/import_notes.py holds every recovered note for review.
"""
import io
import math
import re
from statistics import median

PROSE, WATCH, NUMBER, TITLE = 8.0, 7.2, 6.2, 8.3

# Section title (8.3 pt) -> note field(s), in the order their prose blocks appear.
SECTIONS = {
    "KEY TAKEAWAYS": ("takeaways",),
    "US EQUITIES": ("equities",),
    "INTERNATIONAL EQUITIES": ("international",),
    "RATES": ("rates",),
    "CREDIT": ("credit",),
    "FOREIGN EXCHANGE": ("fx",),
    "COMMODITIES": ("commodities",),
    "CROSS-ASSET CORRELATION": ("correlation",),
    "VOLATILITY AND DIGITAL ASSETS": ("volatility", "digital"),
    "DESK VIEW": ("desk_view",),
}


def runs(pdf):
    """Every text run as (page, size, y, text), in drawing order."""
    from pypdf import PdfReader
    out = []
    for pno, page in enumerate(PdfReader(io.BytesIO(pdf)).pages):
        def visit(text, cm, tm, font, size, pno=pno):
            if not text.strip():
                return
            scale = math.hypot(tm[0], tm[1]) * math.hypot(cm[0], cm[1])
            y = cm[1] * tm[4] + cm[3] * tm[5] + cm[5]
            out.append((pno, round(size * scale, 1), y, text))
        page.extract_text(visitor_text=visit)
    return out


def _is(size, target):
    return abs(size - target) < 0.15


def _join(parts):
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def _paragraphs(lines):
    """Join 8 pt lines into paragraphs, breaking where the line gap widens."""
    gaps = [a[2] - b[2] for a, b in zip(lines, lines[1:]) if a[0] == b[0] and a[2] > b[2]]
    step = median(gaps) if gaps else 0
    paras, cur = [], []
    for i, (page, size, y, text) in enumerate(lines):
        if cur and step:
            prev = lines[i - 1]
            if prev[0] == page and prev[2] - y > step * 1.4:
                paras.append(_join(cur))
                cur = []
        cur.append(text)
    if cur:
        paras.append(_join(cur))
    return "\n\n".join(p for p in paras if p)


def extract(pdf):
    """Return the note fields found in the PDF (missing fields are left out)."""
    rs = [r for r in runs(pdf) if not re.search(r"GLOBAL MARKETS RESEARCH\s+US CLOSE", r[3])]
    note = {}

    # Headline and standfirst: the large runs at the top of page one.
    first_section = next((i for i, r in enumerate(rs) if _is(r[1], NUMBER) and re.fullmatch(r"\s*1\.0\s*", r[3])), len(rs))
    top = rs[:first_section]
    head = [i for i, r in enumerate(top) if r[1] >= 15]
    if head:
        note["headline"] = _join(top[i][3] for i in head)
        after = [r for r in top[head[-1] + 1:]]
        stand = []
        for r in after:
            if 8.6 <= r[1] <= 10.5:
                stand.append(r[3])
            elif stand:
                break
        if stand:
            note["standfirst"] = _join(stand)

    # Sections: prose blocks are runs of consecutive 8 pt lines.
    section, blocks = None, {}
    watching, in_watch = [], False
    for r in rs:
        page, size, y, text = r
        if _is(size, TITLE):
            # The watch list is drawn last, after the methodology title, so a
            # new title ends a prose section but never the watch list.
            section = text.strip().upper() if text.strip().upper() in SECTIONS else None
            if section:
                blocks.setdefault(section, [[]])
                in_watch = False
            continue
        if _is(size, NUMBER) and "WHAT WE ARE WATCHING" in text.upper():
            in_watch, section = True, None
            watching.append([])
            continue
        if in_watch:
            if _is(size, WATCH):
                watching[-1].append(text)
            elif _is(size, NUMBER) and re.fullmatch(r"\s*\d+\s*", text):
                watching.append([])
            continue
        if section is None:
            continue
        if _is(size, PROSE):
            blocks[section][-1].append(r)
        elif section == "KEY TAKEAWAYS" and _is(size, NUMBER) and re.fullmatch(r"\s*\d+\s*", text):
            blocks[section].append([])  # each number closes one takeaway
        elif blocks[section][-1]:
            blocks[section].append([])

    for title, fields in SECTIONS.items():
        found = [b for b in blocks.get(title, []) if b]
        if not found:
            continue
        if title == "KEY TAKEAWAYS":
            note["takeaways"] = [_join(t for *_, t in b) for b in found]
        elif len(fields) == 1:
            note[fields[0]] = "\n\n".join(_paragraphs(b) for b in found)
        else:
            for field, b in zip(fields, found):
                note[field] = _paragraphs(b)
    items = [_join(w) for w in watching if w]
    if items:
        note["watching"] = items
    return note
