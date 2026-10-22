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
import datetime as dt
import html
import io
import json
import os
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


def excerpt():
    """What the last page said, for the probe log."""
    body = LAST.get("body") or ""
    t = re.sub(r"\s+", " ", strip(body))
    return f"    last page {LAST.get('url')} ({len(body)} bytes): {t[:1500]}"


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
                start = d.replace(tzinfo=ZoneInfo(tzid.strip('"') if tzid else "America/New_York"))
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
    try:
        for start, summary, desc, _ in ics_events(text("https://www.bls.gov/schedule/news_release/bls.ics", ua=BOT)):
            found.append((start, f"{summary} {desc}"))
    except Exception as e:  # noqa: BLE001  the monthly schedule pages say the same
        log(f"bls: calendar file failed ({type(e).__name__}: {e}); reading the schedule pages", "warning")
        today, start, end = window()
        months = sorted({(d.year, d.month) for d in (start, today, end)})
        for y, m in months:
            page = text(f"https://www.bls.gov/schedule/{y}/{m:02d}_sched_list.htm", ua=BOT)
            for r in rows(page):
                dm = re.search(r"([A-Z][a-z]+day), ([A-Z][a-z]+) (\d{1,2}), (\d{4})", r)
                hm = parse_clock(r)
                if dm and hm and month_num(dm.group(2)):
                    d = dt.date(int(dm.group(4)), month_num(dm.group(2)), int(dm.group(3)))
                    found.append((dt.datetime(d.year, d.month, d.day, *hm, tzinfo=NY), r))
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
    return ev.items


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
    ev = Events("census")
    page = text("https://www.census.gov/economic-indicators/calendar-listview.html")
    for r in rows(page):
        for prefix, title, imp, ind, url in CENSUS:
            if prefix.lower() not in r.lower():
                continue
            dm = re.search(r"\b([A-Z][a-z]+)\.? (\d{1,2}),? (\d{4})\b", r) or re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", r)
            if not dm:
                continue
            if dm.group(1).isdigit():
                day = dt.date(int(dm.group(3)), int(dm.group(1)), int(dm.group(2)))
            elif month_num(dm.group(1)):
                day = dt.date(int(dm.group(3)), month_num(dm.group(1)), int(dm.group(2)))
            else:
                continue
            if not in_window(day):
                continue
            ref = None
            rm = re.search(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b(?! \d{1,2},)", r)
            if rm:
                m = month_num(rm.group(1))
                y = day.year if m <= day.month else day.year - 1
                ref = f"{y}-{m:02d}"
            # Census releases at 8:30 am ET, new home sales at 10:00 am, when the row gives no time.
            hm = parse_clock(r) or ((10, 0) if ind == "nhs" else (8, 30))
            ev.add(day, f"{title}, {period_label(ref)}" if ref else title, country="US", imp=imp,
                   when=hm, tz="America/New_York", ind=ind, ref=ref, url=url)
            break
    return ev.items


def g17():
    """Industrial production, Federal Reserve G.17, 9:15 am ET."""
    ev = Events("fed_g17")
    page = text("https://www.federalreserve.gov/releases/g17/release_dates.htm")
    for m in re.finditer(r"\b([A-Z][a-z]+)\.? (\d{1,2}), (\d{4})", strip(page)):
        if not month_num(m.group(1)):
            continue
        day = dt.date(int(m.group(3)), month_num(m.group(1)), int(m.group(2)))
        if in_window(day):
            ev.add(day, "Industrial production", country="US", imp="Medium", when=(9, 15),
                   tz="America/New_York", ind="ip", url="https://www.federalreserve.gov/releases/g17/current/default.htm")
    # The page also lists past dates; one entry per day.
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


FED_SPEAKERS = [("Chair", "High"), ("Vice Chair for Supervision", "Medium"), ("Vice Chair", "Medium")]


def fed_speeches():
    """Speeches by the Chair and Vice Chairs from the Board's calendar."""
    ev = Events("fed_speeches")
    _, start, end = window()
    months = sorted({(d.year, d.month) for d in (start, start + dt.timedelta(days=14), end)})
    for y, m in months:
        page = text(f"https://www.federalreserve.gov/newsevents/{y}-{cal.month_name[m].lower()}.htm")
        for block in re.split(r'(?i)<div class="row(?: [^"]*)?">', page)[1:]:
            t = strip(block[:4000])
            if "Speech" not in t:
                continue
            who = next(((role, imp) for role, imp in FED_SPEAKERS if re.search(rf"\b{role}\b", t)), None)
            if not who or "Governor" in t.split("Speech")[0] and who[0] == "Chair":
                continue
            dm = re.search(r"\b([A-Z][a-z]+)\.? (\d{1,2}), (\d{4})", t) or re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})", t)
            if not dm:
                continue
            day = (dt.date(int(dm.group(3)), month_num(dm.group(1)), int(dm.group(2)))
                   if not dm.group(1).isdigit() else dt.date(int(dm.group(3)), int(dm.group(1)), int(dm.group(2))))
            if not in_window(day):
                continue
            name = re.search(r"(Chair|Vice Chair(?: for Supervision)?) ([A-Z][A-Za-z.\- ]+?)(?:\s{2,}| at | to |,|$)", t)
            title = f"Speech by Fed {name.group(1)} {name.group(2).strip()}" if name else f"Speech by Fed {who[0]}"
            ev.add(day, title, country="US", imp=who[1], when=parse_clock(t), tz="America/New_York")
    return ev.items


