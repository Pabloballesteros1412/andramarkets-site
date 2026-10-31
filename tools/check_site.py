#!/usr/bin/env python3
"""Check the built site before it is published.

Run after tools/build_site.py. It fails (exit 1) when a page that must carry
content came out without it, so a broken build never replaces the live site:
the last good deploy stays up and GitHub emails the owner about the failed run.

Checks:
- every published close note has its page, and every section the note has
  text for (takeaways, desk view, what we watch, equities, ...) is on it;
- the homepage index lists every section of the inner pages' menu;
- with SITE_URL set: sitemap.xml lists the homepage and every published close
  note and no redirect, robots.txt points to it, feed.xml is valid RSS with
  the newest note; with SITE_URL unset, none of the three exists.

    python3 tools/check_site.py
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_site as site  # noqa: E402  (the same lists the build uses)

ROOT = site.ROOT


# Sections every full note carries. Listed here, not read from the build, so the check
# still holds if the build's own list is lost (as on 31 Oct 2026, when another list of
# the same name replaced it and every note page shipped without its body).
CORE = ("takeaways", "desk_view", "watching")
NOT_SECTIONS = ("headline", "standfirst")


def check_notes():
    problems, warnings = [], []
    known = set(CORE) | {f for f, _ in site.SECTIONS if re.fullmatch(r"[a-z_]+", f)}
    notes = site.load_notes()
    for rec in notes:
        page = site.REPORTS / rec["date"] / "index.html"
        if not page.exists():
            problems.append(f"reports/{rec['date']}/: page missing")
            continue
        html = page.read_text(encoding="utf-8")
        for field, value in (rec.get("note") or {}).items():
            if field in NOT_SECTIONS or not value:
                continue
            if f'id="s-{field.replace("_", "-")}"' in html:
                continue
            msg = f"reports/{rec['date']}/: the note's {field} is not on the page"
            # a field the site has never shown (new in the agent's output) only warns
            (problems if field in known else warnings).append(msg)
    return len(notes), problems, warnings


def nav_links(html, pattern):
    m = re.search(pattern, html, re.S)
    # page links only: the menu's icons are <use href="#i-..."> too
    return re.findall(r'<a [^>]*href="(?:\.\./)*([^"]*)"', m.group(1)) if m else []


def check_home():
    """The homepage index is the homepage's only menu: it must list every section the
    inner pages' menu lists."""
    home = nav_links((ROOT / "index.html").read_text(encoding="utf-8"),
                     r'<nav class="hero__index"[^>]*>(.*?)</nav>')
    menu = nav_links((site.REPORTS / "index.html").read_text(encoding="utf-8"),
                     r'<nav class="nav"[^>]*>(.*?)</nav>')
    if not home:
        return ["index.html: the section index is empty"]
    missing = [h for h in menu if h not in home]
    return [f"index.html: the section index lacks {', '.join(missing)}"] if missing else []


def check_discovery():
    """The sitemap, robots.txt and feed: complete with SITE_URL, absent without it."""
    files = {name: ROOT / name for name in site.DISCOVERY}
    if not site.SITE_URL:
        return [f"{name}: written without SITE_URL" for name, f in files.items() if f.exists()]
    missing = [name for name, f in files.items() if not f.exists()]
    if missing:
        return [f"{name}: missing" for name in missing]
    problems = []
    try:
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = {e.text for e in ET.parse(files["sitemap.xml"]).getroot().findall("s:url/s:loc", ns)}
        feed = ET.parse(files["feed.xml"]).getroot()
    except ET.ParseError as e:
        return [f"sitemap.xml or feed.xml: not valid XML ({e})"]
    notes = site.load_notes()
    wanted = [site.abs_url()] + [site.abs_url(f"reports/{r['date']}/") for r in notes]
    problems += [f"sitemap.xml: lacks {u}" for u in wanted if u not in locs]
    for loc in locs:
        page = ROOT / loc[len(site.SITE_URL) + 1:] / "index.html"
        if not page.exists():
            problems.append(f"sitemap.xml: {loc} has no page")
        elif 'name="robots" content="noindex"' in page.read_text(encoding="utf-8"):
            problems.append(f"sitemap.xml: {loc} is a redirect")
    if site.abs_url("sitemap.xml") not in files["robots.txt"].read_text(encoding="utf-8"):
        problems.append("robots.txt: does not point to the sitemap")
    links = [e.text for e in feed.findall("channel/item/link")]
    if not links:
        problems.append("feed.xml: no items")
    elif notes and site.abs_url(f"reports/{notes[0]['date']}/") not in links:
        problems.append("feed.xml: lacks the newest close note")
    return problems


def main():
    n, problems, warnings = check_notes()
    problems += check_home()
    problems += check_discovery()
    for w in warnings[:20]:
        print(f"::warning::{w}")
    if problems:
        for p in problems[:40]:
            print(f"::error::{p}")
        if len(problems) > 40:
            print(f"::error::... and {len(problems) - 40} more")
        sys.exit(1)
    print(f"site check passed: {n} close note pages, homepage index"
          + (", sitemap, robots.txt and feed" if site.SITE_URL else ""))


if __name__ == "__main__":
    main()
