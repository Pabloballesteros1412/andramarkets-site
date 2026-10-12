#!/usr/bin/env python3
"""Temporary diagnostic: font-size map of one new-format report PDF."""
import io, os, sys, zipfile, math
sys.path.insert(0, os.path.dirname(__file__))
import import_notes as m
from pypdf import PdfReader

def notice(title, text):
    text = text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{text}")

token = os.environ["AGENT_ARTIFACTS_TOKEN"]
arts = {a["id"]: a for a in m.list_artifacts(token)}
z = zipfile.ZipFile(io.BytesIO(m.download_zip(arts[11645604264], token)))
pdf = PdfReader(io.BytesIO(z.read("AndraMarkets_Close_20261009.pdf")))
runs = []
for pno, page in enumerate(pdf.pages):
    def visit(text, cm, tm, font, size, pno=pno):
        if not text.strip():
            return
        scale = math.hypot(tm[0], tm[1]) * math.hypot(cm[0], cm[1])
        name = (font or {}).get("/BaseFont", "?") if font else "?"
        runs.append((pno, round(size * scale, 1), str(name)[-14:], text.replace("\n", " ")))
    page.extract_text(visitor_text=visit)
merged = []
for r in runs:
    if merged and merged[-1][:3] == r[:3]:
        merged[-1] = (*r[:3], merged[-1][3] + " " + r[3])
    else:
        merged.append(r)
lines = [f"p{p} {s} {f} | {t[:70]}" for p, s, f, t in merged]
buf, out = "", []
for ln in lines:
    if len(buf) + len(ln) > 3900:
        out.append(buf); buf = ""
    buf += ln + "\n"
out.append(buf)
for i, chunk in enumerate(out[:9]):
    notice(f"runs {i+1}/{len(out)}", chunk)