def treasury():
    ev = Events("treasury")
    data = json.loads(text("https://www.treasurydirect.gov/TA_WS/securities/upcoming?format=json"))
    for s in data:
        kind = s.get("securityType", "")
        if kind not in ("Note", "Bond") or (s.get("floatingRate") or "").lower() == "yes":
            continue
        day = dt.date.fromisoformat(s["auctionDate"][:10])
        if not in_window(day):
            continue
        term = s.get("securityTerm", "").replace("-Year", "-year").replace("-Month", "-month")
        tips = (s.get("inflationIndexSecurity") or "").lower() == "yes"
        title = f"{term} {'TIPS' if tips else kind.lower()} auction"
        if (s.get("reopening") or "").lower() == "yes":
            title += ", reopening"
        close = parse_clock(s.get("closingTimeCompetitive") or "") or (13, 0)
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
    ("Flash US", "US", "S&P Global flash US PMIs", "High"),
    ("Flash Eurozone", "Euro area", "HCOB flash euro area PMIs", "High"),
    ("Flash UK", "UK", "S&P Global flash UK PMIs", "High"),
    ("Flash Japan", "Japan", "S&P Global flash Japan PMIs", "Medium"),
    ("China General Manufacturing", "China", "RatingDog China manufacturing PMI", "Medium"),
    ("China General Services", "China", "RatingDog China services PMI", "Medium"),
]


def pmi():
    ev = Events("spglobal")
    page = text("https://www.pmi.spglobal.com/Public/Release/ReleaseDates")
    for r in rows(page):
        hit = next((p for p in PMI if p[0].lower() in r.lower()), None)
        if not hit:
            continue
        dm = re.search(r"\b(\d{1,2})[ /-]([A-Za-z]{3,9}|\d{1,2})[ /-](\d{4})\b", r) or re.search(r"\b([A-Z][a-z]+) (\d{1,2}),? (\d{4})", r)
        if not dm:
            continue
        a, b, y = dm.group(1), dm.group(2), int(dm.group(3))
        if a.isdigit():
            day = dt.date(y, month_num(b) if not b.isdigit() else int(b), int(a))
        else:
            day = dt.date(y, month_num(a), int(b))
        if not in_window(day):
            continue
        hm = parse_clock(r)
        ev.add(day, hit[2], country=hit[1], imp=hit[3], when=hm, tz="UTC",
               url="https://www.pmi.spglobal.com/Public/Release/ReleaseDates")
    return list({e["id"]: e for e in ev.items}.values())


