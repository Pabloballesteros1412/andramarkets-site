#!/usr/bin/env python3
"""Import the daily close notes from the agent's GitHub Actions artifacts.

Run by .github/workflows/publish-notes.yml. For every artifact the agent
uploaded that this repo has not seen yet (data/import-state.json), oldest
first:

  1. download the zip with a read-only token and take exactly three files:
     AndraMarkets_Close_YYYYMMDD.pdf, note_YYYYMMDD.json, facts_YYYYMMDD.json
  2. check them
       broken (missing file, bad JSON, not a PDF, dates disagree): rejected,
         nothing is published and the workflow run fails so GitHub emails you
       not an NYSE trading day, dated in the future, or the figure check
         failed ("Control note." in the PDF): held, opened as a pull request
       otherwise: published straight to main
  3. a newer note for the same session date replaces the older one

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
    """Return (YYYYMMDD, {"pdf": bytes, "note": bytes, "facts": bytes})."""
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
    missing = [k for k in FILES if k not in found]
    if missing:
        raise Rejected("the artifact has no " + " and no ".join(missing) + " file")
    stamps = {stamp for stamp, _ in found.values()}
    if len(stamps) != 1:
        raise Rejected("the PDF and JSON files carry different dates")
    return stamps.pop(), {k: data for k, (_, data) in found.items()}


def finite(v):
    """JSON as the agent writes it may hold NaN; publish null instead."""
    if isinstance(v, float) and not math.isfinite(v):
        return None
    if isinstance(v, dict):
        return {str(k): finite(x) for k, x in v.items()}
    if isinstance(v, list):
        return [finite(x) for x in v]
    return v


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
        note = json.loads(files["note"])
        facts = json.loads(files["facts"])
    except ValueError as e:
        raise Rejected(f"a JSON file does not parse ({e})")
    if not isinstance(note, dict) or not isinstance(facts, dict):
        raise Rejected("a JSON file is not an object")
    try:
        day = dt.date.fromisoformat(str(facts.get("date"))[:10])
    except ValueError:
        raise Rejected("the facts file has no valid session date")
    if day.strftime("%Y%m%d") != stamp:
        raise Rejected(f"the facts file is dated {day} but the files are named {stamp}")
    if not files["pdf"].startswith(b"%PDF-"):
        raise Rejected("the PDF file is not a PDF")

    text = {}
    for field in NOTE_FIELDS:
        v = note.get(field)
        if field in LIST_FIELDS:
            items = v if isinstance(v, list) else []
            text[field] = [t for t in (clean_text(i) for i in items) if t]
        else:
            text[field] = clean_text(v)
    if not text["headline"]:
        raise Rejected("the note has no headline")

    hold = []
    trading = nyse.is_trading_day(day)
    if trading is None:
        hold.append(f"{day.year} is not in the NYSE holiday table in tools/nyse.py, "
                    "so the session date could not be confirmed. Add that year's dates.")
    elif not trading:
        hold.append(f"{day:%A} {day.day} {day:%B %Y} was not an NYSE trading day.")
    if day > today:
        hold.append(f"The note is dated {day}, after today in New York.")

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
        m = re.search(r"Edition\s*(\d{1,6})\b", body)
        edition = m.group(1) if m else None

    record = {
        "date": day.isoformat(),
        "published": True,
        "edition": edition,
        "figure_check": figure_check,
        "pdf": f"AndraMarkets_Close_{stamp}.pdf",
        "facts": f"facts_{stamp}.json",
        "note": text,
        "source": {
            "repo": AGENT_REPO,
            "run_id": (artifact.get("workflow_run") or {}).get("id"),
            "artifact_id": artifact["id"],
            "created_at": artifact["created_at"],
        },
    }
    facts_json = json.dumps(finite(facts), indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    return record, facts_json, hold


# Files and git ---------------------------------------------------------------

def write_note(root, record, pdf, facts_json):
    folder = root / "reports" / record["date"]
    folder.mkdir(parents=True, exist_ok=True)
    for old in list(folder.glob("AndraMarkets_Close_*.pdf")) + list(folder.glob("facts_*.json")):
        old.unlink()
    (folder / record["pdf"]).write_bytes(pdf)
    (folder / record["facts"]).write_text(facts_json, encoding="utf-8")
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
    git("add", "-A", "data", "reports")
    if not git("status", "--porcelain", "data", "reports"):
        return False
    git("commit", "-m", message)
    for attempt in range(4):
        if subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=ROOT).returncode == 0:
            return True
        # Someone edited main meanwhile (the owner in the web editor). Replay.
        git("pull", "--rebase", "origin", "main")
    raise SystemExit("Could not push to main after 4 attempts.")


def open_held_pr(record, pdf, facts_json, reasons, token):
    date, artifact = record["date"], record["source"]["artifact_id"]
    branch = f"held/{date}-{artifact}"
    tmp = Path(tempfile.mkdtemp())
    try:
        git("fetch", "origin", "main")
        git("worktree", "add", "-B", branch, str(tmp), "origin/main")
        write_note(tmp, record, pdf, facts_json)
        git("add", "-A", "data", "reports", cwd=tmp)
        git("commit", "-m", f"Held close note {date} for review", cwd=tmp)
        git("push", "--force", "origin", f"{branch}:{branch}", cwd=tmp)
    finally:
        git("worktree", "remove", "--force", str(tmp), check=False)
        shutil.rmtree(tmp, ignore_errors=True)

    owner = SITE_REPO.split("/")[0]
    open_prs = api(f"/repos/{SITE_REPO}/pulls?state=open&head={owner}:{branch}", token)
    if open_prs:
        return open_prs[0]["html_url"]
    replaces = existing(ROOT, date)
    lines = [
        f"The close note for **{date}** did not pass every check, so it was not published.",
        "",
        "**Why it was held**",
        "",
        *[f"- {r}" for r in reasons],
        "",
        f"**Headline:** {record['note']['headline']}",
        "",
        f"Source: agent run {record['source']['run_id']}, artifact {artifact}.",
        "",
        "**What to do**",
        "",
        "- **Merge** to publish it on the site as it is.",
        "- **Close** to discard it. Nothing is published.",
    ]
    if replaces:
        lines.append(f"- Merging replaces the note already published for {date}.")
    lines += ["", "Open the PDF from the **Files changed** tab to read it first."]
    pr = api(f"/repos/{SITE_REPO}/pulls", token, "POST", {
        "title": f"Held close note: {date}",
        "head": branch,
        "base": "main",
        "body": "\n".join(lines),
    })
    return pr["html_url"]


def close_stale_prs(date, created_at, state, token):
    """A newer note for the date went live: close older held PRs for it."""
    for pr in api(f"/repos/{SITE_REPO}/pulls?state=open&per_page=100", token) or []:
        ref = pr["head"]["ref"]
        if not ref.startswith(f"held/{date}-"):
            continue
        held = state["artifacts"].get(ref.rsplit("-", 1)[-1], {})
        if held.get("created_at", "") >= created_at:
            continue
        api(f"/repos/{SITE_REPO}/issues/{pr['number']}/comments", token, "POST",
            {"body": f"Closed automatically: a newer note for {date} has been published."})
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


def main():
    agent_token = os.environ.get("AGENT_ARTIFACTS_TOKEN")
    site_token = os.environ.get("GITHUB_TOKEN")
    if not agent_token:
        raise SystemExit("AGENT_ARTIFACTS_TOKEN is not set. See README, Publishing the close note.")
    today = dt.datetime.now(ZoneInfo("America/New_York")).date()
    state = load_state(ROOT)
    seen = state["artifacts"]

    try:
        artifacts = [a for a in list_artifacts(agent_token) if str(a["id"]) not in seen]
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Could not list the agent's artifacts (HTTP {e.code}). "
                         "The token may have expired or lost Actions: read access.")
    print(f"{len(artifacts)} new artifact(s) from {AGENT_REPO}")

    published, held, rejected, rows = [], [], [], []
    for a in artifacts:
        entry = {"run_id": (a.get("workflow_run") or {}).get("id"), "created_at": a["created_at"]}
        try:
            stamp, files = unpack(download_zip(a, agent_token))
            record, facts_json, reasons = check(stamp, files, a, today)
        except Rejected as e:
            entry.update(status="rejected", reason=str(e))
            rejected.append((a, str(e)))
            rows.append((a["id"], "", f"rejected: {e}"))
            print(f"::error::Artifact {a['id']} rejected: {e}")
        else:
            entry["date"] = record["date"]
            if reasons:
                entry.update(status="held", reasons=reasons)
                held.append((record, files["pdf"], facts_json, reasons))
                rows.append((a["id"], record["date"], "held: " + " ".join(reasons)))
            else:
                prev = existing(ROOT, record["date"])
                if prev and prev["source"]["created_at"] > a["created_at"]:
                    entry["status"] = "superseded"
                    rows.append((a["id"], record["date"], "skipped, a newer note is live"))
                else:
                    if prev and prev.get("published") is False:
                        # The owner withdrew this date by hand. Keep it withdrawn.
                        record["published"] = False
                    write_note(ROOT, record, files["pdf"], facts_json)
                    entry["status"] = "published"
                    published.append(record)
                    rows.append((a["id"], record["date"],
                                 "replaced the earlier note" if prev else "published"))
        seen[str(a["id"])] = entry

    failed = 0
    for record, pdf, facts_json, reasons in held:
        key = str(record["source"]["artifact_id"])
        try:
            if not site_token:
                raise RuntimeError("GITHUB_TOKEN is not set")
            seen[key]["pr"] = open_held_pr(record, pdf, facts_json, reasons, site_token)
            print(f"Held {record['date']}: {seen[key]['pr']}")
        except Exception as e:  # noqa: BLE001
            # Not recorded as seen, so the next run tries again.
            del seen[key]
            failed += 1
            print(f"::error::Could not open the review pull request for {record['date']}: {e}. "
                  "Check Settings, Actions, General: Allow GitHub Actions to create "
                  "and approve pull requests.")

    save_state(ROOT, state)
    dates = sorted({r["date"] for r in published})
    message = (f"Publish close note{'s' if len(dates) > 1 else ''} {', '.join(dates)}"
               if dates else "Record imported agent artifacts")
    pushed = push_main(message) if artifacts else False

    if site_token:
        for record in published:
            close_stale_prs(record["date"], record["source"]["created_at"], state, site_token)

    summary(rows)
    output("published", "true" if published and pushed else "false")
    print(f"published {len(published)}, held {len(held) - failed}, rejected {len(rejected)}")
    return 1 if rejected or failed else 0


if __name__ == "__main__":
    sys.exit(main())
