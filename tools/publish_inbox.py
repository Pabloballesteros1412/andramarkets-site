#!/usr/bin/env python3
"""Publish every report PDF dropped in data/reports/inbox/ to the Research Library.

    python3 tools/publish_inbox.py            # move, index and commit (in CI, also push)
    python3 tools/publish_inbox.py --dry-run  # print what each PDF would become

Run by .github/workflows/publish-reports.yml on every push to the inbox. For
each PDF it reads the cover page of the standard Andra Markets layout: the
report number and date ("Report No. 2026-90 · Thursday, 5 November 2026"), the
title (the largest type on the page), the dek (the paragraph under the title,
cut to the 220-character summary) and the category line, which gives the topic
tags. A JSON file next to the PDF with the same name overrides any of type,
date, slug, title, summary and tags; a PDF whose cover cannot be read (the
slide-style covers) needs one, with at least date, slug and title.

The PDF moves to data/reports/pdf/<slug>.pdf as it is and its line goes into
index.json. A PDF identical to one already published is dropped; a new file
for a slug already in the index replaces that report. A PDF that cannot be
read stays in the inbox and the run fails, so GitHub emails the owner; the
others are still published.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_report import TAGS, TYPES, order, page_count  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "data" / "reports"
INBOX = REPORTS / "inbox"
MONTHS = "January February March April May June July August September October November December".split()
SUMMARY_MAX = 220

# Words in the category line or the kicker ("Credit · AI Infrastructure",
# "Thematic Research · Bonds and Gold") and the topic tag each one gives.
TOPIC_WORDS = [
    ("equities", r"equit|semiconductor|technolog|earnings|hyperscaler|internet|healthcare|pharma|"
                 r"beverage|consumer staples|financials|ai infrastructure|ipo|m&a|mergers"),
    ("rates", r"rates|federal reserve|central bank|monetary|bond|treasur|gilt|fed\b"),
    ("fx", r"\bfx\b|currenc|digital assets|crypto"),
    ("commodities", r"commodit|\boil\b|\bgas\b|energy|gold|metals|rare earth"),
    ("macro", r"macro|inflation|trade|politic|election|employment|housing|sanction|policy|united kingdom|japan|china"),
    ("credit", r"credit|sovereign debt|debt"),
]


def tidy(text):
    """One line, words rejoined across line-break hyphens ("Build- Out")."""
    return re.sub(r"(\w)- (\w)", r"\1-\2", " ".join(text.split()))


def cover_text(pdf):
    out = subprocess.run(["pdftotext", "-enc", "UTF-8", "-l", "1", str(pdf), "-"],
                         check=True, capture_output=True, text=True).stdout
    return out


def cover_title(pdf):
    """The largest type on the cover page."""
    from pypdf import PdfReader

    frags = []

    def visit(text, cm, tm, font, size):
        frags.append((round(size * abs(tm[0] or tm[3]) * abs(cm[0] or 1), 1), text))

    PdfReader(str(pdf)).pages[0].extract_text(visitor_text=visit)
    sized = [(s, t) for s, t in frags if t.strip()]
    if not sized:
        return ""
    big = max(s for s, _ in sized)
    return tidy(" ".join(t for s, t in sized if s == big))


def summarise(dek):
    """Whole sentences up to 220 characters, else the first sentence cut at a word."""
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9“\"$€£])", dek)
    out = ""
    for s in sentences:
        if len(out) + len(s) + (1 if out else 0) > SUMMARY_MAX:
            break
        out = f"{out} {s}" if out else s
    if not out:
        out = dek[:SUMMARY_MAX - 1].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return out


def slugify(number, title):
    head = title.split(":")[0]
    words = re.findall(r"[a-z0-9]+", head.lower().replace("’", "").replace("'", ""))[:6]
    return "-".join([number] + words)


def read_cover(pdf):
    """What the cover says: {date, number, title, summary, tags, type}, with None where unread."""
    flat = " ".join(cover_text(pdf).split())
    meta = {"date": None, "number": None, "title": None, "summary": None, "tags": [], "type": "research"}
    m = re.search(r"Report No\. (\d{4}-\d+) · \w+, (\d{1,2}) (%s) (\d{4})" % "|".join(MONTHS), flat)
    if m:
        meta["number"] = m.group(1)
        meta["date"] = dt.date(int(m.group(4)), MONTHS.index(m.group(3)) + 1, int(m.group(2))).isoformat()
    title = cover_title(pdf)
    if title and not re.search(r"\b\w \w \w \w\b", title):  # spaced-out slide titles ("A N T H R O P I C")
        meta["title"] = title
        # Find the title in the page text, letters only, so a hyphen or a line
        # break inside it ("Build-Out", "Build- Out", "BuildOut") still matches.
        words = re.findall(r"\w+", title)
        pattern = r"\b" + r"\W*".join(r"[-\s]*".join(map(re.escape, w)) for w in words) + r"\b"
        hit = re.search(pattern, flat)
        if not hit:  # a margin note printed inside the title: find its first and last words
            first = re.search(r"\b" + re.escape(words[0]) + r"\b", flat)
            if first:
                hit = re.compile(r"\b" + r"[-\s]*".join(map(re.escape, words[-1])) + r"\b").search(flat, first.end())
        if hit:
            dek = flat[hit.end():].split("Global Markets Research")[0]
            dek = re.sub(r"^[^A-Z]*?(?=[A-Z])", "", dek.lstrip(" .:")).strip()  # a margin note before the dek
            if len(dek) > 40:
                meta["summary"] = summarise(tidy(dek))
    head = flat.split("Report No.")[0] + " " + flat.split("Report No.")[-1][:200]
    meta["tags"] = [tag for tag, words in TOPIC_WORDS if re.search(words, head, re.I)]
    if re.search(r"weekly (market )?review", head, re.I):
        meta["type"] = "weekly"
    return meta


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan(pdf, index):
    """The index entry for one inbox PDF, or (None, reason)."""
    meta = read_cover(pdf)
    side = pdf.with_suffix(".json")
    if side.exists():
        meta.update(json.loads(side.read_text(encoding="utf-8")))
    slug = meta.get("slug") or (slugify(meta["number"], meta["title"]) if meta.get("number") and meta.get("title") else None)
    missing = [k for k in ("date", "title") if not meta.get(k)] + ([] if slug else ["slug"])
    if missing:
        return None, f"could not read {', '.join(missing)} from the cover; add {side.name} with them"
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        return None, f"slug {slug!r} takes lower case letters, digits and hyphens"
    if meta.get("type") not in TYPES:
        return None, f"type must be one of {', '.join(TYPES)}"
    tags = [t for t in meta.get("tags") or [] if t in TAGS]
    summary = meta.get("summary") or ""
    if len(summary) > SUMMARY_MAX:
        summary = summarise(summary)
    dt.date.fromisoformat(meta["date"])
    return {"slug": slug, "date": meta["date"], "type": meta["type"], "title": meta["title"],
            "summary": summary, "tags": tags, "pages": page_count(pdf)}, None


def git(*args):
    r = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    if r.returncode:
        raise SystemExit(f"git {args[0]} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def push_main(message):
    git("add", "-A", "data/reports")
    if not git("status", "--porcelain", "data/reports"):
        return False
    git("commit", "-m", message)
    for _ in range(4):
        if subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT).returncode == 0:
            return True
        git("pull", "--rebase", "origin", "main")  # main moved meanwhile: replay on top
    raise SystemExit("Could not push to main after 4 attempts.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="print what each PDF would become; change nothing")
    ap.add_argument("--push", action="store_true", help="commit and push to main (the workflow passes it)")
    args = ap.parse_args()

    pdfs = sorted(INBOX.glob("*.pdf")) + sorted(INBOX.glob("*.PDF"))
    if not pdfs:
        print("The inbox is empty.")
        return
    index_file = REPORTS / "index.json"
    index = json.loads(index_file.read_text(encoding="utf-8"))
    published = {sha(p): p.stem for p in (REPORTS / "pdf").glob("*.pdf")}
    done, failed, dropped = [], [], []
    for pdf in pdfs:
        side = pdf.with_suffix(".json")
        digest = sha(pdf)
        if digest in published:
            dropped.append(f"{pdf.name} (already published as {published[digest]})")
            if not args.dry_run:
                pdf.unlink()
                side.unlink(missing_ok=True)
            continue
        entry, error = plan(pdf, index)
        if error:
            failed.append(f"{pdf.name}: {error}")
            continue
        print(json.dumps(entry, ensure_ascii=False))
        if args.dry_run:
            continue
        shutil.move(str(pdf), REPORTS / "pdf" / f"{entry['slug']}.pdf")
        side.unlink(missing_ok=True)
        index["reports"] = [r for r in index["reports"] if r["slug"] != entry["slug"]] + [entry]
        published[digest] = entry["slug"]
        done.append(entry)
    for line in dropped:
        print(f"dropped {line}")
    if done:
        index["reports"].sort(key=order, reverse=True)
        index_file.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.push and (done or dropped):
        names = ", ".join(r["slug"] for r in done) or "duplicates"
        message = f"Research Library: publish {names}" if done else "Research Library: clear duplicate PDFs from the inbox"
        push_main(message)
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as out:
            out.write(f"published={'true' if done else 'false'}\n")
    for line in failed:
        print(f"::error::{line}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
