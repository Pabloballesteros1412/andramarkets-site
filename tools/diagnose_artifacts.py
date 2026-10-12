#!/usr/bin/env python3
"""Temporary diagnostic: per live note, the state of every charted field in its facts."""
import io, json, os, sys, zipfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
import import_notes as m

def notice(title, text):
    text = text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{text[:4000]}")

token = os.environ["AGENT_ARTIFACTS_TOKEN"]
by_id = {a["id"]: a for a in m.list_artifacts(token)}
lines, intl = [], []
for f in sorted(Path("data/notes").glob("*.json")):
    r = json.loads(f.read_text())
    a = by_id.get(r["source"]["artifact_id"])
    if not a:
        lines.append(f"{r['date']}: artifact expired"); continue
    _, files = m.unpack(m.download_zip(a, token))
    facts = json.loads(files["facts"])
    stale = set(facts.get("series_not_yet_published") or [])
    missing = set(facts.get("series_without_print") or [])
    absent, nul, st = [], [], []
    for chart, spec in m.BARS.items():
        for block, key, _ in spec:
            row = next((x for x in facts.get(block) or [] if isinstance(x, dict) and x.get("key") == key), None)
            if row is None:
                absent.append(f"{key}{'(no print at all)' if key in missing else ''}")
            elif m.number(row.get("last")) is None or m.number(row.get("chg")) is None:
                nul.append(key)
            elif key in stale:
                st.append(key)
    curve = len(facts.get("treasury_curve") or [])
    mv = facts.get("movers") or {}
    lines.append(f"{r['date']}: absent {absent or '-'}; null {nul or '-'}; no-print {len(st)}; curve {curve}; movers {len(mv.get('leaders') or [])}+{len(mv.get('laggards') or [])}; blocks missing {[b for b in ('sectors','credit','fx','commodities','volatility','digital','europe','apac','americas','treasury_curve','movers','risk_barometer','breadth') if b not in facts]}")
    if r["date"] in ("2026-09-01", "2026-09-14", "2026-10-09", "2026-09-24"):
        rows = [x for b in ("europe", "apac", "americas") for x in facts.get(b) or []]
        intl.append(r["date"] + " stale=" + ",".join(sorted(k for k in stale if any(x.get('key') == k for x in rows))) + " | " +
                    "; ".join(f"{x.get('key')} {x.get('last')} {x.get('chg')}" for x in rows))
buf, chunks = "", []
for ln in lines:
    if len(buf) + len(ln) > 3900: chunks.append(buf); buf = ""
    buf += ln + "\n"
chunks.append(buf)
for i, c in enumerate(chunks[:6]): notice(f"fields {i+1}/{len(chunks)}", c)
for i, c in enumerate(intl): notice(f"intl {i}", c)
