#!/usr/bin/env python3
"""Fetch the figures behind Hedge Fund Data: Insiders, at each run.

Run by .github/workflows/hedgefund-data.yml. Writes .cache/hf/insiders.json
(schema "andra.insiders/1", Actions cache, never committed or published):

    trades    every open-market purchase (code P) and sale (code S) reported
              on a Form 4 in the last 45 days: the company and its ticker, the
              insider's role (chief executive, chief financial officer, other
              officer, director, 10% owner), the date, shares, price and value.
              The insider's name is not kept (DESIGN.md: no personal names).
    clusters  the companies where two or more insiders bought in the open
              market within the last 30 days: the signal with the most
              support in the research on insider trading.

From SEC EDGAR, no key. The SEC asks every automated client to name itself and
give a contact address, and refuses those that do not, so the run needs
SEC_CONTACT_EMAIL. It keeps to the SEC's limit of ten requests a second (eight
here) and reads at most MAX_PER_RUN new filings a run, so a busy day is read
over the day's runs; filings already read are never read again.

    python3 tools/insiders_data.py

Environment:
    SEC_CONTACT_EMAIL   the contact address sent in the User-Agent (secret).
"""
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_data import log  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "hf" / "insiders.json"
SCHEMA = "andra.insiders/1"
INDEX = "https://www.sec.gov/Archives/edgar/daily-index/{y}/QTR{q}/form.{d}.idx"
ARCHIVE = "https://www.sec.gov/Archives/"
KEEP_DAYS, INDEX_DAYS, CLUSTER_DAYS = 45, 6, 30
MAX_PER_RUN = 900
GAP = 0.125  # eight requests a second


class Sec:
    def __init__(self, email):
        self.ua = f"Andra Markets research site {email}"
        self.last = 0.0

    def get(self, url, limit=20 * 1024 * 1024, missing_ok=False):
        """missing_ok: the SEC answers 403, not 404, for an object that does not exist yet
        (today's index before it is published), so a 403 there means "not yet"."""
        for i in range(4):
            wait = self.last + GAP - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self.last = time.monotonic()
            req = urllib.request.Request(url, headers={"User-Agent": self.ua, "Accept-Encoding": "identity"})
            try:
                with urllib.request.urlopen(req, timeout=40) as r:
                    return r.read(limit)
            except urllib.error.HTTPError as e:
                if e.code == 404 or (e.code == 403 and missing_ok):
                    return None
                if e.code not in (403, 429, 500, 502, 503) or i == 3:
                    raise
                time.sleep(10 * (i + 1))  # the SEC asks clients over its limit to back off
        return None


def role(rel):
    t = (rel.findtext("officerTitle") or "").strip().lower()
    if rel.findtext("isOfficer") in ("1", "true"):
        if re.search(r"chief executive|\bceo\b|president and c", t):
            return "Chief executive"
        if re.search(r"chief financial|\bcfo\b", t):
            return "Chief financial officer"
        return "Officer"
    if rel.findtext("isDirector") in ("1", "true"):
        return "Director"
    if rel.findtext("isTenPercentOwner") in ("1", "true"):
        return "10% owner"
    return "Other"


def parse(txt):
    """The open-market purchases and sales in one Form 4 submission."""
    m = re.search(r"<ownershipDocument>.*?</ownershipDocument>", txt, re.S)
    if not m:
        return []
    try:
        doc = ET.fromstring(m.group(0))
    except ET.ParseError:
        return []
    if doc.findtext("documentType") not in ("4", "4/A"):
        return []
    issuer = doc.find("issuer")
    ticker = (issuer.findtext("issuerTradingSymbol") or "").strip().upper() if issuer is not None else ""
    company = (issuer.findtext("issuerName") or "").strip() if issuer is not None else ""
    owners = doc.findall("reportingOwner")
    who = role(owners[0].find("reportingOwnerRelationship")) if owners and owners[0].find("reportingOwnerRelationship") is not None else "Other"
    # The filer's SEC number, to count distinct insiders; never shown.
    cik = (owners[0].findtext("reportingOwnerId/rptOwnerCik") or "").strip() if owners else ""
    out = []
    for tx in doc.findall("nonDerivativeTable/nonDerivativeTransaction"):
        code = tx.findtext("transactionCoding/transactionCode")
        if code not in ("P", "S"):
            continue
        try:
            shares = float(tx.findtext("transactionAmounts/transactionShares/value") or 0)
            price = float(tx.findtext("transactionAmounts/transactionPricePerShare/value") or 0)
        except ValueError:
            continue
        date = (tx.findtext("transactionDate/value") or "")[:10]
        if not shares or not date:
            continue
        out.append({"ticker": ticker or None, "company": company, "role": who, "owner": cik or None, "code": code, "date": date,
                    "shares": round(shares), "price": round(price, 4) if price else None,
                    "value": round(shares * price) if price else None})
    return out


