#!/usr/bin/env python3
"""Temporary diagnostic: spot-check control notes and a partial recovery."""
import io, json, os, re, sys, zipfile
sys.path.insert(0, os.path.dirname(__file__))
import import_notes as m
import pdf_note

def notice(title, text):
    text = text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{text[:4000]}")

token = os.environ["AGENT_ARTIFACTS_TOKEN"]
arts = {a["id"]: a for a in m.list_artifacts(token)}
def pdf_of(aid):
    z = zipfile.ZipFile(io.BytesIO(m.download_zip(arts[aid], token)))
    return z, z.read(next(n for n in z.namelist() if n.startswith("AndraMarkets_Close_")))

out = []
for aid in (11577608366, 10522208135, 9625377023):  # held for a control note
    z, pdf = pdf_of(aid)
    body = re.sub(r"\s+", " ", m.pdf_text(pdf))
    for mm in re.finditer(r"Control\s*note", body, re.I):
        out.append(f"{aid}: ...{body[max(0, mm.start()-160):mm.end()+200]}...")
    nj = next((n for n in z.namelist() if n.startswith("note_")), None)
notice("control notes", "\n\n".join(out) or "none found")

for aid in (9956689740, 9871461806):  # 4 Sep (short equities), 2 Sep newest (headline only)
    z, pdf = pdf_of(aid)
    got = pdf_note.extract(pdf)
    body = m.pdf_text(pdf)
    i = body.find("US EQUITIES")
    notice(f"partial {aid}", json.dumps({k: (v if isinstance(v, list) else v[:300]) for k, v in got.items()}, ensure_ascii=False)[:2000]
           + "\n---RAW near US EQUITIES---\n" + body[max(0, i-200):i+1500])
