#!/usr/bin/env python3
"""Import the daily close notes from the agent's GitHub Actions artifacts.

Run by .github/workflows/publish-notes.yml. For every artifact the agent
uploaded that this repo has not seen yet (data/import-state.json), oldest
first:

  1. download the zip with a read-only token and take at most three files:
     AndraMarkets_Close_YYYYMMDD.pdf, facts_YYYYMMDD.json and, from runs since
     15 September 2026, note_YYYYMMDD.json. Earlier runs saved no note file:
     their text is recovered from the PDF (tools/pdf_note.py) and always held
  2. check them (the PDF is read in memory for the figure check and edition)
       broken (missing PDF or facts, bad JSON, not a PDF, dates disagree):
         rejected, nothing is published and the run fails so GitHub emails you
       not an NYSE trading day, dated in the future, made before that day's
         close, the figure check failed ("Control note." in the PDF), or the
         text was recovered from the PDF: held, opened as a pull request
       otherwise: published straight to main
  3. one note per session date: the newest clean run is published; a held
     run newer than it gets a pull request (for recovered text, the most
     complete run of the day); every other run that day is superseded

Only data/notes/<date>.json is written: the note text plus the ten closing
levels the home tape shows. This repo is public, so the PDF and the full facts
file are never written to it: they stay in the agent repo's artifacts.
Captions, LinkedIn and TikTok files in the artifact are never read.

Environment:
    AGENT_ARTIFACTS_TOKEN  fine-grained token, Actions: read on the agent repo
    GITHUB_TOKEN           this repo's workflow token (push, pull requests)
    AGENT_REPO             default Pabloballesteros1412/andramarkets
    GITHUB_REPOSITORY      this repo, set by Actions
"""
import datetime as dt
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nyse  # noqa: E402
import pdf_note  # noqa: E402

# Bump when a change should re-check artifacts already imported.
VERSION = 2
NY = ZoneInfo("America/New_York")
RECOVERED = ("Recovered from the PDF: the agent saved no note text for this run, "
             "so the text was read back from the report. Check it before merging.")

ROOT = Path(__file__).resolve().parent.parent
STATE = Path("data/import-state.json")
API = "https://api.github.com"
AGENT_REPO = os.environ.get("AGENT_REPO", "Pabloballesteros1412/andramarkets")
SITE_REPO = os.environ.get("GITHUB_REPOSITORY", "Pabloballesteros1412/andramarkets-site")

MAX_ZIP = 100 * 1024 * 1024
MAX_PDF = 25 * 1024 * 1024
MAX_JSON = 5 * 1024 * 1024
FILES = {
    "pdf": re.compile(r"AndraMarkets_Close_(\d{8})\.pdf"),
    "note": re.compile(r"note_(\d{8})\.json"),
    "facts": re.compile(r"facts_(\d{8})\.json"),
}
# The note text published on the site. linkedin and tiktok are left out.
NOTE_FIELDS = ("headline", "standfirst", "takeaways", "desk_view", "watching",
               "equities", "rates", "credit", "fx", "commodities", "volatility",
               "digital", "international", "correlation")
LIST_FIELDS = ("takeaways", "watching")
# The home tape: (facts block, instrument key). Only these closes are kept.
TAPE = [("us_equity", "spx"), ("us_equity", "ndx"), ("us_equity", "rut"),
        ("europe", "sx5e"), ("apac", "nky"), ("volatility", "vix"),
        ("treasury_curve", "ust10y"), ("fx", "eurusd"),
        ("commodities", "wti"), ("commodities", "gold")]


class Rejected(Exception):
    """The artifact cannot be published at all."""


# GitHub ----------------------------------------------------------------------

