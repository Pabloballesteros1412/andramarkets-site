#!/usr/bin/env python3
"""Temporary diagnostic: font map of a pre-22-August report PDF."""
import io, os, sys, zipfile
sys.path.insert(0, os.path.dirname(__file__))
import import_notes as m
import pdf_note

def notice(title, text):
    text = text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{text[:4000]}")

token = os.environ["AGENT_ARTIFACTS_TOKEN"]
arts = {a["id"]: a for a in m.list_artifacts(token)}
z = zipfile.ZipFile(io.BytesIO(m.download_zip(arts[9464378710], token)))
pdf = z.read(next(n for n in z.namelist() if n.startswith("AndraMarkets_Close_")))
merged = []
for r in pdf_note.runs(pdf):
    if merged and merged[-1][:2] == r[:2]:
        merged[-1] = (r[0], r[1], r[2], merged[-1][3] + " " + r[3])
    else:
        merged.append(r)
lines = [f"p{p} {s} | {' '.join(t.split())[:60]}" for p, s, y, t in merged]
buf, out = "", []
for ln in lines:
    if len(buf) + len(ln) > 3900:
        out.append(buf); buf = ""
    buf += ln + "\n"
out.append(buf)
for i, c in enumerate(out[:9]):
    notice(f"old runs {i+1}/{len(out)}", c)
