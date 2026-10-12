#!/usr/bin/env python3
"""Temporary diagnostic: what the agent's figure check flags in each held run.

Re-applies the agent's own audit (andra/narrative.py: same number pattern,
permitted set and 2% tolerance) to the run's final text and fact pack.
"""
import io, json, os, re, sys, zipfile
sys.path.insert(0, os.path.dirname(__file__))
import import_notes as m
import pdf_note

RUNS = [32530195378, 32544612904, 32900041440, 33017490040, 33123892754, 33455683795,
        33690084080, 33814031226, 34287405560, 34537600553, 34648426208, 34909074715,
        35026847006, 35279900498, 35400256673, 35794037679, 36188375899, 36273633718,
        36352393921, 36491134602, 36633541740, 36782255591, 37155987401, 37841586991]
TOL = 0.02
# Corrected tokenizer: ASCII digits only, whole numbers with or without commas.
NUM = re.compile(r"(?<![\w.])[-+−]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?![\w])", re.A)
# Numbers that are part of a name, not a figure.
NAMES = re.compile(r"(S&P(?: MidCap)? \d+|Russell \d+|CSI ?\d+|ASX \d+|Nikkei \d+|EURO STOXX \d+|DAX \d+|CAC \d+|FTSE(?: MIB| 100)?|IBEX \d+|Nasdaq \d+|SX5E|\d+-\d+ year|\d+-year|\d+-month|\d+-day|\d+y\d+y|\d+s\d+s|\dm\d+y|VIX\d*D?|VIX ?\d+-\w+|20\d\d)")

def notice(title, text):
    text = text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::notice title={title}::{text[:4000]}")

def facts_values(facts):
    vals = []
    def walk(o, path):
        if isinstance(o, dict):
            name = o.get("name") or o.get("key")
            for k, v in o.items():
                walk(v, f"{path}.{name}.{k}" if name and k not in ("name", "key") else f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, path)
        elif isinstance(o, (int, float)) and not isinstance(o, bool):
            vals.append((float(o), path.strip(".")))
    walk(facts, "")
    return vals

def permitted(vals):
    out = set()
    for v, _ in vals:
        out |= {round(v, 2), round(abs(v), 2), round(v, 1), round(v, 0)}
    out |= {float(x) for x in range(0, 101)}
    out |= {1900.0 + i for i in range(220)}
    return out

token = os.environ["AGENT_ARTIFACTS_TOKEN"]
by_run = {(a.get("workflow_run") or {}).get("id"): a for a in m.list_artifacts(token)}
lines, counts = [], []
for run in RUNS:
    a = by_run[run]
    z = zipfile.ZipFile(io.BytesIO(m.download_zip(a, token)))
    names = z.namelist()
    get = lambda pre: next((n for n in names if n.startswith(pre) and "/" not in n), None)
    facts = json.loads(z.read(get("facts_")))
    if get("note_"):
        note = json.loads(z.read(get("note_")))
        site = {k: note.get(k) for k in m.NOTE_FIELDS}
        social = {"linkedin": note.get("linkedin") or "", "tiktok": note.get("tiktok") or ""}
    else:
        site = pdf_note.extract(z.read(get("AndraMarkets_Close_")))
        social = {"linkedin": z.read(get("linkedin_caption_")).decode(),
                  "tiktok": z.read(get("tiktok_caption_")).decode().split("\n---\n")[-1]}
    vals = facts_values(facts)
    allowed = permitted(vals)
    n_site = n_social = 0
    for where, fields in (("site", site), ("social", social)):
        for field, v in fields.items():
            text = v if isinstance(v, str) else " ".join(map(str, v or []))
            text = NAMES.sub(lambda mm: "#" * len(mm.group()), text or "")
            for mm in NUM.finditer(text):
                n = float(mm.group().replace(",", "").replace("−", "-"))
                if any(abs(n - p) <= max(TOL, abs(p) * TOL) for p in allowed):
                    continue
                near = min(vals, key=lambda x: abs(abs(x[0]) - abs(n))) if vals else (None, "")
                raw = v if isinstance(v, str) else " ".join(map(str, v or []))
                ctx = " ".join(raw[max(0, mm.start() - 50):mm.end() + 20].split())
                lines.append(f"{facts.get('date')} | {where}:{field} | {mm.group()} | ...{ctx}... | nearest fact {near[1]}={near[0]:g}")
                if where == "site": n_site += 1
                else: n_social += 1
    counts.append(f"{facts.get('date')} run {run}: {n_site} on the site text, {n_social} in social captions")
notice("counts", "\n".join(counts))
buf, chunks = "", []
for ln in lines:
    if len(buf) + len(ln) > 3900:
        chunks.append(buf); buf = ""
    buf += ln + "\n"
chunks.append(buf)
for i, c in enumerate(chunks[:9]):
    notice(f"flags {i+1}/{len(chunks)}", c)