def conference_board():
    ev = Events("conference_board")
    page = strip(text("https://www.conference-board.org/topics/consumer-confidence"))
    for m in re.finditer(r"([A-Z][a-z]+), ([A-Z][a-z]+) (\d{1,2}), (\d{4})(?:,? (?:at )?(\d{1,2}(?::\d{2})? ?[ap]\.?m\.?))?", page):
        if not month_num(m.group(2)):
            continue
        day = dt.date(int(m.group(4)), month_num(m.group(2)), int(m.group(3)))
        ctx = page[max(0, m.start() - 80):m.start()].lower()
        if in_window(day) and "release" in ctx:
            ev.add(day, "Consumer confidence (Conference Board)", country="US", imp="High",
                   when=parse_clock(m.group(5) or "") or (10, 0), tz="America/New_York")
    return list({e["id"]: e for e in ev.items}.values())


def umich():
    ev = Events("umich")
    page = text("https://www.sca.isr.umich.edu/")
    today = window()[0]
    t = strip(page)
    for m in re.finditer(r"(Preliminary|Final)[^.]{0,80}?([A-Z][a-z]+) (\d{1,2})(?:, (\d{4}))?", t):
        if not month_num(m.group(2)):
            continue
        day = (dt.date(int(m.group(4)), month_num(m.group(2)), int(m.group(3))) if m.group(4)
               else nearest_year(month_num(m.group(2)), int(m.group(3)), today))
        if in_window(day):
            ev.add(day, f"Consumer sentiment, {m.group(1).lower()} (University of Michigan)", country="US",
                   imp="Medium", when=(10, 0), tz="America/New_York", ind="umich")
    return list({e["id"]: e for e in ev.items}.values())


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
    ev = Events("ecb_speeches")
    page = text("https://www.ecb.europa.eu/press/calendars/weekly/html/index.en.html")
    for d, what in re.findall(r"(?is)<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", page):
        dm = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", strip(d))
        t = strip(what)
        if not dm or "Lagarde" not in t or not re.search(r"speech|remarks|address|testimony|hearing", t, re.I):
            continue
        day = dt.date(int(dm.group(3)), int(dm.group(2)), int(dm.group(1)))
        if in_window(day):
            hm = parse_clock(t)
            title = "ECB President Lagarde testifies" if re.search(r"hearing|testimony", t, re.I) else "Speech by ECB President Lagarde"
            ev.add(day, title, country="Euro area", imp="Medium", when=hm, tz="Europe/Berlin")
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
    try:
        q = urllib.parse.urlencode({"limit": 200, "release-type": "type-upcoming,type-published",
                                    "fromDate": start.isoformat(), "toDate": end.isoformat()})
        data = json.loads(text(f"https://api.beta.ons.gov.uk/v1/search/releases?{q}"))
        for r in data.get("releases", []):
            d = r.get("description", {})
            found.append((d.get("release_date") or r.get("release_date"), d.get("title") or r.get("title"),
                          r.get("uri")))
    except Exception as e:  # noqa: BLE001
        log(f"ons: search API failed ({type(e).__name__}: {e}); reading the release calendar page", "warning")
        page = text("https://www.ons.gov.uk/releasecalendar?" + urllib.parse.urlencode(
            {"release-type": "type-upcoming", "after-date": start.isoformat(), "before-date": end.isoformat(),
             "limit": 100}))
        for item in re.findall(r"(?is)<li\b.*?</li>", page):
            t = strip(item)
            dm = re.search(r"(\d{1,2}) ([A-Z][a-z]+) (\d{4})(?: (\d{1,2}:\d{2}) ?([ap]m)?)?", t)
            link = re.search(r'href="(/releases/[^"]+)"', item)
            if dm and month_num(dm.group(2)):
                found.append((f"{dm.group(3)}-{month_num(dm.group(2)):02d}-{int(dm.group(1)):02d}T07:00:00+00:00", t,
                              link.group(1) if link else None))
    for when, title, uri in found:
        if not when or not title:
            continue
        hit = next((x for x in ONS if title.startswith(x[0])), None)
        if not hit:
            continue
        stamp = dt.datetime.fromisoformat(when.replace("Z", "+00:00"))
        local = stamp.astimezone(ZoneInfo("Europe/London"))
        if not in_window(local.date()):
            continue
        tail = title.split(":", 1)[1] if ":" in title else ""
        ref = ref_quarter(tail) or (ref_month(tail) if hit[3] in ("uk_cpi", "uk_gdpm", None) else None)
        hm = (local.hour, local.minute) if (local.hour, local.minute) != (0, 0) else (7, 0)
        ev.add(local.date(), f"{hit[1]}, {period_label(ref)}" if ref else hit[1], country="UK", imp=hit[2],
               when=hm, tz="Europe/London", ind=hit[3], ref=ref,
               url=f"https://www.ons.gov.uk{uri}" if uri else None)
    return list({e["id"]: e for e in ev.items}.values())