def _request(url, token=None, method="GET", body=None):
    headers = {"Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28",
               "User-Agent": "andramarkets-site-importer"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    return urllib.request.Request(url, data=data, method=method, headers=headers)


def api(path, token, method="GET", body=None):
    with urllib.request.urlopen(_request(API + path, token, method, body), timeout=60) as r:
        raw = r.read()
    return json.loads(raw) if raw else None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def download_zip(artifact, token):
    """Artifact zips redirect to signed storage: follow it without the token."""
    url = f"{API}/repos/{AGENT_REPO}/actions/artifacts/{artifact['id']}/zip"
    try:
        r = urllib.request.build_opener(_NoRedirect).open(_request(url, token), timeout=60)
    except urllib.error.HTTPError as e:
        if e.code not in (301, 302, 303, 307, 308):
            raise
        r = urllib.request.urlopen(_request(e.headers["Location"]), timeout=300)
    with r:
        blob = r.read(MAX_ZIP + 1)
    if len(blob) > MAX_ZIP:
        raise Rejected("the artifact is larger than 100 MB")
    return blob


def list_artifacts(token):
    found, page = [], 1
    while True:
        res = api(f"/repos/{AGENT_REPO}/actions/artifacts?per_page=100&page={page}", token)
        items = res.get("artifacts", [])
        found += items
        if len(items) < 100:
            break
        page += 1
    keep = [a for a in found
            if re.fullmatch(r"andramarkets-\d+", a.get("name", ""))
            and not a.get("expired")
            and (a.get("workflow_run") or {}).get("head_branch") == "main"]
    return sorted(keep, key=lambda a: (a["created_at"], a["id"]))


# Checks ----------------------------------------------------------------------

def unpack(blob):
    """Return (YYYYMMDD, {"pdf": bytes, "facts": bytes[, "note": bytes]})."""
    found = {}
    try:
        z = zipfile.ZipFile(io.BytesIO(blob))
    except zipfile.BadZipFile:
        raise Rejected("the artifact is not a valid zip file")
    with z:
        for info in z.infolist():
            # Top-level files only, by exact name. Nothing else is extracted.
            if info.is_dir() or "/" in info.filename or "\\" in info.filename:
                continue
            for kind, pattern in FILES.items():
                m = pattern.fullmatch(info.filename)
                if not m:
                    continue
                if kind in found:
                    raise Rejected(f"the artifact holds more than one {kind} file")
                cap = MAX_PDF if kind == "pdf" else MAX_JSON
                if info.file_size > cap:
                    raise Rejected(f"{info.filename} is too large")
                with z.open(info) as f:
                    data = f.read(cap + 1)
                if len(data) > cap:
                    raise Rejected(f"{info.filename} is too large")
                found[kind] = (m.group(1), data)
    missing = [k for k in ("pdf", "facts") if k not in found]
    if missing:
        raise Rejected("the artifact has no " + " and no ".join(missing) + " file")
    stamps = {stamp for stamp, _ in found.values()}
    if len(stamps) != 1:
        raise Rejected("the PDF and JSON files carry different dates")
    return stamps.pop(), {k: data for k, (_, data) in found.items()}


def number(v):
    """The agent's JSON may hold NaN; keep finite numbers only."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return float(v) if math.isfinite(v) else None


def closes(facts):
    """The tape's closing level and daily change, from the facts file."""
    stale = set(facts.get("series_not_yet_published") or [])
    out = {}
    for block, key in TAPE:
        rows = facts.get(block) if isinstance(facts.get(block), list) else []
        row = next((r for r in rows if isinstance(r, dict) and r.get("key") == key), {})
        out[key] = {"last": number(row.get("last")), "chg": number(row.get("chg")),
                    "stale": key in stale}
    return out


def clean_text(v):
    if not isinstance(v, str):
        return ""
    v = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", v.replace("\r\n", "\n"))
    return re.sub(r"\n{3,}", "\n\n", v).strip()


def pdf_text(pdf):
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(pdf))
    return " ".join(page.extract_text() or "" for page in reader.pages)


