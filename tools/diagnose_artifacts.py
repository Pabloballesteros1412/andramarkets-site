#!/usr/bin/env python3
"""Temporary diagnostic: dry-run the importer against the real artifacts."""
import os, subprocess, sys

def notice(title, text):
    text = text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{text[:4000]}")

r = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "import_notes.py"), "--dry-run"],
                   capture_output=True, text=True)
out = (r.stdout + r.stderr).replace("::error::", "ERROR ")
out = out.replace("Recovered from the PDF: the agent saved no note text for this run, so the text was read back from the report. Check it before merging.", "[RECOVERED]")
out = out.replace("The figure check failed: the PDF carries a Control note.", "[CONTROL]")
chunks, buf = [], ""
for ln in out.splitlines():
    if len(buf) + len(ln) > 3900:
        chunks.append(buf); buf = ""
    buf += ln + "\n"
chunks.append(buf)
for i, c in enumerate(chunks[:8]):
    notice(f"dry run {i+1}/{len(chunks)}", c)
