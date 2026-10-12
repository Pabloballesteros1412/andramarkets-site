#!/usr/bin/env python3
"""Temporary diagnostic: validate PDF recovery, then dry-run the importer."""
import collections, io, json, os, re, subprocess, sys, zipfile
sys.path.insert(0, os.path.dirname(__file__))
import import_notes as m
import pdf_note

def notice(title, text):
    text = text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{text[:4000]}")

def norm(v):
    return [norm(x) for x in v] if isinstance(v, list) else re.sub(r"\s+", " ", (v or "")).strip()

token = os.environ["AGENT_ARTIFACTS_TOKEN"]
stats, diffs, old = collections.Counter(), [], []
for a in m.list_artifacts(token):
    z = zipfile.ZipFile(io.BytesIO(m.download_zip(a, token)))
    names = z.namelist()
    got = pdf_note.extract(z.read(next(n for n in names if n.startswith("AndraMarkets_Close_"))))
    nj = next((n for n in names if n.startswith("note_")), None)
    if not nj:
        old.append(f"{a['created_at'][:16]} {sum(1 for v in got.values() if v)}/14 | {got.get('headline', '')[:60]}")
        continue
    truth = json.loads(z.read(nj))
    for f in m.NOTE_FIELDS:
        t, g = truth.get(f) or "", got.get(f) or ""
        if norm(t) == norm(g) and (f in m.LIST_FIELDS or [norm(x) for x in re.split(r"\n\s*\n", t)] == [norm(x) for x in re.split(r"\n\s*\n", g)]):
            stats["exact"] += 1
        else:
            stats["different"] += 1
            diffs.append(f"{a['id']} {f}")
notice("validation", f"{stats['exact']} fields exact, {stats['different']} different, over {stats['exact'] + stats['different']} fields\n" + "\n".join(diffs[:20]))
notice("old recoveries", "\n".join(old))

r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "import_notes.py"), "--dry-run"],
                   capture_output=True, text=True)
out = (r.stdout + r.stderr).replace("::error::", "ERROR ")
out = out.replace("Recovered from the PDF: the agent saved no note text for this run, so the text was read back from the report. Check it before merging.", "[RECOVERED]")
out = out.replace("The figure check failed: the PDF carries a Control note.", "[CONTROL]")
out = out.replace(" The agent's reply was probably truncated.", "")
lines = [l for l in out.splitlines() if "superseded" not in l]
notice("dry run", f"({sum('superseded' in l for l in out.splitlines())} superseded lines hidden)\n" + "\n".join(lines))
