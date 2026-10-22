#!/usr/bin/env python3
"""Fetch the economic calendar, at deploy time.

Run by .github/workflows/pages.yml before tools/build_site.py. Writes one
file, .cache/calendar/calendar.json: every event from the first week the
calendar ran (past weeks feed the archive pages the close notes link to),
the last good copy of each source with the day it was fetched, and the
figures behind Previous and Actual. build_site.py reads it.

Sources: each publisher's own schedule (see SOURCES), values from FRED,
Eurostat, the ECB, the ONS, the Bank of England and TreasuryDirect, and the
earnings of the 100 largest S&P 500 companies: membership from State
Street's SPY holdings, market cap, dates and EPS from Yahoo Finance.

When a source fails, its events stay as last fetched and the page shows the
day of that copy; a failure never empties the calendar. Nothing here is
published: the deploy refuses any .json in the site.

    python3 tools/calendar_data.py           fetch and update the cache
    python3 tools/calendar_data.py --probe   fetch into a scratch copy and
                                             print what each source returned
"""
import calendar as cal
import csv
import datetime as dt
import html
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nyse  # noqa: E402
from dashboard_data import fred, log  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "calendar" / "calendar.json"
NY = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
WEEKS = 5  # this week and the next four
BROWSER = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
           "Chrome/124.0 Safari/537.36")
BOT = "Mozilla/5.0 (compatible; andramarkets-site; +https://github.com/Pabloballesteros1412/andramarkets-site)"
MAX = 8 * 1024 * 1024
PROBE = "--probe" in sys.argv
MONTHS = {m.lower(): i for i, m in enumerate(cal.month_name) if m}
MONTHS.update({m.lower(): i for i, m in enumerate(cal.month_abbr) if m})
MONTHS["sept"] = 9


