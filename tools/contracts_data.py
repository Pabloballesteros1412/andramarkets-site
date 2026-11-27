#!/usr/bin/env python3
"""Fetch the figures behind Hedge Fund Data: Government contracts, at each run.

Run by .github/workflows/hedgefund-data.yml. Writes .cache/hf/contracts.json
(schema "andra.contracts/1", Actions cache, never committed or published):

    actions    every US federal contract action of $10 million or more in the
               last 45 days (new awards, orders and the funding added to
               existing ones), from USAspending.gov, no key: the date, the
               amount, the recipient, the agency, what it is for, and the
               listed company behind the recipient where it is one of the
               contractors in LISTED.
    by_company the listed companies' totals over 7 and 30 days.

USAspending posts contract actions from FPDS a few days after they are signed,
so the latest days fill in over the following week; the Department of Defense's
actions appear only after a 90-day delay, so its awards are under-counted here. An amount is the money
obligated by that action, not the contract's ceiling; a negative amount (a
de-obligation) is kept as it is.

    python3 tools/contracts_data.py
"""
import datetime as dt
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_data import UA, log  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "hf" / "contracts.json"
SCHEMA = "andra.contracts/1"
API = "https://api.usaspending.gov/api/v2/search/spending_by_transaction/"
DAYS, FLOOR, PAGES = 45, 10_000_000, 40

# Listed contractors: (ticker, company, pattern on the recipient's name).
LISTED = [
    ("LMT", "Lockheed Martin", r"LOCKHEED"), ("RTX", "RTX", r"\bRAYTHEON\b|\bRTX\b|PRATT & WHITNEY|COLLINS AEROSPACE"),
    ("GD", "General Dynamics", r"GENERAL DYNAMICS|ELECTRIC BOAT|GULFSTREAM AEROSPACE|BATH IRON WORKS"),
    ("NOC", "Northrop Grumman", r"NORTHROP"), ("BA", "Boeing", r"\bBOEING\b"),
    ("LHX", "L3Harris", r"L3HARRIS|\bL3 \b|HARRIS CORP|AEROJET"), ("HII", "Huntington Ingalls", r"HUNTINGTON INGALLS|NEWPORT NEWS SHIPBUILDING"),
    ("LDOS", "Leidos", r"\bLEIDOS\b"), ("BAH", "Booz Allen Hamilton", r"BOOZ ALLEN"), ("SAIC", "SAIC", r"SCIENCE APPLICATIONS INTERNATIONAL"),
    ("CACI", "CACI", r"\bCACI\b"), ("PSN", "Parsons", r"\bPARSONS\b"), ("KBR", "KBR", r"\bKBR\b"),
    ("PLTR", "Palantir", r"PALANTIR"), ("MSFT", "Microsoft", r"MICROSOFT"), ("AMZN", "Amazon", r"AMAZON WEB SERVICES|\bAMAZON\b"),
    ("GOOGL", "Alphabet", r"\bGOOGLE\b"), ("ORCL", "Oracle", r"\bORACLE\b"), ("IBM", "IBM", r"INTERNATIONAL BUSINESS MACHINES|\bIBM\b"),
    ("ACN", "Accenture", r"ACCENTURE"), ("BWXT", "BWX Technologies", r"\bBWX"), ("TXT", "Textron", r"TEXTRON|BELL TEXTRON"),
    ("GE", "GE Aerospace", r"GENERAL ELECTRIC|GE AEROSPACE"), ("HON", "Honeywell", r"HONEYWELL"),
    ("MCK", "McKesson", r"MCKESSON"), ("CAH", "Cardinal Health", r"CARDINAL HEALTH"), ("UNH", "UnitedHealth", r"OPTUM|UNITEDHEALTH"),
    ("CNC", "Centene", r"CENTENE|HEALTH NET FEDERAL"), ("HUM", "Humana", r"HUMANA"), ("PFE", "Pfizer", r"\bPFIZER\b"),
    ("MRNA", "Moderna", r"MODERNA"), ("FLR", "Fluor", r"\bFLUOR\b"), ("J", "Jacobs", r"\bJACOBS\b"), ("AMTM", "Amentum", r"AMENTUM"),
    ("V2X", "V2X", r"\bV2X\b|VECTRUS"), ("KTOS", "Kratos", r"KRATOS"), ("AVAV", "AeroVironment", r"AEROVIRONMENT"),
    ("RKLB", "Rocket Lab", r"ROCKET LAB"), ("LUNR", "Intuitive Machines", r"INTUITIVE MACHINES"),
]
LISTED_RE = [(t, n, re.compile(p)) for t, n, p in LISTED]
FIELDS = ["Award ID", "Recipient Name", "Action Date", "Transaction Amount", "Awarding Agency",
          "Awarding Sub Agency", "Transaction Description", "naics_code"]


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def post(body):
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={"User-Agent": UA, "Content-Type": "application/json"})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read(30 * 1024 * 1024))
        except OSError:
            if i == 3:
                raise
            time.sleep(3 * (i + 1))


def listed(name):
    for t, n, rx in LISTED_RE:
        if rx.search(name or ""):
            return t, n
    return None, None


def fetch():
    end = now_utc().date()
    start = end - dt.timedelta(days=DAYS)
    out = []
    for page in range(1, PAGES + 1):
        d = post({"filters": {"award_type_codes": ["A", "B", "C", "D"],
                              "time_period": [{"start_date": start.isoformat(), "end_date": end.isoformat()}]},
                  "fields": FIELDS, "sort": "Transaction Amount", "order": "desc", "limit": 100, "page": page})
        rows = d.get("results") or []
        for r in rows:
            amt = r.get("Transaction Amount") or 0
            if amt < FLOOR:
                break
            t, n = listed((r.get("Recipient Name") or "").upper())
            out.append({"id": r.get("generated_internal_id"), "award": r.get("Award ID"), "date": r.get("Action Date"),
                        "amount": round(amt), "recipient": r.get("Recipient Name"), "ticker": t, "company": n,
                        "agency": r.get("Awarding Agency"), "sub_agency": r.get("Awarding Sub Agency"),
                        "what": (r.get("Transaction Description") or "")[:240], "naics": r.get("naics_code")})
        else:
            if (d.get("page_metadata") or {}).get("hasNext"):
                time.sleep(0.5)
                continue
        break
    if not out:
        raise ValueError("USAspending returned no contract actions")
    return out


def main():
    try:
        acts = fetch()
    except Exception as e:  # noqa: BLE001
        log(f"USAspending failed, keeping the last copy: {type(e).__name__}: {e}", "warning")
        return 0 if CACHE.exists() else 1
    today = now_utc().date()
    by = {}
    for a in acts:
        if not a["ticker"] or not a["date"]:
            continue
        age = (today - dt.date.fromisoformat(a["date"])).days
        c = by.setdefault(a["ticker"], {"ticker": a["ticker"], "company": a["company"], "d7": 0, "d30": 0, "n30": 0})
        if age <= 7:
            c["d7"] += a["amount"]
        if age <= 30:
            c["d30"] += a["amount"]
            c["n30"] += 1
    out = {"schema": SCHEMA, "fetched": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"), "days": DAYS, "floor": FLOOR,
           "actions": acts, "by_company": sorted(by.values(), key=lambda c: -c["d30"]),
           "source": "USAspending.gov (FPDS contract actions)"}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    log(f"USAspending: {len(acts)} actions of $10m or more in {DAYS} days, {len(by)} listed companies")
    return 0


if __name__ == "__main__":
    sys.exit(main())