def check(stamp, files, artifact, today):
    """Build the note record. Returns (record, hold_reasons) or raises Rejected."""
    try:
        note = json.loads(files["note"]) if "note" in files else None
        facts = json.loads(files["facts"])
    except ValueError as e:
        raise Rejected(f"a JSON file does not parse ({e})")
    if not isinstance(facts, dict) or not isinstance(note, (dict, type(None))):
        raise Rejected("a JSON file is not an object")
    try:
        day = dt.date.fromisoformat(str(facts.get("date"))[:10])
    except ValueError:
        raise Rejected("the facts file has no valid session date")
    if day.strftime("%Y%m%d") != stamp:
        raise Rejected(f"the facts file is dated {day} but the files are named {stamp}")
    if not files["pdf"].startswith(b"%PDF-"):
        raise Rejected("the PDF file is not a PDF")
    source = "agent"
    if note is None:
        source = "pdf"
        try:
            note = pdf_note.extract(files["pdf"])
        except Exception as e:  # noqa: BLE001
            raise Rejected(f"no note file, and the PDF text could not be read ({type(e).__name__})")

    text = {}
    for field in NOTE_FIELDS:
        v = note.get(field)
        if field in LIST_FIELDS:
            items = v if isinstance(v, list) else []
            text[field] = [t for t in (clean_text(i) for i in items) if t]
        else:
            text[field] = clean_text(v)
    if not text["headline"]:
        raise Rejected("the note has no headline" if source == "agent"
                       else "no note file, and no headline could be read from the PDF")

    hold = []
    trading = nyse.is_trading_day(day)
    if trading is None:
        hold.append(f"{day.year} is not in the NYSE holiday table in tools/nyse.py, "
                    "so the session date could not be confirmed. Add that year's dates.")
    elif not trading:
        hold.append(f"{day:%A} {day.day} {day:%B %Y} was not an NYSE trading day.")
    if day > today:
        hold.append(f"The note is dated {day}, after today in New York.")
    made = dt.datetime.fromisoformat(artifact["created_at"].replace("Z", "+00:00")).astimezone(NY)
    close = dt.datetime.combine(day, dt.time(13 if nyse.close_time(day) == "1:00 pm" else 16), NY)
    if day <= today and made < close:
        hold.append(f"The run finished at {made:%H:%M} ET on {made:%A} {made.day} {made:%B}, "
                    f"before the {day.day} {day:%B} close, so its figures cannot be that session's.")
    if source == "pdf":
        hold.append(RECOVERED)

    edition, figure_check = None, "unknown"
    try:
        body = re.sub(r"\s+", " ", pdf_text(files["pdf"]))
    except Exception as e:  # noqa: BLE001
        body = ""
        hold.append(f"The PDF text could not be read ({type(e).__name__}), so the "
                    "figure check could not be confirmed.")
    else:
        if not body.strip():
            hold.append("The PDF has no extractable text, so the figure check "
                        "could not be confirmed.")
        if re.search(r"Control\s*note", body):
            figure_check = "failed"
            hold.append("The figure check failed: the PDF carries a Control note.")
        elif body.strip():
            figure_check = "passed"
        m = re.search(r"Edition\s*(\d{1,6})\b", body, re.I)
        edition = m.group(1) if m else None

    record = {
        "date": day.isoformat(),
        "published": True,
        "edition": edition,
        "figure_check": figure_check,
        "text_source": source,
        "note": text,
        "closes": closes(facts),
        "source": {
            "repo": AGENT_REPO,
            "run_id": (artifact.get("workflow_run") or {}).get("id"),
            "artifact_id": artifact["id"],
            "created_at": artifact["created_at"],
        },
    }
    return record, hold


# Files and git ---------------------------------------------------------------