def boj():
    ev = Events("boj")
    page = text("https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm")
    url = "https://www.boj.or.jp/en/mopo/mpmsche_minu/index.htm"
    for r in rows(page):
        # "October 29 (Thu.), 30 (Fri.)" or "Apr. 30 (Thu.), May 1 (Fri.)"; the year is in the table caption.
        y = re.search(r"\b(20\d\d)\b", r)
        dates = re.findall(r"\b([A-Z][a-z]{2,8})\.? (\d{1,2}) \(([A-Z][a-z]{2})\.?\)(?:, (\d{1,2}) \(([A-Z][a-z]{2})\.?\))?", r)
        if not dates:
            continue
        mon, d1, _, d2, _ = dates[0]
        if not month_num(mon):
            continue
        year = int(y.group(1)) if y else window()[0].year
        last_mon, last_day = (dates[1][0], dates[1][1]) if len(dates) > 1 and month_num(dates[1][0]) else (mon, d2 or d1)
        day = dt.date(year, month_num(last_mon), int(last_day))
        if in_window(day):
            ev.add(day, "Bank of Japan rate decision", country="Japan", imp="High", url=url,
                   extra={"no_time": True})
    return list({e["id"]: e for e in ev.items}.values())


def nbs():
    ev = Events("nbs")
    page = text("https://www.stats.gov.cn/english/PressRelease/ReleaseCalendar/")
    names = [("Gross Domestic Product", "GDP", "High"), ("Industrial Production", "Industrial production", "Medium"),
             ("Retail Sales", "Retail sales", "Medium"), ("Consumer Price", "Consumer and producer prices (CPI, PPI)", "High"),
             ("Purchasing Managers", "Official PMIs", "High"), ("Fixed Assets", "Fixed asset investment", "Medium")]
    today = window()[0]
    for r in rows(page):
        hit = next((n for n in names if n[0].lower() in r.lower()), None)
        if not hit:
            continue
        for dm in re.finditer(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{4}))?\b|\b([A-Z][a-z]+)\.? (\d{1,2})\b", r):
            if dm.group(1):
                m, d = int(dm.group(1)), int(dm.group(2))
            elif month_num(dm.group(4) or ""):
                m, d = month_num(dm.group(4)), int(dm.group(5))
            else:
                continue
            try:
                day = dt.date(int(dm.group(3)), m, d) if dm.group(3) else nearest_year(m, d, today)
            except ValueError:
                continue
            if day and in_window(day):
                hm = parse_clock(r) or ((9, 30) if hit[0] in ("Consumer Price", "Purchasing Managers") else (10, 0))
                ev.add(day, hit[1], country="China", imp=hit[2], when=hm, tz="Asia/Shanghai")
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
    "earnings": {"name": "Yahoo Finance, earnings", "url": "https://finance.yahoo.com/calendar/earnings", "fn": None},
    "spy": {"name": "State Street, SPY holdings",
            "url": "https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy", "fn": None},
}
# Sources that always have something in a five-week window: an empty answer
# means the page changed, so it counts as a failure and the last copy stays.
EXPECTED = {"bls", "census", "dol", "eurostat", "ons", "treasury", "market", "spglobal", "nbs"}


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
    "uk_gdpm": (lambda: ons_points("/economy/grossdomesticproductgdp/timeseries/ecy2/mgdp", "M"), pct("m/m")),
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
                and ((p.get("inflationIndexSecurity") or "").lower() == "yes") == e.get("tips")
                and (p.get("floatingRate") or "").lower() != "yes" and p.get("highYield")]
        before = sorted((p for p in same if p["auctionDate"][:10] < e["date"]), key=lambda p: p["auctionDate"])
        if before and "actual" not in e:
            e["previous"] = f"{float(before[-1]['highYield']):.3f}%"
        mine = [p for p in past if p.get("cusip") == e.get("cusip") and p["auctionDate"][:10] == e["date"] and p.get("highYield")]
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

    def _open(self, url):
        """Body at url, waiting and retrying when Yahoo rate-limits (429)."""
        for wait in (5, 20, 60, None):
            try:
                return self.op.open(url, timeout=45).read()
            except urllib.error.HTTPError as e:
                if e.code != 429 or wait is None:
                    raise
                time.sleep(wait)

    def json(self, url):
        sep = "&" if "?" in url else "?"
        return json.loads(self._open(f"{url}{sep}crumb={urllib.parse.quote(self.crumb)}"))

    def quotes(self, symbols):
        out = []
        for i in range(0, len(symbols), 50):
            q = urllib.parse.urlencode({"symbols": ",".join(symbols[i:i + 50])})
            out += self.json(f"https://query1.finance.yahoo.com/v7/finance/quote?{q}")["quoteResponse"]["result"]
        return out

    def eps(self, symbol):
        """[(quarter end, diluted EPS)] as reported."""
        q = urllib.parse.urlencode({"type": "quarterlyDilutedEPS", "period1": 1600000000,
                                    "period2": int(dt.datetime.now().timestamp()) + 86400})
        res = self.json(f"https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/{symbol}?{q}")
        out = []
        for r in res["timeseries"]["result"]:
            for x in r.get("quarterlyDilutedEPS") or []:
                if x and x.get("reportedValue"):
                    out.append((dt.date.fromisoformat(x["asOfDate"]), x["reportedValue"]["raw"]))
        return sorted(out)


