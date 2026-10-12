#!/usr/bin/env python3
"""Temporary diagnostic: report what the agent's artifacts really contain.

Reports through workflow annotations. Reads only; writes nothing.
"""
import collections, io, json, os, re, sys, zipfile
sys.path.insert(0, os.path.dirname(__file__))
import import_notes as m

def notice(title, text):
    text = text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{text[:60000]}")

token = os.environ["AGENT_ARTIFACTS_TOKEN"]
arts = m.list_artifacts(token)
sigs, lines = collections.Counter(), []
samples = {}
for a in arts:
    blob = m.download_zip(a, token)
    z = zipfile.ZipFile(io.BytesIO(blob))
    names = sorted(i.filename for i in z.infolist() if not i.is_dir())
    pat = sorted({re.sub(r"\d{8}", "YYYYMMDD", re.sub(r"_\d+\.png$", "_N.png", n)) for n in names})
    sigs[tuple(pat)] += 1
    lines.append(f"{a['created_at'][:16]} {a['id']}: " + ", ".join(f"{n} ({z.getinfo(n).file_size})" for n in names if "/" not in n) + f" + {sum('/' in n for n in names)} in subfolders")
    key = "old" if not any(n.startswith("note_") for n in names) else "new"
    if key not in samples or (key == "new"):
        samples[key] = (a, z, names)
notice("signatures", "\n".join(f"{c} artifacts: {list(p)}" for p, c in sigs.items()))
notice("listing 1", "\n".join(lines[:35]))
notice("listing 2", "\n".join(lines[35:]))
for key, (a, z, names) in samples.items():
    pdf = next(n for n in names if n.startswith("AndraMarkets_Close_"))
    text = m.pdf_text(z.read(pdf))
    notice(f"pdf text {key} {a['id']}", text[:30000])
    if key == "new":
        nj = next(n for n in names if n.startswith("note_"))
        notice(f"note json {a['id']}", z.read(nj).decode()[:20000])
