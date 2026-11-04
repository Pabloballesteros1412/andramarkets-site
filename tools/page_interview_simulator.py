"""Interview simulator (interview-simulator/): a timed mock interview, answered aloud.

Owner-approved format (1 Nov 2026): pick a track (IB, S&T, AM/ER) and a length (10, 20
or 30 minutes); each question appears with a countdown, you answer aloud (notes
optional), then see the model answer and its key points and rate yourself (Nailed it,
Partly, Missed). At the end, a result by topic with links to the pages to review.
assets/interview-sim.js runs it in the browser: no microphone, nothing recorded or
sent; progress and best results stay in localStorage.

Questions are used as they are, from two places:
- the nine technical topics, data/technicals/<topic>.json (the practice cards);
- data/interview_prep.json: its question bank (one topic per subject) and its weekly
  block ("week": each topic's title and "Say it in an interview" text, with the dates
  of the close notes its figures come from). The weekly block is offered only while it
  is under two weeks old, so a stale week never shows as this week's.

data/interview_simulator.json is kept by hand (see its *_rule fields):
- Tracks: a question belongs to every track that lists its topic.
- Review page: the page the question comes from, a technical topic's training page
  (../break-into-wall-street/technicals/<topic>/) or the Interview Prep question bank
  (../interview-prep/#ip-bank; the weekly block: ../interview-prep/#ip-week).
- Length: "lengths" gives the number of questions for 10, 20 and 30 minutes; each
  question has answer_seconds on the clock, and the rest of the time is for checking.
- Same: questions that ask the same thing in two files; one interview draws one of them.
- Key points: two to four short phrases from each model answer's own words. A key point
  is kept only if every figure in it, and every word of three letters or more that is
  not a filler word, appears in that answer; the build prints the ones it drops.
"""
import datetime as dt
import hashlib
import json
import re

FILLER = set("""a an the and or of to in on at for by with from as is are be it its not you your
what how why when then than this that these those can may do does was were has have had but if
so all any one each per which who there their they them we me my yes no""".split())
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
WEEK_DAYS = 14  # the weekly block is offered while it is younger than this


def _norm(text):
    return text.lower().replace("−", "-").replace("’", "'")


def _blocks_bank(text):
    """A bank answer: paragraphs split by a blank line; a block of "1. " lines is a numbered
    list (as ip_blocks() in build_site.py renders it on Interview Prep)."""
    out = []
    for block in text.strip().split("\n\n"):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if lines and all(re.match(r"\d+\. ", ln) for ln in lines):
            out.append(["ol", [re.sub(r"^\d+\. ", "", ln) for ln in lines]])
        elif lines:
            out.append(["p", " ".join(lines)])
    return out


def _plain(blocks):
    return " ".join(b[1] if b[0] == "p" else " ".join(b[1]) for b in blocks)


def _key_points(points, answer, where, warn):
    """Keep a key point only if its figures and its words are in the model answer."""
    text = _norm(answer)
    figures = set(NUMBER.findall(text))
    kept = []
    for p in points:
        low = _norm(p)
        missing = [n for n in NUMBER.findall(low) if n not in figures]
        missing += [w for w in re.findall(r"[a-z]+", low) if len(w) > 2 and w not in FILLER and w not in text]
        if missing:
            warn(f"key point dropped ({where}): {p!r}; not in the answer: {', '.join(missing)}")
        else:
            kept.append(p)
    return kept


def _qid(topic, question):
    return hashlib.sha1(f"{topic}|{question}".encode("utf-8")).hexdigest()[:10]