def write_note(root, record):
    notes = root / "data" / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    (notes / f"{record['date']}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def existing(root, date):
    f = root / "data" / "notes" / f"{date}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def git(*args, cwd=ROOT, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)
    if check and r.returncode:
        raise RuntimeError(f"git {args[0]} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def push_main(message):
    git("add", "-A", "data")
    if not git("status", "--porcelain", "data"):
        return False
    git("commit", "-m", message)
    for attempt in range(4):
        if subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT).returncode == 0:
            return True
        # Someone edited main meanwhile (the owner in the web editor). Replay.
        git("pull", "--rebase", "origin", "main")
    raise SystemExit("Could not push to main after 4 attempts.")


def push_branch(branch, records, message):
    """Commit the records on a fresh branch from main and force-push it."""
    tmp = Path(tempfile.mkdtemp())
    try:
        git("fetch", "origin", "main")
        git("worktree", "add", "-B", branch, str(tmp), "origin/main")
        for record in records:
            write_note(tmp, record)
        git("add", "-A", "data", cwd=tmp)
        git("commit", "-m", message, cwd=tmp)
        git("push", "--force", "origin", f"{branch}:{branch}", cwd=tmp)
    finally:
        git("worktree", "remove", "--force", str(tmp), check=False)
        shutil.rmtree(tmp, ignore_errors=True)


def open_pr(branch, title, body, token):
    owner = SITE_REPO.split("/")[0]
    open_prs = api(f"/repos/{SITE_REPO}/pulls?state=open&head={owner}:{branch}", token)
    if open_prs:
        api(f"/repos/{SITE_REPO}/pulls/{open_prs[0]['number']}", token, "PATCH",
            {"title": title, "body": body})
        return open_prs[0]["html_url"]
    return api(f"/repos/{SITE_REPO}/pulls", token, "POST",
               {"title": title, "head": branch, "base": "main", "body": body})["html_url"]


def _run_link(record):
    return f"https://github.com/{AGENT_REPO}/actions/runs/{record['source']['run_id']}"


def _filled(record):
    return sum(1 for v in record["note"].values() if v)


def open_held_pr(record, reasons, token):
    date, artifact = record["date"], record["source"]["artifact_id"]
    branch = f"held/{date}-{artifact}"
    push_branch(branch, [record], f"Held close note {date} for review")
    lines = [
        f"The close note for **{date}** did not pass every check, so it was not published.",
        "",
        "**Why it was held**",
        "",
        *[f"- {r}" for r in reasons],
        "",
        f"**Headline:** {record['note']['headline']}",
        "",
        "**What to do**",
        "",
        "- **Merge** to publish it on the site as it is.",
        "- **Close** to discard it. Nothing is published.",
    ]
    if existing(ROOT, date):
        lines.append(f"- Merging replaces the note already published for {date}.")
    lines += ["", f"Read the note text under **Files changed** (`data/notes/{date}.json`), "
              f"or the PDF in the agent run: {_run_link(record)}"]
    return open_pr(branch, f"Held close note: {date}", "\n".join(lines), token)


def open_recovered_pr(records, token):
    """One pull request for every note whose only issue is recovered text."""
    records = sorted(records, key=lambda r: r["date"])
    first, last = records[0]["day"], records[-1]["day"]
    span = f"{first.day} {first:%b} to {last.day} {last:%b %Y}" if len(records) > 1 else f"{first.day} {first:%b %Y}"
    branch = "held/recovered"
    push_branch(branch, [{k: v for k, v in r.items() if k != "day"} for r in records],
                f"Recovered close notes {span} for review")
    lines = [
        f"These {len(records)} close notes come from agent runs before 15 September 2026, "
        "which saved no note text. Their text was read back from each report PDF, using the "
        "report's type sizes to tell the prose from tables and exhibits. On the 23 later runs, "
        "where the agent's own text exists, this recovery reproduced every field exactly.",
        "",
        "Each passed every other check (trading day, made after the close, figure check). "
        "Where a day had several runs, the most complete one was taken.",
        "",
        "| Date | Headline | Fields | Agent run |",
        "|---|---|---|---|",
        *[f"| {r['date']} | {r['note']['headline']} | {_filled(r)} of {len(NOTE_FIELDS)} | "
          f"[PDF]({_run_link(r)}) |" for r in records],
        "",
        "**What to do**",
        "",
        "- Read the notes under **Files changed** (`data/notes/<date>.json`).",
        "- **Merge** to publish them all. To leave one out first, open its file in "
        "**Files changed**, use the **...** menu, **Delete file**, and commit to this branch.",
        "- **Close** to publish none of them.",
    ]
    return open_pr(branch, f"Recovered close notes: {span}", "\n".join(lines), token)


def close_stale_prs(date, keep, state, token):
    """Close held pull requests for the date other than the one kept."""
    for pr in api(f"/repos/{SITE_REPO}/pulls?state=open&per_page=100", token) or []:
        ref = pr["head"]["ref"]
        if not ref.startswith(f"held/{date}-") or ref == keep:
            continue
        api(f"/repos/{SITE_REPO}/issues/{pr['number']}/comments", token, "POST",
            {"body": f"Closed automatically: a newer or more complete note for {date} replaces this one."})
        api(f"/repos/{SITE_REPO}/pulls/{pr['number']}", token, "PATCH", {"state": "closed"})
        try:
            api(f"/repos/{SITE_REPO}/git/refs/heads/{ref}", token, "DELETE")
        except urllib.error.HTTPError:
            pass


# Run -------------------------------------------------------------------------

def load_state(root):
    f = root / STATE
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"artifacts": {}}


