#!/usr/bin/env python3
"""Temporary diagnostic: dry-run the importer and show the backfill table."""
import os, subprocess, sys

def notice(title, text):
    text = text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{text[:4000]}")

r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "import_notes.py"), "--dry-run"],
                   capture_output=True, text=True)
lines = (r.stdout + r.stderr).splitlines()
notice("summary", "\n".join(l for l in lines if l.startswith(("DRY", "ERROR", "Traceback", "  ")) or "withdrawn" in l or "published" in l and "BACKFILL" not in l))
back = [l for l in lines if l.startswith("BACKFILL")]
notice("backfill 1", "\n".join(back[:20]))
notice("backfill 2", "\n".join(back[20:]))