def _join(names):
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def load(site, today=None):
    """The simulator's data: tracks, lengths, topics and questions, checked."""
    warnings = []

    def warn(msg):
        warnings.append(msg)

    cfg = json.loads((site.ROOT / "data" / "interview_simulator.json").read_text(encoding="utf-8"))
    kp = cfg.get("key_points", {})
    topics, questions = {}, []

    def add(topic, q, blocks, follow="", kp_file=None, ctx="", sources=None, qid=None):
        points = []
        if kp_file is not None:
            if q in kp.get(kp_file, {}):
                points = _key_points(kp[kp_file][q], _plain(blocks), f"{kp_file}: {q}", warn)
            else:
                warn(f"no key points for {kp_file}: {q}")
        questions.append({"id": qid or _qid(topic, q), "t": topic, "q": q, "a": blocks, "f": follow, "k": points,
                          "c": ctx, "s": sources or []})

    for t in site.load_technicals():
        slug = t["slug"]
        topics[slug] = {"id": slug, "name": t["name"], "src": "Technical preparation",
                        "href": f"../break-into-wall-street/technicals/{slug}/"}
        for x in t["questions"]:
            add(slug, x["q"], [["p", p] for p in x["a"]], x.get("follow", ""), slug)

    ip = json.loads(site.IPREP.read_text(encoding="utf-8"))
    for c in ip["categories"]:
        topics[f"ip-{c['id']}"] = {"id": f"ip-{c['id']}", "name": c["name"], "src": "Interview Prep question bank",
                                   "href": "../interview-prep/#ip-bank"}
    for x in ip["questions"]:
        add(f"ip-{x['cat']}", x["q"], _blocks_bank(x["a"]), x.get("follow", ""), "interview-prep")

    # The weekly block, as it is: its title, its "say" text and its close-note dates.
    week = ip.get("week") or {}
    today = today or dt.date.today()
    if week.get("topics") and week.get("updated"):
        updated = dt.date.fromisoformat(week["updated"])
        monday = dt.date.fromisoformat(week["of"])
        if (today - updated).days < WEEK_DAYS:
            published = {rec["date"] for rec in site.load_notes()}
            topics["ip-week"] = {"id": "ip-week", "name": "This week's markets",
                                 "src": f"Interview Prep, week of {site.day_med(monday)}",
                                 "href": "../interview-prep/#ip-week"}
            for w in week["topics"]:
                srcs = []
                for day in w.get("sources", []):
                    d = dt.date.fromisoformat(day)
                    srcs.append([f"{d.day} {d:%b}", f"../reports/{day}/" if day in published else ""])
                add("ip-week", "What moved markets this week? Talk me through this story.", [["p", w["say"]]],
                    ctx=w["title"], sources=srcs, qid=_qid("ip-week", w["title"]))
        else:
            warn(f"weekly block of {week['of']} is {(today - updated).days} days old: left out")

    # Key points written for a question that no longer exists (its wording changed).
    asked = {(q["t"] if not q["t"].startswith("ip-") else "interview-prep", q["q"]) for q in questions}
    for f, entries in kp.items():
        for q in entries:
            if (f, q) not in asked:
                warn(f"key points for a question not found: {f}: {q}")

    # Questions that ask the same thing share a group: one interview draws one of them.
    by_ref = {(q["t"], q["q"]): q for q in questions}
    for i, group in enumerate(cfg.get("same", [])):
        for ref in group:
            q = by_ref.get(tuple(ref))
            if q:
                q["g"] = f"g{i}"
            else:
                warn(f"same-question group {i + 1}: not found: {ref[0]}: {ref[1]}")

    counts = {}
    for q in questions:
        counts[q["t"]] = counts.get(q["t"], 0) + 1
    tracks = []
    for tr in cfg["tracks"]:
        for t in tr["topics"]:
            if t not in topics and t != "ip-week":
                warn(f"track {tr['id']}: unknown topic {t}")
        tracks.append({"id": tr["id"], "chip": tr["chip"], "name": tr["name"],
                       "topics": [t for t in tr["topics"] if counts.get(t)]})
    for t in topics.values():
        t["n"] = counts.get(t["id"], 0)
        t["tracks"] = [tr["id"] for tr in tracks if t["id"] in tr["topics"]]
    for msg in warnings:
        print(f"interview simulator: {msg}")
    return {"secs": int(cfg["answer_seconds"]), "lengths": cfg["lengths"], "tracks": tracks,
            "topics": topics, "qs": questions, "warnings": warnings}


def _words_secs(secs):
    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}
    if secs % 60 == 0 and secs // 60 in words:
        m = secs // 60
        return f"{words[m]} minute{'s' if m > 1 else ''}"
    return f"{secs // 60}:{secs % 60:02d}"