def company(name):
    """One key per company across share classes ('Alphabet Inc.' for GOOGL and GOOG)."""
    return re.sub(r"\b(class [a-z]|cl [a-z]|inc|corp|corporation|co|plc|ltd|new)\b|[^a-z0-9 ]", "", name.lower()).strip()


def earnings(cache):
    """The next report of the 100 largest S&P 500 companies by market cap."""
    ev = Events("earnings")
    try:
        members = spy_members()
        cache["spy"] = {"tickers": members, "ok": dt.datetime.now(UTC).isoformat(timespec="seconds"), "error": None}
    except Exception as e:  # noqa: BLE001
        members = (cache.get("spy") or {}).get("tickers")
        log(f"spy: {type(e).__name__}: {e}; using the last good list ({(cache.get('spy') or {}).get('ok')})", "warning")
        cache.setdefault("spy", {})["error"] = f"{type(e).__name__}: {e}"[:200]
        if not members:
            raise ValueError("no S&P 500 membership list yet") from e
    yahoo = Yahoo()
    quotes = [q for q in yahoo.quotes(members) if q.get("marketCap")]
    quotes.sort(key=lambda q: -q["marketCap"])
    top, seen = [], set()
    for q in quotes:
        key = company(q.get("longName") or q.get("shortName") or q["symbol"])
        if key in seen:
            continue
        seen.add(key)
        top.append(q)
        if len(top) == 100:
            break
    cache["top100"] = [q["symbol"] for q in top]
    for rank, q in enumerate(top):
        ts = q.get("earningsTimestampStart") or q.get("earningsTimestamp")
        if not ts:
            continue
        stamp = dt.datetime.fromtimestamp(ts, UTC).astimezone(NY)
        end = q.get("earningsTimestampEnd")
        estimated = bool(q.get("isEarningsDateEstimate")) or (end and end != ts) or q.get("isEarningsDateEstimate") is None
        if estimated:
            timing = "none"
        elif (stamp.hour, stamp.minute) <= (9, 30):
            timing = "before"
        elif stamp.hour >= 16:
            timing = "after"
        else:
            timing = "none"
        day = stamp.date()
        if not in_window(day):
            continue
        name = (q.get("longName") or q.get("shortName") or q["symbol"]).replace("&amp;", "&")
        ev.add(day, f"{name}, {q['symbol']}", country="US", imp="High" if rank < 25 else "Medium", kind="earnings",
               timing=timing, url=f"https://finance.yahoo.com/quote/{q['symbol']}/financials/",
               extra={"ticker": q["symbol"], "company": name, "status": "estimated" if estimated else "confirmed",
                      "rank": rank + 1})
    return ev.items, yahoo


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