def save_state(root, state):
    (root / STATE).parent.mkdir(parents=True, exist_ok=True)
    (root / STATE).write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def output(name, value):
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"{name}={value}\n")


def summary(rows):
    if not os.environ.get("GITHUB_STEP_SUMMARY") or not rows:
        return
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
        f.write("| Artifact | Date | Result |\n|---|---|---|\n")
        for a, d, r in rows:
            f.write(f"| {a} | {d} | {r} |\n")


def decide(results, root):
    """Pick, per session date, what to publish, what to hold and what is superseded.

    results: dicts with artifact, record, reasons. Returns (publish, held, superseded).
    """
    by_date = {}
    for r in results:
        by_date.setdefault(r["record"]["date"], []).append(r)
    publish, held, superseded = [], [], []
    for date, cands in sorted(by_date.items()):
        cands.sort(key=lambda r: r["artifact"]["created_at"])
        prev = existing(root, date)
        live = prev["source"]["created_at"] if prev else ""
        clean = [r for r in cands if not r["reasons"]]
        winner = clean[-1] if clean and clean[-1]["artifact"]["created_at"] >= live else None
        if winner:
            publish.append(winner)
            live = winner["artifact"]["created_at"]
        later = [r for r in cands if r["reasons"] and r["artifact"]["created_at"] > live]
        keep = None
        if later:
            # The agent's own text wins over recovered text; then, for recovered
            # text, the most complete run; then the newest.
            keep = max(later, key=lambda r: (r["record"]["text_source"] == "agent",
                                             0 if r["record"]["text_source"] == "agent" else _filled(r["record"]),
                                             r["artifact"]["created_at"]))
            held.append(keep)
        superseded += [r for r in cands if r is not winner and r is not keep]
    return publish, held, superseded