def fetch(url, data=None, headers=None, ua=BROWSER, cookies=None):
    """Bytes at url. Retries once with the other user agent on a 403."""
    last = None
    for agent in (ua, BOT if ua == BROWSER else BROWSER):
        h = {"User-Agent": agent, "Accept": "text/html,application/xhtml+xml,application/json,text/calendar,*/*",
             "Accept-Language": "en-GB,en;q=0.9", **(headers or {})}
        if cookies:
            h["Cookie"] = cookies
        req = urllib.request.Request(url, data=data, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                raw = r.read(MAX + 1)
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 403:
                continue
            raise
        if len(raw) > MAX:
            raise ValueError(f"{url}: response too large")
        return raw
    raise last


LAST = {}  # the last page read, for --probe to show when a parser finds nothing


def text(url, **kw):
    body = fetch(url, **kw).decode("utf-8", "replace")
    LAST.update(url=url, body=body)
    return body


PROBE_KEYS = {"conference_board": r"Consumer Confidence|[Rr]elease [Cc]alendar", "fed_g17": r"2026", "fed_speeches": r"Speech|title",
              "boj": r"20\d\d|Meeting", "ecb_speeches": r"Lagarde|[Ss]peech", "ism": r"PMI|Manufacturing"}


def snippets(key):
    t = re.sub(r"\s+", " ", strip(LAST.get("body") or ""))
    out = []
    for m in re.finditer(PROBE_KEYS.get(key, r"$^"), t):
        if out and m.start() < out[-1][1]:
            continue
        out.append((max(0, m.start() - 150), m.end() + 250))
        if len(out) == 6:
            break
    return "\n".join(f"    ...{t[a:b]}..." for a, b in out)


def excerpt():
    """What the last page said, for the probe log."""
    body = LAST.get("body") or ""
    t = re.sub(r"\s+", " ", strip(body))
    return f"    last page {LAST.get('url')} ({len(body)} bytes): {t[:1500]}"


# The full set a browser sends on a page load; some sites refuse a request without it.
NAVIGATE = {"Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1", "Upgrade-Insecure-Requests": "1", "Cache-Control": "no-cache"}


def links(page, base):
    """[(absolute url, link text)] in a page."""
    return [(urllib.parse.urljoin(base, html.unescape(h)), re.sub(r"\s+", " ", strip(t)))
            for h, t in re.findall(r'(?is)<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', page)]


def strip(fragment):
    """Plain text of an HTML fragment, whitespace collapsed."""
    fragment = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", fragment)
    fragment = re.sub(r"(?i)<br\s*/?>|</(p|div|li|td|th|tr|dt|dd|h\d)>", " \n ", fragment)
    return re.sub(r"[ \t\r\f\v]+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def rows(page, tag="tr"):
    """Plain text of each <tr> (or other block) in a page."""
    return [re.sub(r"\s+", " ", strip(m)) for m in re.findall(rf"(?is)<{tag}\b.*?</{tag}>", page)]


def month_num(name):
    return MONTHS.get(name.lower().rstrip("."))


def nearest_year(month, day, today):
    """The year that puts month/day closest to today (schedules often omit it)."""
    best = None
    for y in (today.year - 1, today.year, today.year + 1):
        try:
            d = dt.date(y, month, day)
        except ValueError:
            continue
        if best is None or abs((d - today).days) < abs((best - today).days):
            best = d
    return best


def parse_clock(s):
    """(hour, minute) from '8:30 AM', '8:30 a.m.', '14:15', '2 p.m.', else None."""
    m = re.search(r"(\d{1,2})(?:[:.](\d{2}))?\s*([ap])\.?\s*m\.?", s, re.I)
    if m:
        h = int(m.group(1)) % 12 + (12 if m.group(3).lower() == "p" else 0)
        return h, int(m.group(2) or 0)
    m = re.search(r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\b", s)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def at(day, hm, tz):
    """Aware UTC datetime for a local wall-clock time, or None for an all-day item."""
    if hm is None:
        return None
    return dt.datetime(day.year, day.month, day.day, hm[0], hm[1], tzinfo=ZoneInfo(tz)).astimezone(UTC)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def ref_month(s):
    """'2026-09' from 'September 2026' or 'Sep 2026' in s, else None."""
    m = re.search(r"\b([A-Z][a-z]{2,8})\.? (\d{4})\b", s)
    if m and month_num(m.group(1)):
        return f"{m.group(2)}-{month_num(m.group(1)):02d}"
    return None


def ref_quarter(s):
    """'2026-Q3' from 'Q3/2026', '3rd Quarter 2026', 'Third Quarter 2026', 'Q3 2026'."""
    m = re.search(r"\bQ([1-4])\s*[/ ]\s*(\d{4})\b", s)
    if m:
        return f"{m.group(2)}-Q{m.group(1)}"
    m = re.search(r"\b(January|April|July|October) to (March|June|September|December),? (\d{4})", s)
    if m:
        return f"{m.group(3)}-Q{month_num(m.group(2)) // 3}"
    words = {"first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3, "fourth": 4, "4th": 4}
    m = re.search(r"\b(first|1st|second|2nd|third|3rd|fourth|4th) quarter,? (\d{4})", s, re.I)
    if m:
        return f"{m.group(2)}-Q{words[m.group(1).lower()]}"
    return None


def period_label(ref):
    if not ref:
        return ""
    if "-Q" in ref:
        y, q = ref.split("-Q")
        return f"Q{q} {y}"
    y, m = ref.split("-")[:2]
    return f"{cal.month_abbr[int(m)]} {y}"


class Events:
    """Collects one source's events."""

    def __init__(self, src):
        self.src, self.items = src, []

    def add(self, day, title, *, country, imp, kind="macro", when=None, tz=None, url=None,
            ind=None, ref=None, extra=None, timing=None, cite=None):
        """One event. when is (hour, minute) in tz, or None for an all-day item;
        cite names another source the row is read from (its schedule page is the link)."""
        hm = when if isinstance(when, tuple) or when is None else parse_clock(when)
        utc = at(day, hm, tz) if hm else None
        nyday = utc.astimezone(NY).date() if utc else day
        ev = {"id": f"{self.src}:{nyday}:{slug(title)}", "src": cite or self.src, "date": nyday.isoformat(),
              "utc": utc.isoformat() if utc else None, "timing": timing, "country": country,
              "kind": kind, "imp": imp, "title": title, "url": url or SOURCES[cite or self.src]["url"],
              "ind": ind, "ref": ref}
        ev.update(extra or {})
        self.items.append(ev)


# Publishers -----------------------------------------------------------------
#
# Each fetcher returns the publisher's events from the start of this week to
# the end of the window. Titles say what the release is in plain words; the
# reference period is added when the schedule names it.

def window():
    today = dt.datetime.now(NY).date()
    start = today - dt.timedelta(days=today.weekday())
    return today, start, start + dt.timedelta(days=7 * WEEKS - 1)


def in_window(day):
    _, start, end = window()
    return start <= day <= end


ICS_ZONES = {"US-Eastern": "America/New_York", "US/Eastern": "America/New_York", "Eastern Standard Time": "America/New_York"}


def ics_events(raw):
    """[(dtstart aware or date, summary, description, url)] from an iCalendar file."""
    raw = re.sub(r"\r?\n[ \t]", "", raw)  # unfold lines
    out = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", raw, re.S):
        props = {}
        for line in block.strip().splitlines():
            if ":" not in line:
                continue
            k, v = line.split(":", 1)
            name, *params = k.split(";")
            props[name.upper()] = (params, v.replace("\\,", ",").replace("\\n", " ").replace("\\;", ";"))
        if "DTSTART" not in props:
            continue
        params, v = props["DTSTART"]
        tzid = next((p.split("=", 1)[1] for p in params if p.upper().startswith("TZID=")), None)
        if re.fullmatch(r"\d{8}", v):
            start = dt.date(int(v[:4]), int(v[4:6]), int(v[6:]))
        else:
            d = dt.datetime.strptime(v.rstrip("Z")[:15], "%Y%m%dT%H%M%S")
            if v.endswith("Z"):
                start = d.replace(tzinfo=UTC)
            else:
                tz = (tzid or "America/New_York").strip('"')
                start = d.replace(tzinfo=ZoneInfo(ICS_ZONES.get(tz, tz)))
        out.append((start, props.get("SUMMARY", ([], ""))[1], props.get("DESCRIPTION", ([], ""))[1],
                    props.get("URL", ([], ""))[1]))
    return out


BLS = [  # (summary starts with, title, importance, indicator, release page)
    ("Employment Situation", "Nonfarm payrolls", "High", "payrolls", "empsit"),
    ("Consumer Price Index", "Consumer prices (CPI)", "High", "cpi", "cpi"),
    ("Producer Price Index", "Producer prices (PPI)", "Medium", "ppi", "ppi"),
    ("Job Openings and Labor Turnover", "Job openings (JOLTS)", "Medium", "jolts", "jolts"),
    ("Employment Cost Index", "Employment cost index", "Medium", "eci", "eci"),
]


def bls():
    ev = Events("bls")
    found = []
    today, start, end = window()
    try:
        for y, m in sorted({(d.year, d.month) for d in (start, today, end)}):
            page = text(f"https://www.bls.gov/schedule/{y}/{m:02d}_sched_list.htm", headers=NAVIGATE)
            for r in rows(page):
                dm = re.search(r"([A-Z][a-z]+day), ([A-Z][a-z]+) (\d{1,2}), (\d{4})", r)
                hm = parse_clock(r)
                if dm and hm and month_num(dm.group(2)):
                    d = dt.date(int(dm.group(4)), month_num(dm.group(2)), int(dm.group(3)))
                    found.append((dt.datetime(d.year, d.month, d.day, *hm, tzinfo=NY), r))
    except Exception as e:  # noqa: BLE001  the calendar file has the dates, without reference periods
        log(f"bls: schedule pages failed ({type(e).__name__}: {e}); reading the calendar file", "warning")
        found = [(start_, f"{summary} {desc}") for start_, summary, desc, _ in
                 ics_events(text("https://www.bls.gov/schedule/news_release/bls.ics", headers=NAVIGATE))]
    for start, label in found:
        day = start.astimezone(NY).date() if isinstance(start, dt.datetime) else start
        if not in_window(day):
            continue
        for prefix, title, imp, ind, page in BLS:
            if label.startswith(prefix) or f" {prefix}" in label[:80]:
                ref = ref_quarter(label) if ind == "eci" else ref_month(label)
                when = (start.astimezone(NY).hour, start.astimezone(NY).minute) if isinstance(start, dt.datetime) else None
                ev.add(day, f"{title}, {period_label(ref)}" if ref else title, country="US", imp=imp,
                       when=when, tz="America/New_York", ind=ind, ref=ref,
                       url=f"https://www.bls.gov/news.release/{page}.nr0.htm")
                break
    return list({e["id"]: e for e in ev.items}.values())


BEA = [
    ("GDP", "GDP", "High", "gdp", "https://www.bea.gov/data/gdp/gross-domestic-product"),
    ("Gross Domestic Product", "GDP", "High", "gdp", "https://www.bea.gov/data/gdp/gross-domestic-product"),
    ("Personal Income and Outlays", "PCE prices, personal income and spending", "High", "pce",
     "https://www.bea.gov/data/income-saving/personal-income"),
    ("U.S. International Trade in Goods and Services", "Trade balance", "Medium", "trade",
     "https://www.bea.gov/data/intl-trade-investment/international-trade-goods-and-services"),
]


def bea():
    ev = Events("bea")
    page = text("https://www.bea.gov/news/schedule")
    today = window()[0]
    for r in rows(page):
        dm = re.search(r"\b([A-Z][a-z]+)\.? (\d{1,2})\b", r)
        hm = parse_clock(r)
        if not (dm and month_num(dm.group(1)) and hm):
            continue
        day = nearest_year(month_num(dm.group(1)), int(dm.group(2)), today)
        if not in_window(day):
            continue
        for prefix, title, imp, ind, url in BEA:
            if prefix in r:
                if ind == "gdp":
                    stage = re.search(r"\((Advance|Second|Third)[^)]*\)", r)
                    ref = ref_quarter(r)
                    name = f"GDP, {period_label(ref)}" if ref else "GDP"
                    if stage:
                        name += f", {stage.group(1).lower()} estimate"
                else:
                    ref = ref_month(r)
                    name = f"{title}, {period_label(ref)}" if ref else title
                ev.add(day, name, country="US", imp=imp, when=hm, tz="America/New_York",
                       ind=ind, ref=ref, url=url)
                break
    return ev.items


CENSUS = [
    ("Advance Monthly Sales for Retail", "Retail sales", "High", "retail",
     "https://www.census.gov/retail/sales.html"),
    ("New Residential Construction", "Housing starts", "Medium", "starts",
     "https://www.census.gov/construction/nrc/current/index.html"),
    ("New Residential Sales", "New home sales", "Medium", "nhs",
     "https://www.census.gov/construction/nrs/current/index.html"),
    ("Advance Report on Durable Goods", "Durable goods orders", "Medium", "durables",
     "https://www.census.gov/manufacturing/m3/adv/current/index.html"),
]


def census():
    """The list view shows one year; the year pages it links to hold the rest."""
    ev = Events("census")
    base = "https://www.census.gov/economic-indicators/calendar-listview.html"
    first = ""
    for attempt in range(3):
        first = text(base)
        if "Release Schedule" in first:
            break
        # Sometimes the indicators landing page is served instead; it links the schedule.
        lv = [h for h, t in links(first, base) if "calendar" in h.lower() and "list" in h.lower()]
        if lv:
            first = text(lv[0])
            if "Release Schedule" in first:
                break
        time.sleep(3)
    _, start, end = window()
    pages = {base: first}
    for y in sorted({start.year, end.year}):
        if f"{y} Economic Indicator Release Schedule" in strip(first):
            continue
        for href, label in links(first, base):
            if str(y) in label and "calendar" in label.lower():
                page = text(href)
                lv = [h for h, t in links(page, href) if "list view" in t.lower() and str(y) in h]
                if lv:
                    href, page = lv[0], text(lv[0])
                pages[href] = page
                break
    seen = set()
    for page in pages.values():
        for r in rows(page):
            for prefix, title, imp, ind, url in CENSUS:
                if prefix.lower() not in r.lower():
                    continue
                dm = re.search(r"\b([A-Z][a-z]+) (\d{1,2}), (\d{4})\b", r)
                if not dm or not month_num(dm.group(1)):
                    continue
                day = dt.date(int(dm.group(3)), month_num(dm.group(1)), int(dm.group(2)))
                if not in_window(day) or (ind, day) in seen:
                    continue
                seen.add((ind, day))
                after = r[dm.end():]
                ref = ref_month(after)
                # Census releases at 8:30 am ET, new home sales at 10:00 am, when the row gives no time.
                hm = parse_clock(after[:20]) or ((10, 0) if ind == "nhs" else (8, 30))
                ev.add(day, f"{title}, {period_label(ref)}" if ref else title, country="US", imp=imp,
                       when=hm, tz="America/New_York", ind=ind, ref=ref, url=url)
                break
    return ev.items


def g17():
    """Industrial production, Federal Reserve G.17, 9:15 am ET. Dates read "17-November-2026"."""
    ev = Events("fed_g17")
    t = strip(text("https://www.federalreserve.gov/releases/g17/release_dates.htm"))
    for m in re.finditer(r"\b(\d{1,2})-([A-Z][a-z]+)-(\d{4})\b", t):
        if not month_num(m.group(2)):
            continue
        day = dt.date(int(m.group(3)), month_num(m.group(2)), int(m.group(1)))
        if in_window(day):
            ev.add(day, "Industrial production", country="US", imp="Medium", when=(9, 15),
                   tz="America/New_York", ind="ip", url="https://www.federalreserve.gov/releases/g17/current/default.htm")
    return list({e["id"]: e for e in ev.items}.values())


def fomc_meetings():
    """[(first day, last day, minutes date or None)] from the FOMC calendar page."""
    page = text("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm")
    out = []
    for panel in re.split(r'(?i)<div class="panel panel-default', page):
        y = re.search(r"(\d{4}) FOMC Meetings", panel)
        if not y:
            continue
        year = int(y.group(1))
        for block in re.split(r'(?i)<div class="(?:row )?fomc-meeting(?:"| )', panel)[1:]:
            t = strip(block[:3000])
            m = re.search(r"([A-Z][a-z]+)(?:/([A-Z][a-z]+))?\s+(\d{1,2})(?:-(\d{1,2}))?", t)
            if not m or not month_num(m.group(1)):
                continue
            m1 = month_num(m.group(1))
            m2 = month_num(m.group(2)) if m.group(2) else m1
            first = dt.date(year, m1, int(m.group(3)))
            last = dt.date(year + (1 if m2 < m1 else 0), m2, int(m.group(4) or m.group(3)))
            minutes = None
            mm = re.search(r"Minutes.{0,80}?Released ([A-Z][a-z]+) (\d{1,2}), (\d{4})", t, re.S)
            if mm and month_num(mm.group(1)):
                minutes = dt.date(int(mm.group(3)), month_num(mm.group(1)), int(mm.group(2)))
            if "notation vote" in t.lower() or "unscheduled" in t.lower():
                continue
            out.append((first, last, minutes))
    if not out:
        raise ValueError("no FOMC meetings found")
    return out


def fed():
    ev = Events("fed")
    url = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
    for first, last, minutes in fomc_meetings():
        if in_window(last):
            ev.add(last, "FOMC rate decision", country="US", imp="High", when=(14, 0),
                   tz="America/New_York", ind="fedfunds", url=url,
                   extra={"policy_day": last.isoformat()})
            ev.add(last, "Fed Chair press conference", country="US", imp="High", when=(14, 30),
                   tz="America/New_York", url=url)
        if minutes and in_window(minutes):
            ev.add(minutes, f"FOMC minutes, {last.day} {cal.month_abbr[last.month]} meeting", country="US",
                   imp="Medium", when=(14, 0), tz="America/New_York", url=url)
    return ev.items


def fed_blackout():
    """The FOMC's blackout: from the second Saturday before a meeting to the
    midnight after it ends (Fed, FOMC Policy on External Communications)."""
    ev = Events("fed_blackout")
    for first, last, _ in fomc_meetings():
        start = first - dt.timedelta(days=(first.weekday() - 5) % 7 or 7) - dt.timedelta(days=7)
        end = last + dt.timedelta(days=1)
        if in_window(start):
            ev.add(start, f"Fed blackout period begins, until {end.day} {cal.month_abbr[end.month]}",
                   country="US", imp="Medium", kind="market")
        if in_window(end):
            ev.add(end, "Fed blackout period ends at midnight", country="US", imp="Medium", kind="market")
    return ev.items


# The Board's calendar writes "Chairman"; fireside chats are listed as "Discussion".
FED_SPEAKERS = [("Vice Chair for Supervision", "Medium"), ("Vice Chair", "Medium"), ("Chairman", "High"), ("Chair", "High")]


def fed_speeches():
    """Speeches by the Chair and Vice Chairs, from the data behind the Board's calendar."""
    ev = Events("fed_speeches")
    data = json.loads(text("https://www.federalreserve.gov/json/calendar.json").lstrip("\ufeff"))
    items = data.get("events", data) if isinstance(data, dict) else data
    today = window()[0]
    for e in items if isinstance(items, list) else []:
        if not isinstance(e, dict):
            continue
        title = strip(str(e.get("title") or ""))
        kind = str(e.get("type") or "")
        if "Speech" not in kind and not re.match(r"(Speech|Discussion|Testimony)\b", title):
            continue
        who = next(((role, imp) for role, imp in FED_SPEAKERS if re.search(rf"\b{role}\b", title)), None)
        if not who or "Governor" in title.split(who[0])[0]:
            continue
        month = str(e.get("month") or "")
        days = re.findall(r"\d{1,2}", str(e.get("days") or ""))
        if not re.fullmatch(r"\d{4}-\d{2}", month) or not days:
            continue
        day = dt.date(int(month[:4]), int(month[5:]), int(days[0]))
        if not in_window(day):
            continue
        name = re.search(r"(Vice Chair for Supervision|Vice Chair|Chairman|Chair) ([A-Z][A-Za-z.\- ]+?)(?:$| at | on | to |,| -)", title)
        what = "Testimony" if title.startswith("Testimony") else "Discussion" if title.startswith("Discussion") else "Speech"
        role = name.group(1).replace("Chairman", "Chair") if name else who[0].replace("Chairman", "Chair")
        label = f"{what} by Fed {role} {name.group(2).strip()}" if name else f"{what} by Fed {role}"
        ev.add(day, label, country="US", imp=who[1], when=parse_clock(str(e.get("time") or "")), tz="America/New_York")
    del today
    return ev.items


def treasury():
    ev = Events("treasury")
    data = json.loads(text("https://www.treasurydirect.gov/TA_WS/securities/upcoming?format=json"))
    for s in data:
        kind = s.get("securityType", "")
        if kind not in ("Note", "Bond") or (s.get("floatingRate") or "").lower() == "yes":
            continue
        when = s.get("auctionDate") or s.get("competitiveAuctionCloseDate")
        if not when:
            raise ValueError(f"no auction date among {sorted(k for k in s if 'ate' in k)[:20]}")
        day = dt.date.fromisoformat(when[:10])
        if not in_window(day):
            continue
        term = s.get("securityTerm", "").replace("-Year", "-year").replace("-Month", "-month")
        tips = (s.get("inflationIndexSecurity") or "").lower() == "yes" or bool(s.get("cpiBaseReferencePeriod"))
        title = f"{term} {'TIPS' if tips else kind.lower()} auction"
        if (s.get("reopening") or "").lower() == "yes":
            title += ", reopening"
        close = parse_clock(s.get("closingTimeCompetitive") or s.get("competitiveAuctionCloseTime") or "") or (13, 0)
        ev.add(day, title, country="US", imp="Medium", when=close, tz="America/New_York",
               ind="auction", extra={"cusip": s.get("cusip"), "term": s.get("securityTerm"), "stype": kind, "tips": tips},
               url="https://www.treasurydirect.gov/auctions/upcoming/")
    return ev.items


def claims():
    """Weekly jobless claims: Thursdays at 8:30 am ET, a day earlier when the
    Thursday is a federal holiday (Department of Labor)."""
    ev = Events("dol")
    _, start, end = window()
    d = start + dt.timedelta(days=(3 - start.weekday()) % 7)
    while d <= end:
        day = d - dt.timedelta(days=1) if d in federal_holidays(d.year) else d
        week = d - dt.timedelta(days=5)  # the Saturday that ends the week reported
        ev.add(day, f"Initial jobless claims, week to {week.day} {cal.month_abbr[week.month]}", country="US",
               imp="Medium", when=(8, 30), tz="America/New_York", ind="claims", ref=week.isoformat())
        d += dt.timedelta(days=7)
    return ev.items


def federal_holidays(year):
    def nth(month, weekday, n):
        d = dt.date(year, month, 1)
        d += dt.timedelta(days=(weekday - d.weekday()) % 7)
        return d + dt.timedelta(weeks=n - 1)

    def observed(d):
        return d - dt.timedelta(days=1) if d.weekday() == 5 else d + dt.timedelta(days=1) if d.weekday() == 6 else d

    fixed = [observed(dt.date(year, m, d)) for m, d in ((1, 1), (6, 19), (7, 4), (11, 11), (12, 25))]
    return set(fixed) | {nth(1, 0, 3), nth(2, 0, 3), nth(9, 0, 1), nth(10, 0, 2), nth(11, 3, 4),
                         dt.date(year, 5, 31) - dt.timedelta(days=dt.date(year, 5, 31).weekday())}


def ism():
    ev = Events("ism")
    page = text("https://www.ismworld.org/supply-management-news-and-reports/reports/rob-report-calendar/")
    if "Report On Business" not in page and "Manufacturing" not in page:
        raise ValueError(f"the calendar page did not load ({len(page)} bytes, likely a bot check)")
    today = window()[0]
    for r in rows(page):
        for key, title in (("Manufacturing", "ISM manufacturing PMI"), ("Services", "ISM services PMI")):
            if key not in r:
                continue
            for dm in re.finditer(r"\b([A-Z][a-z]+)\.? (\d{1,2})(?:, (\d{4}))?", r):
                if not month_num(dm.group(1)):
                    continue
                day = (dt.date(int(dm.group(3)), month_num(dm.group(1)), int(dm.group(2))) if dm.group(3)
                       else nearest_year(month_num(dm.group(1)), int(dm.group(2)), today))
                if in_window(day):
                    ev.add(day, title, country="US", imp="High", when=(10, 0), tz="America/New_York",
                           url="https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/")
    return list({e["id"]: e for e in ev.items}.values())


PMI = [  # (title contains, region, label, importance)
    ("Flash US PMI", "US", "S&P Global flash US PMIs", "High"),
    ("Flash Eurozone PMI", "Euro area", "S&P Global flash euro area PMIs", "High"),
    ("Flash UK PMI", "UK", "S&P Global flash UK PMIs", "High"),
    ("Flash Japan PMI", "Japan", "S&P Global flash Japan PMIs", "Medium"),
    ("China General Manufacturing PMI", "China", "RatingDog China manufacturing PMI", "Medium"),
    ("China General Services PMI", "China", "RatingDog China services PMI", "Medium"),
]
MONTH_RE = "January|February|March|April|May|June|July|August|September|October|November|December"


def pmi():
    """The page lists days ("October 23") each followed by "00:30 UTC [title]" lines."""
    ev = Events("spglobal")
    t = re.sub(r"\s+", " ", strip(text("https://www.pmi.spglobal.com/Public/Release/ReleaseDates")))
    t = t[t.find("Upcoming"):] if "Upcoming" in t else t
    today = window()[0]
    day = None
    item = re.compile(rf"\b({MONTH_RE}) (\d{{1,2}}) (?=\d{{2}}:\d{{2}} UTC)|(\d{{2}}):(\d{{2}}) UTC (.+?)(?= \d{{2}}:\d{{2}} UTC| (?:{MONTH_RE}) \d{{1,2}} \d{{2}}:\d{{2}} UTC|$)")
    for m in item.finditer(t):
        if m.group(1):
            day = nearest_year(month_num(m.group(1)), int(m.group(2)), today)
            continue
        hit = next((x for x in PMI if x[0].lower() in m.group(5).lower()), None)
        if hit and day and in_window(day):
            ev.add(day, hit[2], country=hit[1], imp=hit[3], when=(int(m.group(3)), int(m.group(4))), tz="UTC")
    return list({e["id"]: e for e in ev.items}.values())


def conference_board():
    """The topic page shows the last release; the next is on the Release Calendar it links."""
    ev = Events("conference_board")
    base = "https://www.conference-board.org/topics/consumer-confidence"
    page = text(base)
    cal_pages = [h for h, t in links(page, base) if "release calendar" in t.lower() or "release-calendar" in h.lower()]
    if cal_pages:
        page = text(cal_pages[0])
    t = re.sub(r"\s+", " ", strip(page))
    for m in re.finditer(r"Consumer Confidence", t):
        near = t[max(0, m.start() - 160):m.end() + 160]
        dm = re.search(r"([A-Z][a-z]+)\.? (\d{1,2}),? (\d{4})", near) or re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", near)
        if not dm:
            continue
        if dm.group(1).isdigit():
            day = dt.date(int(dm.group(3)), int(dm.group(1)), int(dm.group(2)))
        elif month_num(dm.group(1)):
            day = dt.date(int(dm.group(3)), month_num(dm.group(1)), int(dm.group(2)))
        else:
            continue
        if in_window(day):
            ev.add(day, "Consumer confidence (Conference Board)", country="US", imp="High",
                   when=parse_clock(near[dm.end():dm.end() + 30]) or (10, 0), tz="America/New_York", url=base)
    return list({e["id"]: e for e in ev.items}.values())


def umich():
    """The home page names the next release: "Next data release: Friday, October 23,
    2026 for Final October data at 10am ET"."""
    ev = Events("umich")
    t = re.sub(r"\s+", " ", strip(text("https://www.sca.isr.umich.edu/")))
    m = re.search(r"Next data release: [A-Z][a-z]+, ([A-Z][a-z]+) (\d{1,2}), (\d{4}) for (Preliminary|Final) "
                  r"([A-Z][a-z]+) data(?: at ([\d:]+ ?[ap]m))?", t)
    if not m or not month_num(m.group(1)):
        raise ValueError("no next release on the Surveys of Consumers page")
    day = dt.date(int(m.group(3)), month_num(m.group(1)), int(m.group(2)))
    if in_window(day):
        ev.add(day, f"Consumer sentiment, {m.group(5)}, {m.group(4).lower()} (University of Michigan)", country="US",
               imp="Medium", when=parse_clock(m.group(6) or "") or (10, 0), tz="America/New_York", ind="umich")
    return ev.items


def ecb():
    ev = Events("ecb")
    page = text("https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html")
    pairs = re.findall(r"(?is)<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", page)
    if not pairs:
        raise ValueError("no meetings on the ECB calendar page")
    for d, what in pairs:
        dm = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", strip(d))
        what = strip(what)
        if not dm:
            continue
        day = dt.date(int(dm.group(3)), int(dm.group(2)), int(dm.group(1)))
        if not in_window(day):
            continue
        low = what.lower()
        if "monetary policy" in low and "press conference" in low:
            ev.add(day, "ECB rate decision", country="Euro area", imp="High", when=(14, 15), tz="Europe/Berlin",
                   ind="ecb_dfr", extra={"policy_day": day.isoformat()})
            ev.add(day, "ECB press conference", country="Euro area", imp="High", when=(14, 45), tz="Europe/Berlin")
        elif "account" in low:
            ev.add(day, "ECB account of the monetary policy meeting", country="Euro area", imp="Medium",
                   when=(13, 30), tz="Europe/Berlin")
    return ev.items


def ecb_speeches():
    """Speeches and hearings by the President from the ECB's weekly schedule."""
    ev = Events("ecb_speeches")
    t = re.sub(r"\s+", " ", strip(text("https://www.ecb.europa.eu/press/calendars/weekly/html/index.en.html")))
    heads = list(re.finditer(r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), (\d{1,2}) ([A-Z][a-z]+) (\d{4})(?! -)", t))
    for i, h in enumerate(heads):
        if not month_num(h.group(2)):
            continue
        day = dt.date(int(h.group(3)), month_num(h.group(2)), int(h.group(1)))
        chunk = t[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(t)]
        for entry in re.split(r"(?=Board member: )", chunk):
            if "Lagarde" not in entry:
                continue
            what = re.search(r"Event: (.+?)(?: Time: | Venue: | Contact | Text: |$)", entry)
            what = what.group(1) if what else ""
            if not re.search(r"speech|remarks|address|hearing|testimony|introductory statement", what, re.I):
                continue
            hm = re.search(r"Time: (\d{1,2}:\d{2})", entry)
            title = ("ECB President Lagarde at the European Parliament" if re.search(r"hearing|Parliament", what, re.I)
                     else "Speech by ECB President Lagarde")
            if in_window(day):
                ev.add(day, title, country="Euro area", imp="Medium", when=hm.group(1) if hm else None, tz="Europe/Berlin")
    return list({e["id"]: e for e in ev.items}.values())


EUROSTAT = [  # (title starts with, label, importance, indicator)
    ("Flash estimate inflation", "HICP inflation, flash", "High", "ea_hicp"),
    ("Inflation (HICP)", "HICP inflation, final", "Medium", "ea_hicp"),
    ("Preliminary flash estimate GDP", "GDP, preliminary flash", "High", "ea_gdp"),
    ("Flash estimate GDP", "GDP and employment, flash", "Medium", "ea_gdp"),
    ("GDP main aggregates", "GDP, update", "Medium", "ea_gdp"),
    ("Unemployment", "Unemployment rate", "Medium", "ea_unemp"),
    ("Industrial production", "Industrial production", "Medium", "ea_ip"),
    ("Retail trade", "Retail sales", "Medium", "ea_retail"),
    ("Economic Sentiment Indicator", "Economic sentiment", "Medium", "ea_esi"),
]


def eurostat():
    ev = Events("eurostat")
    _, start, end = window()
    url = ("https://ec.europa.eu/eurostat/o/calendars/eventsJson?"
           + urllib.parse.urlencode({"start": f"{start}T00:00:00Z", "end": f"{end + dt.timedelta(days=1)}T00:00:00Z",
                                     "isEuroindicator": "true"}))
    for e in json.loads(text(url)):
        hit = next((x for x in EUROSTAT if e.get("title", "").startswith(x[0])), None)
        if not hit:
            continue
        # The feed writes Luxembourg wall-clock times with a "Z".
        local = dt.datetime.strptime(e["start"][:16], "%Y-%m-%dT%H:%M")
        p = e.get("period") or ""
        ref = ref_quarter(p) or ref_month(p.replace("Sept ", "September "))
        ev.add(local.date(), f"{hit[1]}, {period_label(ref)}" if ref else hit[1], country="Euro area", imp=hit[2],
               when=(local.hour, local.minute), tz="Europe/Luxembourg", ind=hit[3], ref=ref,
               url="https://ec.europa.eu/eurostat/web/euro-indicators")
    return ev.items


def boe():
    ev = Events("boe")
    page = text("https://www.bankofengland.co.uk/monetary-policy/upcoming-mpc-dates")
    today = window()[0]
    for r in rows(page) or [strip(page)]:
        for m in re.finditer(r"\b([A-Z][a-z]+day) (\d{1,2}) ([A-Z][a-z]+)(?: (\d{4}))?", r):
            if not month_num(m.group(3)):
                continue
            day = (dt.date(int(m.group(4)), month_num(m.group(3)), int(m.group(2))) if m.group(4)
                   else nearest_year(month_num(m.group(3)), int(m.group(2)), today))
            if in_window(day) and day.strftime("%A") == m.group(1):
                ev.add(day, "Bank of England rate decision and minutes", country="UK", imp="High", when=(12, 0),
                       tz="Europe/London", ind="boe_rate", extra={"policy_day": day.isoformat()},
                       url="https://www.bankofengland.co.uk/monetary-policy/the-interest-rate-bank-rate")
    return list({e["id"]: e for e in ev.items}.values())


ONS = [  # (title starts with, label, importance, indicator)
    ("Consumer price inflation, UK", "Consumer prices (CPI)", "High", "uk_cpi"),
    ("Labour market overview, UK", "Labour market, unemployment rate", "High", "uk_unemp"),
    ("GDP monthly estimate, UK", "GDP, monthly", "High", "uk_gdpm"),
    ("GDP first quarterly estimate, UK", "GDP, first estimate", "High", "uk_gdpq"),
    ("GDP quarterly national accounts, UK", "GDP, final estimate", "Medium", "uk_gdpq"),
    ("Retail sales, Great Britain", "Retail sales", "Medium", None),
]


def ons():
    ev = Events("ons")
    _, start, end = window()
    found = []
    for n in (1, 2, 3):
        page = text("https://www.ons.gov.uk/releasecalendar?" + urllib.parse.urlencode(
            {"release-type": "type-upcoming", "after-date": start.isoformat(), "before-date": end.isoformat(),
             "limit": 50, "page": n}))
        items = re.findall(r"(?is)<li\b.*?</li>", page)
        for item in items:
            t = strip(item)
            dm = re.search(r"(\d{1,2}) ([A-Z][a-z]+) (\d{4})", t)
            link = re.search(r'href="(/releases/[^"]+)"', item)
            if dm and month_num(dm.group(2)) and link:
                found.append((dt.date(int(dm.group(3)), month_num(dm.group(2)), int(dm.group(1))),
                              parse_clock(t[dm.end():dm.end() + 12]), re.sub(r"\s+", " ", t), link.group(1)))
        if "page=" + str(n + 1) not in page:
            break
    for day, hm, title, uri in found:
        hit = next((x for x in ONS if x[0] in title), None)
        if not hit or not in_window(day):
            continue
        tail = title.split(hit[0], 1)[1]
        ref = ref_quarter(tail) or (ref_month(tail) if hit[3] in ("uk_cpi", "uk_gdpm", None) else None)
        ev.add(day, f"{hit[1]}, {period_label(ref)}" if ref else hit[1], country="UK", imp=hit[2],
               when=hm or (7, 0), tz="Europe/London", ind=hit[3], ref=ref, url=f"https://www.ons.gov.uk{uri}")
    return list({e["id"]: e for e in ev.items}.values())


def boj_dates(cell, year):
    """Dates in a cell like "Oct. 29 (Thurs.), 30 (Fri.)" or "Apr. 30 (Thurs.), May 1 (Fri.)"."""
    out, month = [], None
    for mon, d, y in re.findall(r"(?:([A-Z][a-z]{2,8})\.? )?(\d{1,2}) \([A-Z][a-z]{2,4}\.?\)(?:, (\d{4}))?", cell):
        if mon and month_num(mon):
            month = month_num(mon)
        if month:
            out.append(dt.date(int(y) if y else year, month, int(d)))
    return out


def boj():
    ev = Events("boj")
    url = "https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm"
    page = text(url)
    for table in re.findall(r"(?is)<table\b.*?</table>", page):
        y = re.search(r"Table\s*:\s*(\d{4})|<caption[^>]*>\D*(\d{4})", table)
        if not y:
            continue
        year = int(y.group(1) or y.group(2))
        for row in re.findall(r"(?is)<tr\b.*?</tr>", table):
            cells = [strip(c) for c in re.findall(r"(?is)<t[hd]\b[^>]*>(.*?)</t[hd]>", row)]
            if len(cells) < 4:
                continue
            meeting = boj_dates(cells[0], year)
            if not meeting:
                continue
            day = meeting[-1]
            if in_window(day):
                ev.add(day, "Bank of Japan rate decision", country="Japan", imp="High", url=url,
                       extra={"no_time": True})
            for d in boj_dates(cells[2], year):
                if in_window(d):
                    ev.add(d, f"Bank of Japan summary of opinions, {day.day} {cal.month_abbr[day.month]} meeting",
                           country="Japan", imp="Medium", when=(8, 50), tz="Asia/Tokyo", url=url)
            for d in boj_dates(cells[3], year):
                if in_window(d):
                    ev.add(d, f"Bank of Japan minutes, {meeting[0].day} {cal.month_abbr[meeting[0].month]} meeting",
                           country="Japan", imp="Medium", when=(8, 50), tz="Asia/Tokyo", url=url)
    return list({e["id"]: e for e in ev.items}.values())


NBS = [  # (row contains, title, importance)
    ("National Economic Performance", "Activity data: industrial production, retail sales, investment", "High"),
    ("Purchasing Managers", "Official PMIs", "High"),
    ("Consumer Price Index", "Consumer and producer prices (CPI, PPI)", "High"),
]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def nbs_days(row, year):
    """Release days in a calendar row: one "DD/Day" cell or "......" per month in order,
    a moved release sitting in the next month's cell; the weekday settles the month."""
    out, month, last = [], 1, 0
    for m in re.finditer(r"(\d{1,2})/(Mon|Tue|Wed|Thu|Fri|Sat|Sun)|\u2026\u2026|\.{6}", row):
        if not m.group(1):
            month += 1
            continue
        d, wd = int(m.group(1)), WEEKDAYS.index(m.group(2))
        fits = []
        for mo in range(max(1, last), 13):
            try:
                day = dt.date(year, mo, d)
            except ValueError:
                continue
            if day.weekday() == wd:
                fits.append((abs(mo - month), mo, day))
        if fits:
            _, mo, day = min(fits)
            out.append(day)
            last, month = mo, mo + 1
    return out


def nbs():
    ev = Events("nbs")
    index = "https://www.stats.gov.cn/english/PressRelease/ReleaseCalendar/"
    year = window()[0].year
    pages = [h for h, t in links(text(index), index) if f"Calendar of NBS in {year}" in t]
    if not pages:
        raise ValueError(f"no {year} calendar linked from the NBS index")
    page = text(pages[0])
    for r in rows(page):
        hit = next((n for n in NBS if n[0] in r), None)
        if not hit:
            continue
        hm = parse_clock(r) or (10, 0)
        for day in nbs_days(r, year):
            if in_window(day):
                title = hit[1]
                if hit[0] == "National Economic Performance" and day.month in (1, 4, 7, 10):
                    title = "GDP and activity data: industrial production, retail sales, investment"
                ev.add(day, title, country="China", imp=hit[2], when=hm, tz="Asia/Shanghai",
                       url=pages[0])
    return list({e["id"]: e for e in ev.items}.values())


def pboc_lpr():
    """Loan prime rate: the 20th of each month at 9:00 am Beijing, the next
    working day when the 20th is not one (PBoC announcement, 2019)."""
    ev = Events("pboc")
    today, start, end = window()
    for y, m in sorted({(d.year, d.month) for d in (start, today, end)}):
        d = dt.date(y, m, 20)
        while d.weekday() >= 5:
            d += dt.timedelta(days=1)
        if in_window(d):
            ev.add(d, "Loan prime rates", country="China", imp="Medium", when=(9, 0), tz="Asia/Shanghai")
    return ev.items


def market():
    """NYSE holidays and early closes, options expiry, quad witching and the
    S&P 500 quarterly rebalance, from each exchange's published rules."""
    ev = Events("market")
    _, start, end = window()
    d = start
    while d <= end:
        if d.year in nyse.HOLIDAYS:
            if d.weekday() < 5 and nyse.is_trading_day(d) is False:
                ev.add(d, "NYSE closed, holiday", country="US", imp="High", kind="market",
                       url="https://www.nyse.com/markets/hours-calendars")
            elif nyse.close_time(d) == "1:00 pm":
                ev.add(d, "NYSE closes early, 1:00 pm", country="US", imp="High", kind="market",
                       url="https://www.nyse.com/markets/hours-calendars")
        third = d.day in range(15, 22) and d.weekday() == 4
        if third:
            expiry = d
            while nyse.is_trading_day(expiry) is False:
                expiry -= dt.timedelta(days=1)
            quarterly = d.month in (3, 6, 9, 12)
            ev.add(expiry, "Quarterly options and futures expiry (quad witching)" if quarterly else "Monthly options expiry",
                   country="US", imp="High" if quarterly else "Medium", kind="market", cite="cboe")
            if quarterly:
                ev.add(expiry, "S&P 500 quarterly rebalance, effective after the close", country="US", imp="Medium",
                       kind="market", cite="spdji")
        d += dt.timedelta(days=1)
    return ev.items


# One-off events, each with its official source. Add OPEC+ meetings, Jackson
# Hole, debt-ceiling deadlines and elections here as they are announced.
ONE_OFF = [
    (dt.date(2026, 11, 3), "US midterm elections", "US", "High", "https://www.usa.gov/midterm-elections"),
]


def one_off():
    ev = Events("one_off")
    for day, title, country, imp, url in ONE_OFF:
        if in_window(day):
            ev.add(day, title, country=country, imp=imp, kind="market", url=url)
    return ev.items


SOURCES = {
    # key: (display name, schedule page, fetcher)
    "bls": {"name": "Bureau of Labor Statistics", "url": "https://www.bls.gov/schedule/news_release/", "fn": bls},
    "bea": {"name": "Bureau of Economic Analysis", "url": "https://www.bea.gov/news/schedule", "fn": bea},
    "census": {"name": "Census Bureau", "url": "https://www.census.gov/economic-indicators/calendar-listview.html", "fn": census},
    "dol": {"name": "Department of Labor", "url": "https://www.dol.gov/ui/data.pdf", "fn": claims},
    "fed": {"name": "Federal Reserve, FOMC", "url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm", "fn": fed},
    "fed_blackout": {"name": "Federal Reserve, blackout policy",
                     "url": "https://www.federalreserve.gov/monetarypolicy/files/FOMC_ExtCommunicationStaff.pdf", "fn": fed_blackout},
    "fed_speeches": {"name": "Federal Reserve, calendar", "url": "https://www.federalreserve.gov/newsevents/calendar.htm", "fn": fed_speeches},
    "fed_g17": {"name": "Federal Reserve, G.17", "url": "https://www.federalreserve.gov/releases/g17/release_dates.htm", "fn": g17},
    "treasury": {"name": "US Treasury, TreasuryDirect", "url": "https://www.treasurydirect.gov/auctions/upcoming/", "fn": treasury},
    "ism": {"name": "ISM", "url": "https://www.ismworld.org/supply-management-news-and-reports/reports/rob-report-calendar/", "fn": ism},
    "spglobal": {"name": "S&P Global PMI", "url": "https://www.pmi.spglobal.com/Public/Release/ReleaseDates", "fn": pmi},
    "conference_board": {"name": "The Conference Board", "url": "https://www.conference-board.org/topics/consumer-confidence", "fn": conference_board},
    "umich": {"name": "University of Michigan", "url": "https://www.sca.isr.umich.edu/", "fn": umich},
    "ecb": {"name": "European Central Bank", "url": "https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html", "fn": ecb},
    "ecb_speeches": {"name": "European Central Bank, speeches", "url": "https://www.ecb.europa.eu/press/calendars/weekly/html/index.en.html", "fn": ecb_speeches},
    "eurostat": {"name": "Eurostat", "url": "https://ec.europa.eu/eurostat/web/main/news/release-calendar", "fn": eurostat},
    "boe": {"name": "Bank of England", "url": "https://www.bankofengland.co.uk/monetary-policy/upcoming-mpc-dates", "fn": boe},
    "ons": {"name": "Office for National Statistics", "url": "https://www.ons.gov.uk/releasecalendar", "fn": ons},
    "boj": {"name": "Bank of Japan", "url": "https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm", "fn": boj},
    "nbs": {"name": "National Bureau of Statistics of China", "url": "https://www.stats.gov.cn/english/PressRelease/ReleaseCalendar/", "fn": nbs},
    "pboc": {"name": "People's Bank of China", "url": "https://www.pbc.gov.cn/en/3688229/3688353/3688356/index.html", "fn": pboc_lpr},
    "market": {"name": "NYSE", "url": "https://www.nyse.com/markets/hours-calendars", "fn": market},
    "cboe": {"name": "Cboe, expiration calendar", "url": "https://www.cboe.com/about/hours/us-options/", "fn": None},
    "spdji": {"name": "S&P Dow Jones Indices", "url": "https://www.spglobal.com/spdji/en/indices/equity/sp-500/", "fn": None},
    "one_off": {"name": "One-off events", "url": "https://www.usa.gov/midterm-elections", "fn": one_off},
    "earnings": {"name": "Yahoo Finance, US earnings", "url": "https://finance.yahoo.com/calendar/earnings", "fn": None},
    "earnings_europe": {"name": "Yahoo Finance, European earnings", "url": "https://finance.yahoo.com/calendar/earnings",
                        "fn": None},
    "earnings_asia": {"name": "Yahoo Finance, Asian earnings and market caps",
                      "url": "https://finance.yahoo.com/research-hub/screener/", "fn": None},
    "stoxx600": {"name": "iShares, STOXX Europe 600 holdings",
                 "url": "https://www.ishares.com/uk/individual/en/products/251931/ishares-stoxx-europe-600-ucits-etf-de-fund",
                 "fn": None},
    "spy": {"name": "State Street, SPY holdings",
            "url": "https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy", "fn": None},
}
# Sources that always have something in a five-week window: an empty answer
# means the page changed, so it counts as a failure and the last copy stays.
# Indicators whose figure is a change (a rise or a fall: coloured, DESIGN.md);
# the rest are levels (rates, inflation, sentiment, balances) and stay in ink.
MOVES = {"payrolls", "ppi", "eci", "gdp", "retail", "durables", "ip", "ea_gdp", "ea_ip", "ea_retail", "uk_gdpm",
         "uk_gdpq"}

EXPECTED = {"bls", "census", "dol", "eurostat", "ons", "treasury", "market", "spglobal", "nbs", "fed_g17",
            "conference_board"}


# Previous and Actual ----------------------------------------------------------
#
# Each indicator is a series of (period, value): "2026-09" monthly, "2026-Q3"
# quarterly, an ISO date for weekly and daily data. Previous is the period
# before the one released; Actual is the released period, taken once, within
# a week of the release (so a later revision or a final estimate is never
# shown as the first print). Without a named reference period, the newest
# period before the release is Previous and the next one is Actual.

MINUS = "−"


def signed(v, dec):
    s = f"{abs(v):,.{dec}f}"
    return f"+{s}" if v > 0 else f"{MINUS}{s}" if v < 0 else s


def unsigned(v, dec):
    return f"{MINUS if v < 0 else ''}{abs(v):,.{dec}f}"


def key_of(day, freq):
    if freq == "M":
        return f"{day.year}-{day.month:02d}"
    if freq == "Q":
        return f"{day.year}-Q{(day.month - 1) // 3 + 1}"
    return day.isoformat()


def prev_key(key):
    if re.fullmatch(r"\d{4}-\d{2}", key):
        y, m = map(int, key.split("-"))
        return f"{y - (m == 1)}-{(m - 2) % 12 + 1:02d}"
    if re.fullmatch(r"\d{4}-Q\d", key):
        y, q = int(key[:4]), int(key[-1])
        return f"{y - (q == 1)}-Q{(q - 2) % 4 + 1}"
    return (dt.date.fromisoformat(key) - dt.timedelta(days=7)).isoformat()


def transform(points, how, lag):
    """[(key, value)] from [(key, level)]: level, change, percent change over lag periods."""
    vals = dict(points)
    keys = [k for k, _ in points]
    out = []
    for i, k in enumerate(keys):
        if how == "level":
            out.append((k, vals[k]))
            continue
        back = k
        for _ in range(lag):
            back = prev_key(back)
        if back not in vals:
            continue
        out.append((k, vals[k] - vals[back] if how == "diff" else (vals[k] / vals[back] - 1) * 100))
    return out


def fred_points(sid, freq, how, lag=1):
    start = dt.date.today() - dt.timedelta(days=3 * 366)
    raw = fred([sid], start)[sid]
    return transform([(key_of(d, freq), v) for d, v in raw], how, lag)


def eurostat_points(dataset, filters, how="level"):
    base = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
    for geo in ("EA", "EA21", "EA20"):
        q = urllib.parse.urlencode({**filters, "geo": geo, "lastTimePeriod": 30})
        d = json.loads(text(f"{base}{dataset}?{q}"))
        if not d.get("value"):
            continue
        times = sorted(d["dimension"]["time"]["category"]["index"].items(), key=lambda kv: kv[1])
        pts = []
        for t, i in times:
            v = d["value"].get(str(i))
            if v is not None:
                pts.append((t.replace("Q", "-Q") if re.fullmatch(r"\d{4}Q\d", t) else t, float(v)))
        if pts:
            return transform(pts, how, 1)
    raise ValueError(f"Eurostat {dataset}: no euro area values")


def ons_points(path, freq):
    d = json.loads(text(f"https://www.ons.gov.uk{path}/data"))
    out = []
    if freq == "M":
        for r in d.get("months", []):
            m = re.fullmatch(r"(\d{4}) ([A-Z]{3})", r.get("date", ""))
            if m and r.get("value") not in (None, ""):
                out.append((f"{m.group(1)}-{month_num(m.group(2)):02d}", float(r["value"])))
    else:
        for r in d.get("quarters", []):
            m = re.fullmatch(r"(\d{4}) Q([1-4])", r.get("date", ""))
            if m and r.get("value") not in (None, ""):
                out.append((f"{m.group(1)}-Q{m.group(2)}", float(r["value"])))
    if not out:
        raise ValueError(f"ONS {path}: no values")
    return out


def ecb_dfr_points():
    raw = text("https://data-api.ecb.europa.eu/service/data/FM/B.U2.EUR.4F.KR.DFR.LEV?format=csvdata&startPeriod=2022-01-01")
    lines = raw.strip().splitlines()
    head = lines[0].split(",")
    ti, vi = head.index("TIME_PERIOD"), head.index("OBS_VALUE")
    pts = [(r.split(",")[ti], float(r.split(",")[vi])) for r in lines[1:] if r.split(",")[vi]]
    if not pts:
        raise ValueError("ECB: no deposit facility rate")
    return pts


def boe_points():
    url = ("https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&"
           + urllib.parse.urlencode({"Datefrom": "01/Jan/2024", "Dateto": "now", "SeriesCodes": "IUDBEDR",
                                     "CSVF": "TN", "UsingCodes": "Y", "VPD": "Y", "VFD": "N"}))
    pts = []
    for line in text(url).splitlines()[1:]:
        parts = line.split(",")
        if len(parts) >= 2:
            try:
                pts.append((dt.datetime.strptime(parts[0].strip(), "%d %b %Y").date().isoformat(), float(parts[1])))
            except ValueError:
                continue
    if not pts:
        raise ValueError("Bank of England: no Bank Rate")
    return pts


def fed_range_points():
    start = dt.date.today() - dt.timedelta(days=400)
    s = fred(["DFEDTARL", "DFEDTARU"], start)
    lo = dict(s["DFEDTARL"])
    return [(d.isoformat(), [lo[d], hi]) for d, hi in s["DFEDTARU"] if d in lo]


def pct(suffix, sign=True, dec=1):
    return lambda v: f"{(signed if sign else unsigned)(v, dec)}%{(' ' + suffix) if suffix else ''}"


IND = {
    # key: (fetcher, format)
    "payrolls": (lambda: fred_points("PAYEMS", "M", "diff"), lambda v: f"{signed(v, 0)}k"),
    "cpi": (lambda: fred_points("CPIAUCNS", "M", "pct", 12), pct("y/y", False)),
    "ppi": (lambda: fred_points("PPIFIS", "M", "pct"), pct("m/m")),
    "jolts": (lambda: fred_points("JTSJOL", "M", "level"), lambda v: f"{v / 1000:.2f}m"),
    "eci": (lambda: fred_points("ECIALLCIV", "Q", "pct"), pct("q/q")),
    "gdp": (lambda: fred_points("A191RL1Q225SBEA", "Q", "level"), pct("annualised")),
    "pce": (lambda: fred_points("PCEPI", "M", "pct", 12), pct("y/y", False)),
    "retail": (lambda: fred_points("RSAFS", "M", "pct"), pct("m/m")),
    "starts": (lambda: fred_points("HOUST", "M", "level"), lambda v: f"{v / 1000:.2f}m annualised"),
    "nhs": (lambda: fred_points("HSN1F", "M", "level"), lambda v: f"{v:,.0f}k annualised"),
    "durables": (lambda: fred_points("DGORDER", "M", "pct"), pct("m/m")),
    "ip": (lambda: fred_points("INDPRO", "M", "pct"), pct("m/m")),
    "trade": (lambda: fred_points("BOPGSTB", "M", "level"), lambda v: f"{unsigned(v / 1000, 1)}bn dollars"),
    "claims": (lambda: fred_points("ICSA", "W", "level"), lambda v: f"{v / 1000:,.0f}k"),
    "umich": (lambda: fred_points("UMCSENT", "M", "level"), lambda v: f"{v:.1f}"),
    "fedfunds": (fed_range_points, lambda v: f"{v[0]:.2f} to {v[1]:.2f}%"),
    "ea_hicp": (lambda: eurostat_points("teicp000", {"unit": "PCH_M12", "coicop18": "TOTAL"}), pct("y/y", False)),
    "ea_gdp": (lambda: eurostat_points("namq_10_gdp", {"unit": "CLV_PCH_PRE", "s_adj": "SCA", "na_item": "B1GQ"}), pct("q/q")),
    "ea_unemp": (lambda: eurostat_points("une_rt_m", {"s_adj": "SA", "age": "TOTAL", "sex": "T", "unit": "PC_ACT"}),
                 pct("", False)),
    "ea_ip": (lambda: eurostat_points("sts_inpr_m", {"unit": "PCH_PRE", "s_adj": "SCA", "nace_r2": "B-D", "indic_bt": "PRD"}),
              pct("m/m")),
    "ea_retail": (lambda: eurostat_points("sts_trtu_m", {"unit": "PCH_PRE", "s_adj": "SCA", "nace_r2": "G47",
                                                         "indic_bt": "VOL_SLS"}), pct("m/m")),
    "ea_esi": (lambda: eurostat_points("teibs010", {"indic": "BS-ESI-I", "s_adj": "SA"}), lambda v: f"{v:.1f}"),
    "ecb_dfr": (ecb_dfr_points, lambda v: f"{v:.2f}%"),
    "uk_cpi": (lambda: ons_points("/economy/inflationandpriceindices/timeseries/d7g7/mm23", "M"), pct("y/y", False)),
    "uk_unemp": (lambda: ons_points("/employmentandlabourmarket/peoplenotinwork/unemployment/timeseries/mgsx/lms", "M"),
                 pct("", False)),
    "uk_gdpm": (lambda: transform(ons_points("/economy/grossdomesticproductgdp/timeseries/ecy2/mgdp", "M"), "pct", 1),
                pct("m/m")),
    "uk_gdpq": (lambda: ons_points("/economy/grossdomesticproductgdp/timeseries/ihyq/qna", "Q"), pct("q/q")),
    "boe_rate": (boe_points, lambda v: f"{v:.2f}%"),
}

VALUE_SOURCE = {  # indicator prefix -> source name shown with the figures
    "ea_": "Eurostat", "ecb_": "ECB", "uk_": "ONS", "boe_": "Bank of England",
}
POLICY = {"fedfunds", "ecb_dfr", "boe_rate"}  # step series: a level as of a day


def value_source(ind):
    return next((v for k, v in VALUE_SOURCE.items() if ind.startswith(k)), "FRED")


def level_on(points, day):
    """The level in force on day for a step series of (ISO date, value)."""
    best = None
    for k, v in points:
        if k <= day.isoformat():
            best = v
    return best


def resolve(ev, values, now):
    """Fill Previous and Actual on an event from the indicator's series."""
    ind = ev.get("ind")
    if not ind or ind not in IND or ind not in values:
        return
    pts = [tuple(p) for p in values[ind]["obs"]]
    if not pts:
        return
    fmt = IND[ind][1]
    release = dt.datetime.fromisoformat(ev["utc"]) if ev.get("utc") else \
        dt.datetime.combine(dt.date.fromisoformat(ev["date"]), dt.time(23, 59), NY)
    released = now >= release
    late = now > release + dt.timedelta(days=7)
    if ind in POLICY:
        day = dt.date.fromisoformat(ev.get("policy_day") or ev["date"])
        if not released or "previous" not in ev:
            v = level_on(pts, day - dt.timedelta(days=1))
            if v is not None and not released:
                ev["previous"] = fmt(v)
        # The new level shows once the series has a print after the decision
        # (FRED and the Bank of England publish daily; the ECB lists changes
        # only, so its level counts a day after the meeting).
        newest = max(k for k, _ in pts)
        settled = newest >= (day + dt.timedelta(days=1)).isoformat() or (ind == "ecb_dfr" and now.date() > day + dt.timedelta(days=1))
        if released and "actual" not in ev and settled and not late:
            v = level_on(pts, day + dt.timedelta(days=14))
            if v is not None:
                ev["actual"], ev["actual_seen"] = fmt(v), now.isoformat(timespec="seconds")
        return
    vals = dict(pts)
    keys = [k for k, _ in pts]
    ref = ev.get("ref")
    if not ref and keys:
        if not released:
            ev["base"] = keys[-1]
        if ev.get("base"):
            later = [k for k in keys if k > ev["base"]]
            ref = later[0] if later else None
            if not released:
                ev["previous"] = fmt(vals[ev["base"]])
                ev["prev_period"] = ev["base"]
    if ref:
        p = prev_key(ref)
        if p in vals and (not released or "previous" not in ev):
            ev["previous"], ev["prev_period"] = fmt(vals[p]), p
    if released and ref and ref in vals and "actual" not in ev and not late:
        ev["actual"], ev["actual_seen"] = fmt(vals[ref]), now.isoformat(timespec="seconds")


def fetch_values(cache, wanted):
    now = dt.datetime.now(UTC).isoformat(timespec="seconds")
    values = cache.setdefault("values", {})
    for ind in sorted(wanted):
        try:
            pts = IND[ind][0]()
        except Exception as e:  # noqa: BLE001  keep the last good figures
            kept = values.get(ind, {}).get("ok", "none")
            log(f"values {ind}: {type(e).__name__}: {e}; keeping the last good figures ({kept})", "warning")
            values.setdefault(ind, {"obs": [], "ok": None})["error"] = f"{type(e).__name__}: {e}"[:200]
            continue
        values[ind] = {"obs": [list(p) for p in pts[-40:]], "ok": now, "error": None, "source": value_source(ind)}


# Treasury auction yields: Previous is the last auction of the same security
# type and original term, Actual this auction's high yield.

def auction_values(events, now):
    ups = [e for e in events if e.get("ind") == "auction"]
    if not ups:
        return
    past = []
    for kind in ("Note", "Bond"):
        past += json.loads(text(f"https://www.treasurydirect.gov/TA_WS/securities/auctioned?format=json&type={kind}&days=730"))
    for e in ups:
        term = e.get("term")
        same = [p for p in past if p.get("securityType") == e.get("stype")
                and (p.get("originalSecurityTerm") or p.get("securityTerm")) in (term, e.get("orig_term"))
                and ((p.get("inflationIndexSecurity") or "").lower() == "yes" or bool(p.get("cpiBaseReferencePeriod"))) == e.get("tips")
                and (p.get("floatingRate") or "").lower() != "yes" and p.get("highYield")]
        adate = lambda p: (p.get("auctionDate") or p.get("competitiveAuctionCloseDate") or "")[:10]  # noqa: E731
        before = sorted((p for p in same if adate(p) and adate(p) < e["date"]), key=adate)
        if before and "actual" not in e:
            e["previous"] = f"{float(before[-1]['highYield']):.3f}%"
        mine = [p for p in past if p.get("cusip") == e.get("cusip") and adate(p) == e["date"] and p.get("highYield")]
        if mine and "actual" not in e:
            e["actual"], e["actual_seen"] = f"{float(mine[0]['highYield']):.3f}%", now.isoformat(timespec="seconds")
            e["actual_url"] = "https://www.treasurydirect.gov/auctions/announcements-data-results/"


# Earnings ---------------------------------------------------------------------

def xlsx_rows(raw):
    """Rows of the first sheet of an .xlsx file, as lists of strings."""
    z = zipfile.ZipFile(io.BytesIO(raw))
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        sx = z.read("xl/sharedStrings.xml").decode("utf-8")
        for si in re.findall(r"(?s)<si>(.*?)</si>", sx):
            shared.append(html.unescape("".join(re.findall(r"(?s)<t[^>]*>(.*?)</t>", si))))
    sheet = sorted(n for n in z.namelist() if n.startswith("xl/worksheets/sheet"))[0]
    out = []
    for row in re.findall(r"(?s)<row[^>]*>(.*?)</row>", z.read(sheet).decode("utf-8")):
        cells = []
        for attrs, body in re.findall(r"(?s)<c([^>]*)>(.*?)</c>", row):
            v = re.search(r"(?s)<v>(.*?)</v>", body)
            inline = re.search(r"(?s)<t[^>]*>(.*?)</t>", body)
            if 't="s"' in attrs and v:
                cells.append(shared[int(v.group(1))])
            elif v:
                cells.append(html.unescape(v.group(1)))
            elif inline:
                cells.append(html.unescape(inline.group(1)))
            else:
                cells.append("")
        out.append(cells)
    return out


def spy_members():
    raw = fetch("https://www.ssga.com/us/en/intermediary/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx")
    table = xlsx_rows(raw)
    head = next(i for i, r in enumerate(table) if "Ticker" in r)
    col = table[head].index("Ticker")
    out = []
    for r in table[head + 1:]:
        t = r[col].strip() if len(r) > col else ""
        if re.fullmatch(r"[A-Z]{1,5}(?:\.[A-Z])?", t):
            out.append(t.replace(".", "-"))
    if len(out) < 400:
        raise ValueError(f"SPY holdings: only {len(out)} tickers")
    return out


class Yahoo:
    def __init__(self):
        import http.cookiejar
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        # Yahoo answers 429 to a full browser string from a script; the bare token passes.
        self.op.addheaders = [("User-Agent", "Mozilla/5.0")]
        try:
            self.op.open("https://fc.yahoo.com", timeout=30)
        except urllib.error.HTTPError:
            pass  # answers 404 but sets the cookie
        self.crumb = self._open("https://query2.finance.yahoo.com/v1/test/getcrumb").decode()
        if not self.crumb or "<" in self.crumb:
            raise ValueError("Yahoo: no crumb")

    def _open(self, url, data=None):
        """Body at url, waiting and retrying when Yahoo rate-limits (429)."""
        for wait in (5, 20, 60, None):
            try:
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {})
                return self.op.open(req, timeout=45).read()
            except urllib.error.HTTPError as e:
                if e.code != 429 or wait is None:
                    raise
                time.sleep(wait)

    def json(self, url, body=None):
        sep = "&" if "?" in url else "?"
        data = json.dumps(body).encode() if body is not None else None
        return json.loads(self._open(f"{url}{sep}crumb={urllib.parse.quote(self.crumb)}", data))

    def screener(self, region, size):
        """The largest equities of one market by market cap."""
        body = {"offset": 0, "size": size, "sortField": "intradaymarketcap", "sortType": "desc", "quoteType": "equity",
                "query": {"operator": "and", "operands": [{"operator": "eq", "operands": ["region", region]}]},
                "userId": "", "userIdType": "guid"}
        res = self.json("https://query1.finance.yahoo.com/v1/finance/screener?lang=en-US&region=US&formatted=false", body)
        return res["finance"]["result"][0]["quotes"]

    def quotes(self, symbols):
        out = []
        for i in range(0, len(symbols), 50):
            q = urllib.parse.urlencode({"symbols": ",".join(symbols[i:i + 50])})
            out += self.json(f"https://query1.finance.yahoo.com/v7/finance/quote?{q}")["quoteResponse"]["result"]
        return out

    def eps(self, symbol):
        """([(quarter end, diluted EPS)], [(year end, diluted EPS)], currency) as reported."""
        q = urllib.parse.urlencode({"type": "quarterlyDilutedEPS,annualDilutedEPS", "period1": 1500000000,
                                    "period2": int(dt.datetime.now().timestamp()) + 86400})
        res = self.json(f"https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{symbol}?{q}")
        out, cur = {"quarterlyDilutedEPS": [], "annualDilutedEPS": []}, None
        for r in res["timeseries"]["result"]:
            for k in out:
                for x in r.get(k) or []:
                    if x and x.get("reportedValue"):
                        out[k].append((dt.date.fromisoformat(x["asOfDate"]), x["reportedValue"]["raw"]))
                        cur = cur or x.get("currencyCode")
        return sorted(out["quarterlyDilutedEPS"]), sorted(out["annualDilutedEPS"]), cur


def company(name):
    """One key per company across share classes ('Alphabet Inc.' for GOOGL and GOOG)."""
    return re.sub(r"\b(class [a-z]|cl [a-z]|inc|corp|corporation|co|plc|ltd|limited|new|ag|se|sa|nv|asa|ab)\b|[^a-z0-9 ]",
                  "", name.lower()).strip()


def major(currency):
    """The major unit of a Yahoo currency code: GBp (pence) is GBP."""
    return {"GBp": "GBP", "GBX": "GBP", "ZAc": "ZAR", "ILA": "ILS"}.get(currency or "", currency or "")


def usd_rates(yahoo, currencies):
    """US dollars per unit of each currency, from Yahoo's FX quotes."""
    want = sorted({major(c) for c in currencies if c and major(c) != "USD"})
    rates = {"USD": 1.0}
    for q in yahoo.quotes([f"{c}USD=X" for c in want]) if want else []:
        if q.get("regularMarketPrice"):
            rates[q["symbol"][:3]] = q["regularMarketPrice"]
    return rates


def usd_cap(q, rates):
    """Market cap in US dollars; price times shares when Yahoo gives no cap."""
    cap = q.get("marketCap")
    if not cap and q.get("sharesOutstanding") and q.get("regularMarketPrice"):
        price = q["regularMarketPrice"] / (100 if q.get("currency") == "GBp" else 1)
        cap = price * q["sharesOutstanding"]
    rate = rates.get(major(q.get("currency")))
    return cap * rate if cap and rate else None


# Europe: the STOXX Europe 600 from iShares' published holdings of its STOXX
# Europe 600 ETF (EXSA). Each holding's exchange (or, failing that, its
# country) gives the Yahoo Finance suffix.
STOXX600_HOLDINGS = [
    # The rebuilt site's holdings file, linked from the fund page (22 Oct 2026).
    "https://www.ishares.com/de/privatanleger/de/produkte/251931/ishares-stoxx-europe-600-ucits-etf-de/latest-holdings.csv",
    "https://www.ishares.com/uk/individual/en/products/251931/ishares-stoxx-europe-600-ucits-etf-de-fund/"
    "1478358465952.ajax?fileType=csv&fileName=EXSA_holdings&dataType=fund",
    "https://www.ishares.com/de/privatanleger/de/produkte/251931/ishares-stoxx-europe-600-ucits-etf-de-fund/"
    "1478358465952.ajax?fileType=csv&fileName=EXSA_holdings&dataType=fund",
]
# When a holdings address serves the fund's web page instead (iShares has rebuilt
# its site), the page's own download link for the holdings is followed.
HOLDINGS_LINK = re.compile(r'(?:holdings\.csv|fileType=csv|holdings[^"\'<>\s]*\.(?:csv|xlsx)|[Hh]oldings[^"\'<>\s]*download)')
EXCHANGE_SUFFIX = [("london", ".L"), ("xetra", ".DE"), ("deutsche b", ".DE"), ("frankfurt", ".DE"),
                   ("amsterdam", ".AS"), ("paris", ".PA"), ("brussels", ".BR"), ("lisbon", ".LS"),
                   ("italiana", ".MI"), ("milan", ".MI"), ("madrid", ".MC"), ("bolsa", ".MC"), ("swiss", ".SW"),
                   ("copenhagen", ".CO"), ("stockholm", ".ST"), ("helsinki", ".HE"), ("oslo", ".OL"),
                   ("irish", ".IR"), ("dublin", ".IR"), ("wiener", ".VI"), ("vienna", ".VI"), ("warsaw", ".WA")]
COUNTRY_SUFFIX = {"United Kingdom": ".L", "Germany": ".DE", "France": ".PA", "Netherlands": ".AS",
                  "Switzerland": ".SW", "Denmark": ".CO", "Sweden": ".ST", "Finland": ".HE", "Norway": ".OL",
                  "Spain": ".MC", "Italy": ".MI", "Belgium": ".BR", "Portugal": ".LS", "Ireland": ".IR",
                  "Austria": ".VI", "Poland": ".WA"}
COUNTRY_EN = {"Deutschland": "Germany", "Frankreich": "France", "Niederlande": "Netherlands", "Schweiz": "Switzerland",
              "Dänemark": "Denmark", "Schweden": "Sweden", "Finnland": "Finland", "Norwegen": "Norway",
              "Spanien": "Spain", "Italien": "Italy", "Belgien": "Belgium", "Irland": "Ireland",
              "Österreich": "Austria", "Polen": "Poland", "Vereinigtes Königreich": "United Kingdom"}


def stoxx600_members():
    """[(Yahoo symbol, country)] of the STOXX Europe 600, from the ETF's holdings file."""
    last = None
    for url in STOXX600_HOLDINGS:
        try:
            raw = text(url)
        except Exception as e:  # noqa: BLE001  the other site may answer
            last = e
            if PROBE:
                print(f"    {url[:70]}... failed: {type(e).__name__}: {e}")
            continue
        lines = raw.lstrip("\ufeff").splitlines()
        # The English file separates with commas, the German one with semicolons.
        head = next((i for i, ln in enumerate(lines) if re.search(r'(^|[,;])"?(Ticker|Emittententicker)"?[,;]', ln)), None)
        if head is None and raw.lstrip().lower().startswith("<!doctype html"):
            # A plain .csv file first; never the address that served this page.
            found = [h for h, _ in links(raw, url) if HOLDINGS_LINK.search(h) and h.split("#")[0] != url]
            found.sort(key=lambda h: not h.split("?")[0].endswith(".csv"))
            if PROBE:
                hrefs = sorted({h for h, t in links(raw, url) if re.search(r"csv|xls|holding|download|bestand|positionen",
                                                                          h + " " + t, re.I)})
                print(f"    {url[:70]}... served the fund page; download-like links: {hrefs[:12]}")
            if found:
                try:
                    raw = text(found[0])
                except Exception as e:  # noqa: BLE001
                    last = e
                    continue
                lines = raw.lstrip("\ufeff").splitlines()
                head = next((i for i, ln in enumerate(lines)
                             if re.search(r'(^|[,;])"?(Ticker|Emittententicker)"?[,;]', ln)), None)
        if head is None:
            if PROBE:
                print(f"    {url[:70]}... answered: " + re.sub(r"\s+", " ", raw[:400]))
            last = ValueError(f"{url}: no holdings table")
            continue
        sep = ";" if lines[head].count(";") > lines[head].count(",") else ","
        reader = csv.DictReader(io.StringIO("\n".join(lines[head:])), delimiter=sep)
        out = []
        for r in reader:
            tick = (r.get("Ticker") or r.get("Emittententicker") or "").strip()
            kind = (r.get("Asset Class") or r.get("Anlageklasse") or "").strip()
            if not tick or (kind and kind not in ("Equity", "Aktien")):
                continue
            country = COUNTRY_EN.get((r.get("Location") or r.get("Standort") or "").strip(),
                                     (r.get("Location") or r.get("Standort") or "").strip())
            exch = (r.get("Exchange") or r.get("Börse") or "").lower()
            suffix = next((sx for key, sx in EXCHANGE_SUFFIX if key in exch), None) or COUNTRY_SUFFIX.get(country)
            if not suffix:
                continue
            sym = re.sub(r"[ /]+", "-", tick.rstrip(".")) + suffix
            out.append((sym, country))
        if len(out) >= 500:
            return out
        last = ValueError(f"{url}: only {len(out)} equity holdings")
    raise last or ValueError("no holdings file")


# Asia: Yahoo Finance's screener ranks each market by market cap; the top 20
# companies across the six markets, one listing each.
ASIA = {"jp": "Japan", "tw": "Taiwan", "kr": "South Korea", "hk": "Hong Kong", "cn": "China", "in": "India"}
# Companies whose primary listing is London, quoted in Hong Kong: they belong to
# Europe's list (STOXX Europe 600), not Asia's. Yahoo has no primary-listing flag.
NOT_PRIMARY = {"0005.HK": "HSBC Holdings, London", "2888.HK": "Standard Chartered, London",
               "2378.HK": "Prudential, London"}
SUFFIX_COUNTRY = {".T": "Japan", ".TW": "Taiwan", ".TWO": "Taiwan", ".KS": "South Korea", ".KQ": "South Korea",
                  ".HK": "Hong Kong", ".SS": "China", ".SZ": "China", ".NS": "India", ".BO": "India"}


def suffix(sym):
    return "." + sym.rsplit(".", 1)[1] if "." in sym else ""


def pick_listing(group):
    """One listing per company (owner's rules, 22 Oct 2026): the mainland A-share
    for companies listed in mainland China and Hong Kong; the Hong Kong listing
    for a Chinese company whose primary listing is in New York (only its Asian
    listings are screened); NSE over BSE in India; otherwise the largest."""
    mainland = [q for q in group if suffix(q["symbol"]) in (".SS", ".SZ")]
    if mainland:
        return max(mainland, key=lambda q: q["_usd"])
    nse = [q for q in group if suffix(q["symbol"]) == ".NS"]
    if nse:
        return max(nse, key=lambda q: q["_usd"])
    return max(group, key=lambda q: q["_usd"])


def asia_universe(yahoo, n=20):
    found = []
    for region in ASIA:
        found += yahoo.screener(region, 30)
    # Korean preferred shares trade under codes not ending in 0 (005935 for Samsung).
    found = [q for q in found if not (suffix(q["symbol"]) in (".KS", ".KQ") and not q["symbol"].split(".")[0].endswith("0"))
             and q["symbol"] not in NOT_PRIMARY]
    rates = usd_rates(yahoo, [q.get("currency") for q in found])
    groups = {}
    for q in found:
        q["_usd"] = usd_cap(q, rates)
        if q["_usd"]:
            groups.setdefault(company(q.get("longName") or q.get("shortName") or q["symbol"]), []).append(q)
    picked = sorted((pick_listing(g) for g in groups.values()), key=lambda q: -q["_usd"])[:n]
    if len(picked) < n:
        raise ValueError(f"Yahoo screener: only {len(picked)} Asian companies")
    # Yahoo gives some NSE lines no market cap, so an Indian company can rank on
    # its BSE line; the NSE listing is still the one shown.
    nse = {q["symbol"]: q["symbol"][:-3] + ".NS" for q in picked if q["symbol"].endswith(".BO")}
    full = {q["symbol"]: q for q in yahoo.quotes([q["symbol"] for q in picked] + list(nse.values()))}
    out = []
    for q in picked:
        alt = full.get(nse.get(q["symbol"], ""))
        f = alt if alt and alt.get("regularMarketPrice") else full.get(q["symbol"], q)
        f["_usd"], f["_country"] = q["_usd"], SUFFIX_COUNTRY.get(suffix(q["symbol"]), "")
        out.append(f)
    return out


def europe_universe(cache, yahoo, n=50):
    try:
        members = stoxx600_members()
        cache["stoxx600"] = {"members": members, "ok": dt.datetime.now(UTC).isoformat(timespec="seconds"), "error": None}
    except Exception as e:  # noqa: BLE001
        members = (cache.get("stoxx600") or {}).get("members")
        log(f"stoxx600: {type(e).__name__}: {e}; using the last good list ({(cache.get('stoxx600') or {}).get('ok')})", "warning")
        cache.setdefault("stoxx600", {})["error"] = f"{type(e).__name__}: {e}"[:200]
        if not members:
            raise ValueError("no STOXX Europe 600 membership list yet") from e
    country = dict((s, c) for s, c in members)
    quotes = yahoo.quotes(list(country))
    rates = usd_rates(yahoo, [q.get("currency") for q in quotes])
    groups = {}
    for q in quotes:
        q["_usd"] = usd_cap(q, rates)
        if q["_usd"]:
            q["_country"] = "UK" if country[q["symbol"]] == "United Kingdom" else country[q["symbol"]]
            groups.setdefault(company(q.get("longName") or q.get("shortName") or q["symbol"]), []).append(q)
    top = sorted((max(g, key=lambda q: q["_usd"]) for g in groups.values()), key=lambda q: -q["_usd"])[:n]
    if PROBE:
        print(f"    STOXX Europe 600: {len(members)} holdings, {len(quotes)} on Yahoo; top {n}:")
        for i, q in enumerate(top, 1):
            print(f"      {i:2} {q['symbol']:<12} {q.get('exchange', ''):<4} {q.get('longName') or q.get('shortName')}"
                  f" (${q['_usd'] / 1e9:,.0f}bn)")
    return top


def us_universe(cache, yahoo, n=100):
    try:
        members = spy_members()
        cache["spy"] = {"tickers": members, "ok": dt.datetime.now(UTC).isoformat(timespec="seconds"), "error": None}
    except Exception as e:  # noqa: BLE001
        members = (cache.get("spy") or {}).get("tickers")
        log(f"spy: {type(e).__name__}: {e}; using the last good list ({(cache.get('spy') or {}).get('ok')})", "warning")
        cache.setdefault("spy", {})["error"] = f"{type(e).__name__}: {e}"[:200]
        if not members:
            raise ValueError("no S&P 500 membership list yet") from e
    quotes = [q for q in yahoo.quotes(members) if q.get("marketCap")]
    quotes.sort(key=lambda q: -q["marketCap"])
    top, seen = [], set()
    for q in quotes:
        key = company(q.get("longName") or q.get("shortName") or q["symbol"])
        if key in seen:
            continue
        seen.add(key)
        q["_country"] = "US"
        top.append(q)
        if len(top) == n:
            break
    cache["top100"] = [q["symbol"] for q in top]
    return top


# Exchange sessions, local wall clock (open, close). Yahoo dates European and
# Asian reports at the exchange's close when it has no time, so a time exactly
# on the close reads "Time not given" (owner's rule, 22 Oct 2026).
SESSIONS = {"LSE": ((8, 0), (16, 30)), "IOB": ((8, 0), (16, 30)), "GER": ((9, 0), (17, 30)), "FRA": ((9, 0), (17, 30)),
            "PAR": ((9, 0), (17, 30)), "AMS": ((9, 0), (17, 30)), "BRU": ((9, 0), (17, 30)), "LIS": ((9, 0), (17, 30)),
            "MIL": ((9, 0), (17, 30)), "MCE": ((9, 0), (17, 30)), "EBS": ((9, 0), (17, 30)), "VTX": ((9, 0), (17, 30)),
            "VIE": ((9, 0), (17, 30)), "ISE": ((8, 0), (16, 30)), "CPH": ((9, 0), (17, 0)), "STO": ((9, 0), (17, 30)),
            "HEL": ((10, 0), (18, 30)), "OSL": ((9, 0), (16, 20)), "WSE": ((9, 0), (17, 0)),
            "JPX": ((9, 0), (15, 30)), "TAI": ((9, 0), (13, 30)), "TWO": ((9, 0), (13, 30)), "KSC": ((9, 0), (15, 30)),
            "KOE": ((9, 0), (15, 30)), "HKG": ((9, 30), (16, 0)), "SHH": ((9, 30), (15, 0)), "SHZ": ((9, 30), (15, 0)),
            "NSI": ((9, 15), (15, 30)), "BSE": ((9, 15), (15, 30))}
CLOSE_STAMPS = {"HKG": {(16, 10)}}  # Hong Kong's closing auction ends at 16:10
BENCH = {"us": ("^GSPC", "S&P 500"), "europe": ("^STOXX", "STOXX Europe 600"),
         "Japan": ("^N225", "Nikkei 225"), "Taiwan": ("^TWII", "TAIEX"), "South Korea": ("^KS11", "KOSPI"),
         "Hong Kong": ("^HSI", "Hang Seng"), "China": ("000300.SS", "CSI 300"), "India": ("^NSEI", "Nifty 50")}


def report_timing(q, market, estimated, stamp_ny):
    """'before', 'after' or 'none' for the open and close of the company's own market."""
    if estimated:
        return "none"
    if market == "us":
        if (stamp_ny.hour, stamp_ny.minute) <= (9, 30):
            return "before"
        return "after" if stamp_ny.hour >= 16 else "none"
    hours = SESSIONS.get(q.get("exchange"))
    tz = q.get("exchangeTimezoneName")
    if not hours or not tz:
        return "none"
    local = stamp_ny.astimezone(ZoneInfo(tz))
    hm = (local.hour, local.minute)
    if hm == (0, 0) or hm == hours[1] or hm in CLOSE_STAMPS.get(q.get("exchange"), ()):
        return "none"
    return "before" if hm < hours[0] else "after" if hm > hours[1] else "none"


def report_events(src, quotes, market, high):
    """One row per company with a report date in the window."""
    ev = Events(src)
    for rank, q in enumerate(quotes):
        ts = q.get("earningsTimestampStart") or q.get("earningsTimestamp")
        if not ts:
            continue
        stamp = dt.datetime.fromtimestamp(ts, UTC).astimezone(NY)
        end = q.get("earningsTimestampEnd")
        estimated = bool(q.get("isEarningsDateEstimate")) or (end and end != ts) or q.get("isEarningsDateEstimate") is None
        timing = report_timing(q, market, estimated, stamp)
        tz = q.get("exchangeTimezoneName") or "America/New_York"
        local_day = stamp.astimezone(ZoneInfo(tz)).date()
        # A known time places the row on its New York day; otherwise the market's own date.
        day = stamp.date() if timing != "none" else local_day
        if not in_window(day):
            continue
        name = html.unescape(q.get("longName") or q.get("shortName") or q["symbol"])
        country = q.get("_country") or "US"
        bench = BENCH["us" if market == "us" else "europe" if market == "europe" else country]
        ev.add(day, f"{name}, {q['symbol']}", country=country, imp="High" if rank < high else "Medium", kind="earnings",
               timing=timing, url=f"https://finance.yahoo.com/quote/{q['symbol']}/financials/",
               extra={"ticker": q["symbol"], "company": name, "status": "estimated" if estimated else "confirmed",
                      "rank": rank + 1, "market": market, "local_day": local_day.isoformat(), "tz": tz,
                      "stamp": stamp.isoformat() if timing != "none" else None,
                      "currency": major(q.get("financialCurrency") or q.get("currency")) or "USD",
                      "bench": bench[0], "bench_name": bench[1]})
    return ev.items


EARNINGS = [  # (source key, market, universe, rows marked High)
    ("earnings", "us", lambda cache, y: us_universe(cache, y), 25),
    ("earnings_europe", "europe", lambda cache, y: europe_universe(cache, y), 12),
    ("earnings_asia", "asia", lambda cache, y: asia_universe(y), 5),
]


def quarter_ends(obs):
    """Known quarter ends plus the next two, from a company's EPS history."""
    ends = [d for d, _ in obs]
    if ends:
        last = ends[-1]
        for k in (1, 2):
            m = last.month + 3 * k
            y = last.year + (m - 1) // 12
            m = (m - 1) % 12 + 1
            ends.append(dt.date(y, m, cal.monthrange(y, m)[1]))
    return ends


def near(obs, day, days):
    hits = [(abs((d - day).days), d, v) for d, v in obs if abs((d - day).days) <= days]
    return min(hits)[1:] if hits else None


def year_before(d):
    return d.replace(year=d.year - 1) if not (d.month == 2 and d.day == 29) else d - dt.timedelta(days=366)


def period_end(day, fye_month):
    """The fiscal period a report on day covers: the last quarter end (in the
    company's fiscal calendar) at least ten days before it."""
    ends = []
    for y in (day.year - 1, day.year):
        for k in range(4):
            m = (fye_month + 3 * k - 1) % 12 + 1
            ends.append(dt.date(y, m, cal.monthrange(y, m)[1]))
    ends = [d for d in ends if d <= day - dt.timedelta(days=10)]
    return max(ends) if ends else None


def report_type(qobs, aobs, end):
    """The report type, inferred from the periods Yahoo holds EPS for (owner's
    rule, 22 Oct 2026); None when the history does not settle it.

    A company with annual EPS and no quarterly EPS reports in full twice a year:
    its year end is full-year results, six months on half-year results, the
    quarters between trading updates. A company with EPS for at least three of
    the six quarters before the period reports every quarter."""
    if not aobs or not end:
        return None
    fye = aobs[-1][0].month
    if not qobs:
        gap = (end.month - fye) % 12
        return {0: "Full-year results", 6: "Half-year results", 3: "Trading update", 9: "Trading update"}.get(gap)
    recent = {(d.year, d.month) for d, _ in qobs if dt.timedelta(0) <= end - d <= dt.timedelta(days=550)}
    return "Quarterly results" if len(recent) >= 3 else None


def earnings_values(events, yahoo, now):
    """Report type, year-ago diluted EPS, and the reported figure once Yahoo has it,
    in the company's reporting currency."""
    for e in events:
        if e.get("kind") != "earnings" or "actual" in e:
            continue
        day = dt.date.fromisoformat(e.get("local_day") or e["date"])
        if (now.date() - day).days > 21:
            continue
        try:
            qobs, aobs, cur = yahoo.eps(e["ticker"])
        except Exception as err:  # noqa: BLE001
            log(f"eps {e['ticker']}: {type(err).__name__}: {err}", "warning")
            continue
        fye = aobs[-1][0].month if aobs else (qobs[-1][0].month if qobs else 12)
        end = period_end(day, fye)
        kind = report_type(qobs, aobs, end)
        if kind:
            e["report_type"] = kind
        code = cur or e.get("currency") or ""
        cur = "" if e.get("market", "us") == "us" else f" {code}".rstrip()
        dec = 0 if code == "KRW" else 2
        series, label = (aobs, "year") if kind == "Full-year results" and not qobs else (qobs, "quarter")
        if kind in ("Half-year results", "Trading update") or not end:
            continue  # Yahoo holds no half-year or interim EPS
        ago = near(series, year_before(end), 20)
        if ago:
            e["previous"] = f"EPS {unsigned(ago[1], dec)}{cur}"
            e["prev_period"] = f"{label} to {cal.month_abbr[ago[0].month]} {ago[0].year}"
        if now.date() >= day:
            got = near(series, end, 10)
            if got:
                e["actual"], e["actual_seen"] = f"EPS {unsigned(got[1], dec)}{cur}", now.isoformat(timespec="seconds")


def first_session(closes, day, timing):
    """Index of the first full session after a report on day: that day's session
    for a report before the open, the next one otherwise (owner's rule when the
    time is not given, 22 Oct 2026)."""
    for i, (d, _) in enumerate(closes):
        if (d >= day if timing == "before" else d > day) and i > 0:
            return i
    return None


def reactions(events, now):
    """The stock's move on the first full session after its report, and the same
    session's move of its benchmark, from Yahoo Finance daily closes. A session
    still trading is left out, so a move is only ever a close-to-close move."""
    from dashboard_data import yahoo as closes_of
    charts = {}

    def closes(sym):
        if sym not in charts:
            try:
                charts[sym] = closes_of(sym, "1mo")
            except Exception as err:  # noqa: BLE001
                log(f"reaction {sym}: {type(err).__name__}: {err}", "warning")
                charts[sym] = []
        return charts[sym]

    for e in events:
        if e.get("kind") != "earnings" or e.get("reaction"):
            continue
        day = dt.date.fromisoformat(e.get("local_day") or e["date"])
        if day > now.date() or (now.date() - day).days > 14:
            continue
        stock = closes(e["ticker"])
        i = first_session(stock, day, e.get("timing") or "none")
        if i is None:
            continue
        session, move = stock[i][0], (stock[i][1] / stock[i - 1][1] - 1) * 100
        bench = closes(e.get("bench") or "^GSPC")
        days = [d for d, _ in bench]
        bmove = None
        if session in days:
            j = days.index(session)
            if j > 0:
                bmove = (bench[j][1] / bench[j - 1][1] - 1) * 100
        e["reaction"] = {"session": session.isoformat(), "move": round(move, 2), "bench": e.get("bench_name", "S&P 500"),
                         "bench_move": round(bmove, 2) if bmove is not None else None}


# Merge and write ----------------------------------------------------------------

KEEP = ("previous", "prev_period", "actual", "actual_seen", "actual_url", "base", "report_type", "reaction")


def merge(cache, src, fresh, now):
    """Replace a source's events from today on with a fresh copy; past events stay."""
    events = cache.setdefault("events", {})
    today = now.astimezone(NY).date().isoformat()
    ids = {e["id"] for e in fresh}
    for k in [k for k, e in events.items() if e.get("fetched_by", e["src"]) == src and e["date"] >= today and k not in ids]:
        del events[k]
    for e in fresh:
        old = events.get(e["id"], {})
        e.update({k: old[k] for k in KEEP if k in old})
        e["fetched_by"] = src
        events[e["id"]] = e


def main():
    now = dt.datetime.now(UTC)
    path = CACHE
    try:
        cache = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    if PROBE:
        path = CACHE.with_name("probe.json")
    today, start, _ = window()
    cache.setdefault("first_week", start.isoformat())
    status = cache.setdefault("sources", {})
    for key, meta in SOURCES.items():
        if not meta["fn"]:
            continue
        LAST.clear()
        try:
            fresh = meta["fn"]()
            if not fresh and key in EXPECTED:
                raise ValueError("no events found; the page may have changed")
        except Exception as e:  # noqa: BLE001  one source failing never empties the calendar
            st = status.setdefault(key, {})
            st["error"] = f"{type(e).__name__}: {e}"[:300]
            log(f"{key}: {st['error']}; keeping the last good copy ({st.get('ok') or 'none'})", "warning")
            if PROBE and LAST:
                print(snippets(key) if key in PROBE_KEYS else excerpt())
            continue
        merge(cache, key, fresh, now)
        status[key] = {"ok": now.isoformat(timespec="seconds"), "error": None, "n": len(fresh)}
        print(f"{key}: {len(fresh)} events")
        if PROBE:
            for e in fresh[:6]:
                print("   ", e["date"], e.get("utc") or "all day", e["title"], e.get("ref") or "")
            if LAST and len(fresh) < 3:
                print(snippets(key) if key in PROBE_KEYS else excerpt())
    yahoo = None
    try:
        yahoo = Yahoo()
    except Exception as e:  # noqa: BLE001
        log(f"Yahoo Finance: {type(e).__name__}: {e}; earnings keep their last good copy", "warning")
    for key, market, universe, high in EARNINGS if yahoo else []:
        # Each market keeps its own last good copy.
        try:
            quotes = universe(cache, yahoo)
            fresh = report_events(key, quotes, market, high)
            if not fresh:
                raise ValueError("no reports in the window")
            merge(cache, key, fresh, now)
            status[key] = {"ok": now.isoformat(timespec="seconds"), "error": None, "n": len(fresh)}
            print(f"{key}: {len(fresh)} reports from the top {len(quotes)}")
            if PROBE:
                for e in sorted(fresh, key=lambda e: e["date"])[:6]:
                    print("   ", e["date"], e["timing"], e["status"], e["country"], e["title"])
        except Exception as e:  # noqa: BLE001
            st = status.setdefault(key, {})
            st["error"] = f"{type(e).__name__}: {e}"[:300]
            log(f"{key}: {st['error']}; keeping the last good copy ({st.get('ok') or 'none'})", "warning")
    events = list(cache.get("events", {}).values())
    live = [e for e in events if (now.date() - dt.date.fromisoformat(e["date"])).days <= 10]
    fetch_values(cache, {e["ind"] for e in live if e.get("ind") in IND})
    for e in live:
        try:
            resolve(e, cache["values"], now)
        except Exception as err:  # noqa: BLE001  a bad figure never stops the calendar
            log(f"values for {e['id']}: {type(err).__name__}: {err}", "warning")
        if e.get("ind") in IND:
            e["value_source"] = value_source(e["ind"])
    try:
        auction_values(live, now)
    except Exception as e:  # noqa: BLE001
        log(f"treasury yields: {type(e).__name__}: {e}", "warning")
    if yahoo:
        earnings_values(live, yahoo, now)
    reactions([e for e in events if e.get("kind") == "earnings"], now)
    cache["updated"] = now.isoformat(timespec="seconds")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=1, sort_keys=True), encoding="utf-8")
    bad = [k for k, s in status.items() if s.get("error")]
    print(f"{len(cache['events'])} events stored; sources failing this run: {', '.join(bad) or 'none'}")
    if PROBE:
        for ind, v in sorted(cache.get("values", {}).items()):
            print(f"  value {ind}: {v.get('error') or (v['obs'][-1] if v['obs'] else 'empty')}")


if __name__ == "__main__":
    main()
