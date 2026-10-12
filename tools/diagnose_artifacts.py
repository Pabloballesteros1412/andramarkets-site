#!/usr/bin/env python3
"""Temporary diagnostic: chart figures the enrich step would add."""
import json, os, subprocess, sys

def notice(title, text):
    text = text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{text[:4000]}")

r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "import_notes.py"), "--dry-run"],
                   capture_output=True, text=True)
lines = (r.stdout + r.stderr).splitlines()
enr = {l.split()[1]: json.loads(l.split(" ", 2)[2]) for l in lines if l.startswith("ENRICH ")}
summary = [f"{d}: curve {len(c['curve'])} tenors, stale {sum(x['stale'] for x in c['curve'])}, "
           f"missing {sum(x['last'] is None for x in c['curve'])}, risk {c['risk']}, breadth {c['breadth']}"
           for d, c in sorted(enr.items())]
notice("enrich summary", "\n".join(summary))
for d in ("2026-10-09", "2026-10-01", "2026-09-18"):
    if d in enr:
        notice(f"charts {d}", json.dumps(enr[d]))
notice("other output", "\n".join(l for l in lines if not l.startswith(("ENRICH", "BACKFILL")) and "superseded" not in l)[-3500:])