def earnings_values(events, yahoo, now):
    """Year-ago diluted EPS, and the reported figure once Yahoo has it."""
    for e in events:
        if e.get("kind") != "earnings" or "actual" in e:
            continue
        day = dt.date.fromisoformat(e["date"])
        if (now.date() - day).days > 21:
            continue
        try:
            obs = yahoo.eps(e["ticker"])
        except Exception as err:  # noqa: BLE001
            log(f"eps {e['ticker']}: {type(err).__name__}: {err}", "warning")
            continue
        q = max((d for d in quarter_ends(obs) if d <= day - dt.timedelta(days=10)), default=None)
        if not q:
            continue
        ago = near(obs, q.replace(year=q.year - 1) if not (q.month == 2 and q.day == 29) else q - dt.timedelta(days=366), 20)
        if ago:
            e["previous"] = f"EPS {unsigned(ago[1], 2)}"
            e["prev_period"] = f"quarter to {cal.month_abbr[ago[0].month]} {ago[0].year}"
        if now.date() >= day:
            got = near(obs, q, 10)
            if got:
                e["actual"], e["actual_seen"] = f"EPS {unsigned(got[1], 2)}", now.isoformat(timespec="seconds")


# Merge and write ----------------------------------------------------------------

KEEP = ("previous", "prev_period", "actual", "actual_seen", "actual_url", "base")


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
                print(excerpt())
            continue
        merge(cache, key, fresh, now)
        status[key] = {"ok": now.isoformat(timespec="seconds"), "error": None, "n": len(fresh)}
        print(f"{key}: {len(fresh)} events")
        if PROBE:
            for e in fresh[:4]:
                print("   ", e["date"], e.get("utc") or "all day", e["title"], e.get("ref") or "")
    yahoo = None
    try:
        fresh, yahoo = earnings(cache)
        if not fresh:
            raise ValueError("no reports in the window")
        merge(cache, "earnings", fresh, now)
        status["earnings"] = {"ok": now.isoformat(timespec="seconds"), "error": None, "n": len(fresh)}
        print(f"earnings: {len(fresh)} reports from the top {len(cache.get('top100', []))}")
    except Exception as e:  # noqa: BLE001
        st = status.setdefault("earnings", {})
        st["error"] = f"{type(e).__name__}: {e}"[:300]
        log(f"earnings: {st['error']}; keeping the last good copy ({st.get('ok') or 'none'})", "warning")
    events = list(cache.get("events", {}).values())
    live = [e for e in events if (now.date() - dt.date.fromisoformat(e["date"])).days <= 10]
    fetch_values(cache, {e["ind"] for e in live if e.get("ind") in IND})
    for e in live:
        resolve(e, cache["values"], now)
        if e.get("ind") in IND:
            e["value_source"] = value_source(e["ind"])
    try:
        auction_values(live, now)
    except Exception as e:  # noqa: BLE001
        log(f"treasury yields: {type(e).__name__}: {e}", "warning")
    if yahoo:
        earnings_values(live, yahoo, now)
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
