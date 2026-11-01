#!/usr/bin/env python3
"""Fetch the history behind Market history (market-history/), at deploy time.

Run by .github/workflows/pages.yml before tools/build_site.py. Writes one file,
.cache/history/sp500.json: every S&P 500 daily close since the end of 1927,
price only (no dividends), from Yahoo Finance ^GSPC, the series the Trading
Simulator replays (the S&P 90 before March 1957, as Yahoo carries it).
tools/page_market_history.py measures each episode's fall, its low and its
recovery from it and draws the charts; nothing here is published as a file.

    {"fetched": "2026-11-02", "source": "Yahoo Finance, ^GSPC",
     "rows": [["1927-12-30", 17.66], ...]}

Fetched at most once a day. A failed fetch keeps the last good copy (restored
by the workflow's cache) and never stops the deploy; with no copy at all the
page shows "Data pending".

    python3 tools/history_data.py
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sim_data import log, yahoo  # noqa: E402  (the Simulators' Yahoo reader)

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "history" / "sp500.json"
SOURCE = "Yahoo Finance, ^GSPC"


def build():
    closes = yahoo("^GSPC", dt.date(1927, 12, 1))
    days = sorted(closes)
    if len(days) < 24000 or days[0] > "1928-01-31":
        raise ValueError(f"^GSPC history too short: {len(days)} sessions from {days[0] if days else None}")
    return {"source": SOURCE, "rows": [[d, round(closes[d], 2)] for d in days]}


def main():
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    try:
        old = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = None
    if old and old.get("fetched") == today:
        log(f"Market history: already fetched today, {len(old['rows'])} sessions to {old['rows'][-1][0]}")
        return 0
    try:
        data = build()
    except Exception as e:  # noqa: BLE001  (keep the last good copy)
        log(f"Market history: S&P 500 history not fetched ({e}); "
            + ("the last good copy stays" if old else "the page shows Data pending"), "warning")
        return 0
    data["fetched"] = today
    CACHE.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    log(f"Market history: {len(data['rows'])} sessions, {data['rows'][0][0]} to {data['rows'][-1][0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
