#!/usr/bin/env python3
"""Add a weekly review or research report to the Research Library.

    python3 tools/import_report.py report.pdf --type research --date 2026-10-30 \
        --title "..." --summary "..." --tags equities,rates --slug 2026-77-big-oil

Copies the PDF to data/reports/pdf/<slug>.pdf, as it is, and adds the report's
line to data/reports/index.json with its page count (pdfinfo, else pypdf). The
site lists the report and opens the PDF itself (see data/reports/README.md).
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


def page_count(path):
    if shutil.which("pdfinfo"):
        out = subprocess.run(["pdfinfo", str(path)], check=True, capture_output=True, text=True).stdout
        m = re.search(r"^Pages:\s+(\d+)", out, re.M)
        if m:
            return int(m.group(1))
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("Needs pdfinfo (poppler-utils) or the pypdf package.")
    return len(PdfReader(str(path)).pages)


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

    (REPORTS / "pdf").mkdir(exist_ok=True)
    shutil.copyfile(args.pdf, REPORTS / "pdf" / f"{slug}.pdf")
    index["reports"].append({"slug": slug, "date": args.date, "type": args.type, "title": args.title,
                             "summary": args.summary, "tags": tags, "pages": page_count(args.pdf)})
    index["reports"].sort(key=lambda r: (r["date"], r["slug"]), reverse=True)
    index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"copied the PDF to data/reports/pdf/{slug}.pdf and added it to data/reports/index.json")


if __name__ == "__main__":
    main()
