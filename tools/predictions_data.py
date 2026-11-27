#!/usr/bin/env python3
"""Fetch the figures behind Hedge Fund Data: Prediction markets, every 30 minutes.

Run by .github/workflows/hedgefund-data.yml. Writes .cache/hf/predictions.json
(schema "andra.predictions/1", Actions cache, never committed or published):

    markets   the most traded open markets on the questions that move markets
              (the Fed, inflation, growth, tariffs, elections, geopolitics,
              companies), from Polymarket and Kalshi: the probability the
              market gives each outcome, its change over a day, and the
              day's and the whole volume in dollars.
    history   each market's probability once a day (the first sample after
              00:00 UTC), for 120 days, so the pages can draw how the odds moved.

Both venues' public read APIs, no key. Sports and entertainment are left out.
A probability is the last traded price of a "Yes" share in dollars (0 to 1);
where nothing has traded the market is skipped rather than given a price.
A failed venue keeps its last good copy with its own date.

    python3 tools/predictions_data.py
"""
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_data import get, log  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "hf" / "predictions.json"
SCHEMA = "andra.predictions/1"

POLY = "https://gamma-api.polymarket.com/events"
# Polymarket tag slugs worth a markets page; a slug the API does not know returns nothing.
POLY_TAGS = ["fed", "fed-rates", "economy", "inflation", "finance", "business", "tariffs", "stocks",
             "commodities", "geopolitics", "politics", "elections", "crypto", "ai"]
POLY_SKIP = {"sports", "nfl", "nba", "mlb", "nhl", "soccer", "games", "pop-culture", "entertainment", "esports"}
KALSHI = "https://api.elections.kalshi.com/trade-api/v2/events"
KALSHI_KEEP = {"Economics", "Financials", "Politics", "Elections", "Companies", "World"}
KALSHI_PAGES = 25
# The open listing is long and unordered, so the series that matter most to markets are always asked for by name.
KALSHI_SERIES = ["KXFEDDECISION", "KXFED", "KXCPI", "KXCPICORE", "KXGDP", "KXU3", "KXRECSSNBER",
                 "KXJOBLESSCLAIMS", "KXINXY", "KXEURUSD", "KXUSDJPY"]
TOP = 80             # events kept per venue, by the day's volume
HISTORY_DAYS = 120


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v == v else None


def polymarket():
    events = {}
    for tag in POLY_TAGS:
        q = urllib.parse.urlencode({"tag_slug": tag, "active": "true", "closed": "false",
                                    "order": "volume24hr", "ascending": "false", "limit": 40})
        for e in json.loads(get(f"{POLY}?{q}", limit=30 * 1024 * 1024)):
            slugs = {t.get("slug") for t in e.get("tags") or []}
            if slugs & POLY_SKIP:
                continue
            events[e["id"]] = e
        time.sleep(0.3)
    if not events:
        raise ValueError("Polymarket returned no events")
    out = []
    for e in sorted(events.values(), key=lambda e: -(num(e.get("volume24hr")) or 0))[:TOP]:
        outcomes = []
        for m in e.get("markets") or []:
            if m.get("closed") or not m.get("active", True):
                continue
            try:
                names, prices = json.loads(m.get("outcomes") or "[]"), json.loads(m.get("outcomePrices") or "[]")
            except ValueError:
                continue
            # The first outcome's price: "Yes" on a yes/no market, else the first named side.
            p = num(prices[0]) if prices else None
            if p is None or not num(m.get("volume")):
                continue
            d1 = num(m.get("oneDayPriceChange"))
            label = m.get("groupItemTitle") or (m.get("question") if names[:1] == ["Yes"] else names[0])
            outcomes.append({"id": f"poly:{m['id']}", "label": label,
                             "question": m.get("question"), "prob": round(p, 4),
                             "prev": round(p - d1, 4) if d1 is not None else None,
                             "vol24h": round(num(m.get("volume24hr")) or 0), "vol": round(num(m.get("volume")) or 0)})
        if outcomes:
            outcomes.sort(key=lambda o: -o["prob"])
            out.append({"venue": "Polymarket", "id": f"poly:{e['id']}", "title": e.get("title"),
                        "url": f"https://polymarket.com/event/{e.get('slug')}",
                        "tags": sorted(t.get("label") for t in e.get("tags") or [] if t.get("label"))[:8],
                        "end": e.get("endDate"), "vol24h": round(num(e.get("volume24hr")) or 0),
                        "vol": round(num(e.get("volume")) or 0), "outcomes": outcomes})
    return out


