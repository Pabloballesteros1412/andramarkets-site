#!/usr/bin/env python3
"""Temporary diagnostic: margin chart figures the enrich step would add."""
import json, os, subprocess, sys

def notice(title, text):
    text = text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{text[:4000]}")

r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "import_notes.py"), "--dry-run"],
                   capture_output=True, text=True)
lines = (r.stdout + r.stderr).splitlines()
enr = {l.split()[1]: json.loads(l.split(" ", 2)[2]) for l in lines if l.startswith("ENRICH ")}
notice("summary", "\n".join(f"{d}: " + ", ".join(f"{k} {len(v['rows'])}/{v['left_out']}" for k, v in c["bars"].items())
                          + f", movers {len(c['movers']['leaders'])}+{len(c['movers']['laggards'])}" for d, c in sorted(enr.items())))
for d in ("2026-10-09",):
    c = dict(enr[d]); c.pop("curve", None)
    blob = json.dumps(c)
    for i in range(0, len(blob), 3800):
        notice(f"charts {d} {i // 3800}", blob[i:i + 3800])
notice("tail", "\n".join(l for l in lines if l.startswith(("ERROR", "::", "Traceback", "  File", "DRY")))[-3000:])