def main():
    email = (os.environ.get("SEC_CONTACT_EMAIL") or "").strip()
    try:
        old = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = {}
    if not email:
        log("Insiders: SEC_CONTACT_EMAIL is not set; the SEC refuses clients without a contact", "warning")
        return 0
    sec = Sec(email)
    seen = set(old.get("seen") or [])
    trades = old.get("trades") or []
    today = dt.datetime.now(dt.timezone.utc).date()

    # Form 4 filings listed in the last few daily indexes, oldest first.
    todo, d = [], today
    days = []
    while len(days) < INDEX_DAYS and d > today - dt.timedelta(days=20):
        if d.weekday() < 5:  # EDGAR files on weekdays
            days.append(d)
        d -= dt.timedelta(days=1)
    for day in reversed(days):
        raw = sec.get(INDEX.format(y=day.year, q=(day.month - 1) // 3 + 1, d=day.strftime("%Y%m%d")), missing_ok=True)
        if not raw:
            continue
        for line in raw.decode("latin-1").splitlines():
            if line.startswith("4 ") or line.startswith("4/A "):
                path = line.split()[-1]
                if path.endswith(".txt") and path not in seen:
                    todo.append(path)
    read = 0
    for path in todo[:MAX_PER_RUN]:
        try:
            raw = sec.get(ARCHIVE + path, limit=5 * 1024 * 1024)
        except Exception as e:  # noqa: BLE001
            log(f"SEC {path}: {type(e).__name__}: {e}", "warning")
            continue
        seen.add(path)
        read += 1
        if raw:
            for t in parse(raw.decode("utf-8", "replace")):
                t["filing"] = path.rsplit("/", 1)[-1].removesuffix(".txt")
                trades.append(t)

    cut = (today - dt.timedelta(days=KEEP_DAYS)).isoformat()
    trades = [t for t in trades if t["date"] >= cut]
    # The seen list only has to cover the filings still in the indexes read.
    seen = sorted(seen)[-60000:]
    ccut = (today - dt.timedelta(days=CLUSTER_DAYS)).isoformat()
    buys = {}
    for t in trades:
        if t["code"] == "P" and t["date"] >= ccut and t["ticker"]:
            b = buys.setdefault(t["ticker"], {"ticker": t["ticker"], "company": t["company"], "owners": set(),
                                               "value": 0, "roles": set(), "last": t["date"]})
            b["owners"].add(t.get("owner") or t["filing"])
            b["value"] += t["value"] or 0
            b["roles"].add(t["role"])
            b["last"] = max(b["last"], t["date"])
    clusters = sorted(({k: v for k, v in b.items() if k != "owners"} | {"insiders": len(b["owners"]), "roles": sorted(b["roles"])}
                       for b in buys.values() if len(b["owners"]) >= 2), key=lambda b: -b["value"])
    out = {"schema": SCHEMA, "fetched": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "trades": sorted(trades, key=lambda t: t["date"], reverse=True), "clusters": clusters, "seen": seen,
           "source": "SEC EDGAR, Form 4"}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    log(f"Insiders: read {read} of {len(todo)} new filings; {len(trades)} trades held, {len(clusters)} cluster buys")
    return 0


if __name__ == "__main__":
    sys.exit(main())