def get_patient(url, limit, tries=5):
    """A GET that waits and tries again when the API says it is busy (HTTP 429)."""
    for i in range(tries):
        try:
            return get(url, limit=limit)
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == tries - 1:
                raise
            time.sleep(2 ** i * 1.5)


def kalshi():
    events, cursor = [], ""
    for _ in range(KALSHI_PAGES):
        q = {"status": "open", "with_nested_markets": "true", "limit": 200}
        if cursor:
            q["cursor"] = cursor
        d = json.loads(get_patient(f"{KALSHI}?{urllib.parse.urlencode(q)}", 40 * 1024 * 1024))
        events += [e for e in d.get("events", []) if e.get("category") in KALSHI_KEEP]
        cursor = d.get("cursor")
        if not cursor:
            break
        time.sleep(1.0)  # the public API is rate limited per address
    for s in KALSHI_SERIES:
        q = urllib.parse.urlencode({"status": "open", "with_nested_markets": "true", "limit": 200, "series_ticker": s})
        events += json.loads(get_patient(f"{KALSHI}?{q}", 40 * 1024 * 1024)).get("events", [])
        time.sleep(1.0)
    events = list({e["event_ticker"]: e for e in events}.values())
    if not events:
        raise ValueError("Kalshi returned no events")
    out = []
    for e in events:
        outcomes = []
        for m in e.get("markets") or []:
            p, prev = num(m.get("last_price_dollars")), num(m.get("previous_price_dollars"))
            vol24, vol = num(m.get("volume_24h_fp")) or 0, num(m.get("volume_fp")) or 0
            if not p or vol == 0:  # never traded: no price to show
                continue
            outcomes.append({"id": f"kalshi:{m['ticker']}", "label": m.get("yes_sub_title") or m.get("title"),
                             "question": m.get("title"), "prob": round(p, 4), "prev": round(prev, 4) if prev else None,
                             # Kalshi counts contracts of $1 face value; the dollar volume is near contracts x price
                             "vol24h": round(vol24 * p), "vol": round(vol * p)})
        if outcomes:
            outcomes.sort(key=lambda o: -o["prob"])
            out.append({"venue": "Kalshi", "id": f"kalshi:{e['event_ticker']}", "title": e.get("title"),
                        "url": f"https://kalshi.com/markets/{e.get('series_ticker', '').lower()}",
                        "tags": [e.get("category")], "end": max((m.get("close_time") or "") for m in e["markets"]) or None,
                        "vol24h": sum(o["vol24h"] for o in outcomes), "vol": sum(o["vol"] for o in outcomes),
                        "outcomes": outcomes})
    out.sort(key=lambda e: -e["vol24h"])
    return out[:TOP]


def main():
    try:
        old = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = {}
    venues = dict(old.get("venues") or {})
    for name, fn in (("Polymarket", polymarket), ("Kalshi", kalshi)):
        try:
            venues[name] = {"fetched": iso(now_utc()), "events": fn()}
            log(f"{name}: {len(venues[name]['events'])} events")
        except Exception as e:  # noqa: BLE001
            log(f"{name} failed, keeping the last copy: {type(e).__name__}: {e}", "warning")
    if not venues:
        log("Prediction markets: no venue has ever been fetched", "error")
        return 1

    # One probability a day per outcome, the day's first sample.
    today = now_utc().date().isoformat()
    hist = old.get("history") or {}
    for v in venues.values():
        for e in v["events"]:
            for o in e["outcomes"]:
                h = hist.setdefault(o["id"], {})
                h.setdefault(today, o["prob"])
    cut = (now_utc().date() - dt.timedelta(days=HISTORY_DAYS)).isoformat()
    live = {o["id"] for v in venues.values() for e in v["events"] for o in e["outcomes"]}
    hist = {k: {d: p for d, p in h.items() if d >= cut} for k, h in hist.items() if k in live or max(h) >= cut}
    hist = {k: h for k, h in hist.items() if h}

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({"schema": SCHEMA, "venues": venues, "history": hist}, separators=(",", ":")), encoding="utf-8")
    log(f"Wrote {CACHE.relative_to(ROOT)} ({CACHE.stat().st_size // 1024} KB, {len(hist)} outcomes with history)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