def main():
    dry = "--dry-run" in sys.argv
    agent_token = os.environ.get("AGENT_ARTIFACTS_TOKEN")
    site_token = os.environ.get("GITHUB_TOKEN")
    if not agent_token:
        raise SystemExit("AGENT_ARTIFACTS_TOKEN is not set. See README, Publishing the close note.")
    today = dt.datetime.now(NY).date()
    state = load_state(ROOT)
    seen = state["artifacts"]

    try:
        artifacts = [a for a in list_artifacts(agent_token)
                     if seen.get(str(a["id"]), {}).get("v", 1) < VERSION]
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Could not list the agent's artifacts (HTTP {e.code}). "
                         "The token may have expired or lost Actions: read access.")
    print(f"{len(artifacts)} artifact(s) to check from {AGENT_REPO}")

    results, rejected, rows = [], [], []
    for a in artifacts:
        entry = {"v": VERSION, "run_id": (a.get("workflow_run") or {}).get("id"),
                 "created_at": a["created_at"]}
        try:
            stamp, files = unpack(download_zip(a, agent_token))
            record, reasons = check(stamp, files, a, today)
        except Rejected as e:
            entry.update(status="rejected", reason=str(e))
            rejected.append((a, str(e)))
            rows.append((a["id"], "", f"rejected: {e}"))
            print(f"::error::Artifact {a['id']} rejected: {e}")
        else:
            entry["date"] = record["date"]
            results.append({"artifact": a, "record": record, "reasons": reasons, "entry": entry})
        seen[str(a["id"])] = entry

    publish, held, superseded = decide(results, ROOT)
    for r in superseded:
        r["entry"]["status"] = "superseded"
        rows.append((r["artifact"]["id"], r["record"]["date"], "superseded by another run that day"))
    for r in publish:
        record, prev = r["record"], existing(ROOT, r["record"]["date"])
        if prev and prev.get("published") is False:
            record["published"] = False  # The owner withdrew this date by hand. Keep it so.
        r["entry"]["status"] = "published"
        rows.append((r["artifact"]["id"], record["date"],
                     "replaced the earlier note" if prev and prev["source"]["artifact_id"] != record["source"]["artifact_id"] else "published"))
        if not dry:
            write_note(ROOT, record)
    recovered = [r for r in held if r["reasons"] == [RECOVERED]]
    single = [r for r in held if r["reasons"] != [RECOVERED]]
    for r in held:
        r["entry"].update(status="held", reasons=r["reasons"])
        rows.append((r["artifact"]["id"], r["record"]["date"], "held: " + " ".join(r["reasons"])))

    if dry:
        plan = [f"{d} {res}" for _, d, res in sorted(rows, key=lambda x: (x[1], str(x[0])))]
        print("\n".join(plan))
        print(f"DRY RUN: publish {len(publish)}, held {len(single)} + {len(recovered)} recovered "
              f"in one PR, superseded {len(superseded)}, rejected {len(rejected)}")
        return 0

    failed = 0
    for group, opener in ([(r,) for r in single], None), ([tuple(recovered)] if recovered else [], "recovered"):
        for batch in group:
            try:
                if not site_token:
                    raise RuntimeError("GITHUB_TOKEN is not set")
                if opener:
                    url = open_recovered_pr([dict(x["record"], day=dt.date.fromisoformat(x["record"]["date"])) for x in batch], site_token)
                else:
                    url = open_held_pr(batch[0]["record"], batch[0]["reasons"], site_token)
                for x in batch:
                    x["entry"]["pr"] = url
                print(f"Held {', '.join(x['record']['date'] for x in batch)}: {url}")
            except Exception as e:  # noqa: BLE001
                # Not recorded, so the next run tries again.
                for x in batch:
                    del seen[str(x["artifact"]["id"])]
                failed += 1
                print(f"::error::Could not open the review pull request: {e}. Check Settings, "
                      "Actions, General: Allow GitHub Actions to create and approve pull requests.")

    save_state(ROOT, state)
    dates = sorted({r["record"]["date"] for r in publish})
    message = (f"Publish close note{'s' if len(dates) > 1 else ''} {', '.join(dates)}"
               if dates else "Record imported agent artifacts")
    pushed = push_main(message) if artifacts else False

    if site_token:
        for r in publish + single:
            date = r["record"]["date"]
            keep = f"held/{date}-{r['artifact']['id']}" if r in single else None
            close_stale_prs(date, keep, state, site_token)
        for r in recovered:
            close_stale_prs(r["record"]["date"], None, state, site_token)

    summary(rows)
    output("published", "true" if publish and pushed else "false")
    print(f"published {len(publish)}, held {len(single)} + {len(recovered)} recovered, "
          f"superseded {len(superseded)}, rejected {len(rejected)}")
    return 1 if rejected or failed else 0


if __name__ == "__main__":
    sys.exit(main())
