#!/usr/bin/env python3
"""Temporary diagnostic: check PDF text recovery against the real note JSON."""
import collections, io, json, os, re, sys, zipfile
sys.path.insert(0, os.path.dirname(__file__))
import import_notes as m
import pdf_note

def notice(title, text):
    text = text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{text[:4000]}")

def norm(v):
    if isinstance(v, list):
        return [norm(x) for x in v]
    return re.sub(r"\s+", " ", (v or "")).strip()

token = os.environ["AGENT_ARTIFACTS_TOKEN"]
stats, diffs, old = collections.Counter(), [], []
for a in m.list_artifacts(token):
    z = zipfile.ZipFile(io.BytesIO(m.download_zip(a, token)))
    names = [i.filename for i in z.infolist()]
    pdf = z.read(next(n for n in names if n.startswith("AndraMarkets_Close_")))
    got = pdf_note.extract(pdf)
    nj = next((n for n in names if n.startswith("note_")), None)
    if not nj:
        old.append(f"{a['id']} {a['created_at'][:10]}: " + ", ".join(f"{k}:{len(v) if isinstance(v, list) else len(v.split())}" for k, v in got.items()) + f" | {got.get('headline','')[:70]}")
        continue
    truth = json.loads(z.read(nj))
    for f in m.NOTE_FIELDS:
        t = truth.get(f) or ([] if f in m.LIST_FIELDS else "")
        g = got.get(f) or ([] if f in m.LIST_FIELDS else "")
        if norm(t) == norm(g):
            stats[f + " ok"] += 1
            if f not in m.LIST_FIELDS and t and [p.strip() for p in re.split(r"\n\s*\n", t)] != [norm(p) for p in g.split("\n\n")]:
                stats[f + " paragraph-split differs"] += 1
        else:
            stats[f + " BAD"] += 1
            if len(diffs) < 12:
                a_, b_ = json.dumps(norm(t))[:300], json.dumps(norm(g))[:300]
                i = next((k for k in range(min(len(a_), len(b_))) if a_[k] != b_[k]), 0)
                diffs.append(f"{a['id']} {f}: truth[{i}:]={a_[max(0,i-30):i+60]!r} got={b_[max(0,i-30):i+60]!r}")
notice("stats", "\n".join(f"{k}: {v}" for k, v in sorted(stats.items())))
notice("diffs", "\n".join(diffs) or "none")
notice("old 1", "\n".join(old[:22]))
notice("old 2", "\n".join(old[22:]))
