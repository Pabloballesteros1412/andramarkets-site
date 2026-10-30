#!/usr/bin/env python3
"""Add a weekly review or research report to the Research Library.

    python3 tools/import_report.py report.pdf --type weekly --date 2026-10-30 \
        --title "..." --summary "..." --tags equities,rates

Reads the PDF's text (pdftotext, else pypdf), writes data/reports/<slug>.md in
the small Markdown the site reads (see data/reports/README.md) and adds the
report's line to data/reports/index.json. The PDF itself is never copied into
the repo: it is public, and PDFs are reserved for subscribers.

A guess is only a guess: short lines without a full stop become headings and
bullet characters become list items. Read the Markdown once before committing;
tables and charts do not survive the conversion.
"""
import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "data" / "reports"
TYPES = ("weekly", "research")
TAGS = ("equities", "rates", "fx", "commodities", "macro", "credit")
BULLETS = "•●▪◦–-*"


def pdf_text(path):
    if shutil.which("pdftotext"):
        out = subprocess.run(["pdftotext", "-enc", "UTF-8", str(path), "-"],
                             check=True, capture_output=True, text=True)
        return out.stdout
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("Needs pdftotext (poppler-utils) or the pypdf package.")
    return "\n\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)


def is_heading(line):
    return (len(line) <= 70 and not line.endswith((".", ",", ";", ":")) and len(line.split()) <= 9
            and line[0].isupper() and not re.fullmatch(r"[\d\s.,%$€£()+−-]+", line))


def to_markdown(text):
    blocks, para = [], []

    def flush():
        if para:
            blocks.append(" ".join(para))
            para.clear()

    for raw in text.replace("\f", "\n\n").splitlines():
        line = " ".join(raw.split())
        if not line or re.fullmatch(r"(page\s*)?\d+(\s*(/|of)\s*\d+)?", line, re.I):
            flush()
            continue
        if line[0] in BULLETS and len(line) > 2 and line[1] == " ":
            flush()
            blocks.append("- " + line[2:])
        elif not para and is_heading(line):
            blocks.append("## " + (line.title() if line.isupper() else line))
        else:
            para.append(line)
    flush()
    # Consecutive list items stay together; everything else is a block.
    md = []
    for b in blocks:
        if md and b.startswith("- ") and md[-1].startswith("- "):
            md[-1] += "\n" + b
        else:
            md.append(b)
    return "\n\n".join(md).strip() + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--type", required=True, choices=TYPES)
    ap.add_argument("--date", required=True, help="publication date, YYYY-MM-DD")
    ap.add_argument("--title", required=True)
    ap.add_argument("--summary", required=True, help="one or two sentences, up to 220 characters")
    ap.add_argument("--tags", required=True, help="comma separated: " + ", ".join(TAGS))
    ap.add_argument("--slug", help="default: <type>-<date>")
    args = ap.parse_args()

    dt.date.fromisoformat(args.date)
    tags = [t.strip().lower() for t in args.tags.split(",") if t.strip()]
    bad = [t for t in tags if t not in TAGS]
    if bad:
        sys.exit(f"Unknown tags {bad}; use {', '.join(TAGS)}.")
    if len(args.summary) > 220:
        sys.exit(f"The summary is {len(args.summary)} characters; keep it to 220.")
    slug = args.slug or f"{args.type}-{args.date}"
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", slug):
        sys.exit("The slug takes lower case letters, digits and hyphens, and cannot be a bare date.")

    index_file = REPORTS / "index.json"
    index = json.loads(index_file.read_text(encoding="utf-8"))
    if any(r["slug"] == slug for r in index["reports"]):
        sys.exit(f"{slug} is already in the index; pass --slug to choose another.")

    (REPORTS / f"{slug}.md").write_text(to_markdown(pdf_text(args.pdf)), encoding="utf-8")
    index["reports"].append({"slug": slug, "date": args.date, "type": args.type, "title": args.title,
                             "summary": args.summary, "tags": tags})
    index["reports"].sort(key=lambda r: r["date"], reverse=True)
    index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote data/reports/{slug}.md and added it to data/reports/index.json; read it before committing")


if __name__ == "__main__":
    main()