def pages(site):
    """{output path: page HTML}. site is tools/build_site.py, for shell(), icon() and the loaders."""
    esc = site.esc
    d = load(site)
    tracks, topics, qs = d["tracks"], d["topics"], d["qs"]
    secs_words = _words_secs(d["secs"])
    default_len = d["lengths"][1]["minutes"] if len(d["lengths"]) > 1 else d["lengths"][0]["minutes"]
    tr0 = tracks[0]
    n0 = next(x["questions"] for x in d["lengths"] if x["minutes"] == default_len)

    track_chips = "".join(
        f'<button type="button" class="chip" data-isim-track="{t["id"]}" aria-pressed="{"true" if i == 0 else "false"}">{esc(t["chip"])}</button>'
        for i, t in enumerate(tracks))
    len_chips = "".join(
        f'<button type="button" class="chip" data-isim-len="{x["minutes"]}" aria-pressed="{"true" if x["minutes"] == default_len else "false"}">{x["minutes"]} min</button>'
        for x in d["lengths"])
    names0 = _join([topics[t]["name"] for t in tr0["topics"]])
    ready = (f'<p class="tq-card__meta"><span>{n0} questions</span><span>{secs_words.capitalize()} each</span>'
             f'<span class="isim__time">{d["secs"] // 60}:{d["secs"] % 60:02d}</span></p>'
             f'<h3 class="tq-card__q isim__h" tabindex="-1">{esc(tr0["name"])}</h3>'
             f'<p class="isim__txt">{n0} questions from {esc(names0)}. Answer each one aloud, as you would in the room. '
             f'When you are ready, or when the clock runs out, show the model answer, check it against its key points and rate yourself.</p>'
             f'<div class="isim__acts isim__acts--start"><button type="button" class="btn" data-act="start">Start the interview</button></div>')

    payload = {"secs": d["secs"], "lengths": d["lengths"], "tracks": tracks,
               "topics": {k: {"name": v["name"], "src": v["src"], "href": v["href"]} for k, v in topics.items()},
               "qs": [{k: v for k, v in q.items() if v not in ("", [], None)} for q in qs]}
    data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")

    # What each track covers: the documented rule, and the way in without JavaScript.
    order = [t for t in topics if not t.startswith("ip-")] + [t for t in topics if t.startswith("ip-")]
    chip_of = {t["id"]: t["chip"] for t in tracks}
    rows = ""
    for tid in order:
        t = topics[tid]
        if not t["n"]:
            continue
        tags = "".join(f'<span class="tag">{esc(chip_of[x])}</span>' for x in t["tracks"]) or '<span class="isim-cov__none">None</span>'
        rows += (f'<tr><th scope="row"><a href="{t["href"]}">{esc(t["name"])}</a><span>{esc(t["src"])}</span></th>'
                 f'<td class="num">{t["n"]}</td><td class="isim-cov__tracks">{tags}</td></tr>')
    first, *more = d["lengths"]
    lengths = _join([f'{first["minutes"]} minutes is {first["questions"]} questions']
                    + [f'{x["minutes"]} minutes {x["questions"]}' for x in more])
    track_rule = "".join(
        f'<li><b>{esc(t["chip"])}</b> <span>{esc(t["name"])}</span>: {esc(_join([topics[x]["name"] for x in t["topics"]]))}.</li>'
        for t in tracks)
    total = len(qs)
    in_topics = sum(1 for t in topics.values() if t["n"])

    body = f"""<main id="main" class="page isim">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Interview simulator</h1>
      <p class="lede">A timed mock interview, answered aloud. Choose a track and a length; each question has its clock, then the model answer and its key points, and you rate yourself.</p>
      <p class="note__meta"><span>{total} questions in {in_topics} topics</span><span>Your progress stays in this browser</span></p>
    </header>
    <section class="isim__sim" id="isim" aria-labelledby="isim-title">
      <h2 class="visually-hidden" id="isim-title">Mock interview</h2>
      <div class="tq-js">
        <div class="isim__ctl" id="isim-ctl">
          <div class="dd__cgroup"><span class="cl__glabel" id="isim-t-l">Track</span><div class="filters" role="group" aria-labelledby="isim-t-l">{track_chips}</div></div>
          <div class="dd__cgroup"><span class="cl__glabel" id="isim-l-l">Length</span><div class="filters" role="group" aria-labelledby="isim-l-l">{len_chips}</div></div>
        </div>
        <article class="tq-card isim__card" id="isim-card" aria-labelledby="isim-title">{ready}</article>
        <p class="visually-hidden" id="isim-live" aria-live="polite"></p>
        <p class="isim__local">Progress and best results stay in this browser only. Nothing you say or type is recorded or sent. <button type="button" class="tq-reset" id="isim-clear">Clear saved progress</button></p>
      </div>
      <p class="tq-nojs isim__nojs">The simulator needs JavaScript. Every question and its model answer are on the pages listed under What each track covers, below.</p>
      <script type="application/json" id="isim-data">{data}</script>
    </section>
    <div class="page__body">
      <section aria-labelledby="isim-how">
        <h2 id="isim-how">How it works</h2>
        <p>Each question has {secs_words} on the clock. Answer aloud, as you would in the room, and jot notes if they help. When you are done, or when the time is up, show the model answer, check it against its key points and rate yourself: Nailed it, Partly or Missed. The clock never moves you on.</p>
        <p>{lengths}: {secs_words} to answer each, and the rest to check it. Questions are drawn at random and spread evenly across the track's topics, those you have not had yet first, and never the same question twice.</p>
        <p>At the end you see each topic's ratings and the page to review: the topic's technical preparation page, or the Interview Prep question bank. The score counts Nailed it as one and Partly as half.</p>
        <p>The key points are taken from the model answer's own words. Model answers are a starting point: say them in your own words. Questions on this week's markets carry the dates of the close notes their figures come from.</p>
        <p>The page never uses the microphone and records nothing. Notes are not saved. Your progress, the questions you have had and your best results stay in this browser only.</p>
        <p>Educational material. Not investment advice.</p>
      </section>
      <section aria-labelledby="isim-cov">
        <h2 id="isim-cov">What each track covers</h2>
        <ul class="isim-tracks">{track_rule}</ul>
        <div class="isim-cov__wrap"><table class="isim-cov">
          <caption class="visually-hidden">Topics, their questions and tracks</caption>
          <thead><tr><th scope="col">Topic and page to review</th><th scope="col" class="num">Questions</th><th scope="col">Tracks</th></tr></thead>
          <tbody>{rows}</tbody>
        </table></div>
      </section>
    </div>
  </div>
</main>"""
    return {"interview-simulator/": site.shell(
        title="Interview simulator: Andra Markets",
        desc="A timed mock interview for IB, S&amp;T and asset management: answer aloud, check the model answer and its key points, and see your result by topic.",
        body=body, home="../", base="../", path="interview-simulator/", scripts=("interview-sim.js",))}
