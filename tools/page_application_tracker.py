"""Application tracker (application-tracker/): the reader's own applications, in their browser.

Owner-approved sketch, 1 Nov 2026. The page carries the Recruiting calendar's programmes
(firm, programme, cycle, the official closing date or the calendar's words for its window,
apply link), embedded at build time from data/recruiting_calendar.json as a JSON data block;
assets/tracker.js does the rest in the browser: add programmes from that list or your own,
move each through To apply, Applied, Interview and Offer, and keep deadlines, the next step,
contacts and notes. Everything the reader enters stays in localStorage on their device and is
never sent: the page loads nothing from other sites. Without JavaScript the page says the
tracker needs it and links to the Recruiting calendar.
"""
import datetime as dt
import json

import page_firms

STATUSES = [("toapply", "To apply", "Nothing here yet. Add a programme from the Recruiting calendar, or one of your own."),
            ("applied", "Applied", "No applications sent yet."),
            ("interview", "Interview", "No interviews yet."),
            ("offer", "Offer", "No offers yet.")]


def programmes(site, rows, today):
    """The calendar's programmes for the picker, in its by-firm order. closes is the firm's
    own closing date (ISO) when the calendar has one; otherwise win holds the calendar's
    words for the window ("Expected Feb 2027", "Rolling", "Not announced")."""
    out, seen = [], set()
    for firm, rs in page_firms.by_firm(site, rows).items():
        for r in rs:
            key = f"{page_firms.slug(firm)}/{page_firms.slug(r['programme'])}"[:120]
            n, base = 2, key
            while key in seen:
                key, n = f"{base}-{n}", n + 1
            seen.add(key)
            closes = r.get("closes") or ""
            out.append({
                "id": key, "firm": firm, "prog": r["programme"], "cycle": page_firms.cycle(site, r),
                "closes": closes, "win": "" if closes else page_firms.window(site, r, "closes", today),
                "url": r.get("url") or "", "re": bool(r.get("verified")), "f": page_firms.slug(firm),
            })
    return out


def data_block(payload):
    """A JSON data block no text can break out of (the browser never runs it)."""
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    raw = raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f'<script type="application/json" id="at-data">{raw}</script>'


def pages(site):
    """{output path: page HTML}. site is tools/build_site.py, for shell(), icon() and the loaders."""
    rows = site.load_recruiting()
    today = dt.datetime.now(site.NY).date()
    progs = programmes(site, rows, today)
    _, checked = page_firms.checked_line(site, rows)
    icon = site.icon
    caret = icon("caret-down")
    status_opts = "".join(f'<option value="{k}">{name}</option>' for k, name, _ in STATUSES)

    cols = "".join(
        f'<section class="at-col" data-status="{k}" aria-labelledby="at-h-{k}">'
        f'<h2 class="at-col__h" id="at-h-{k}">{name}<span class="visually-hidden">,</span> <span class="at-n">0</span></h2>'
        f'<p class="at-none">{none}</p><ol class="at-list"></ol></section>'
        for k, name, none in STATUSES)
    source = (f'Programmes and dates from the <a href="../recruiting-calendar/">Recruiting calendar</a>, checked {checked}'
              if checked else 'Programmes and dates from the <a href="../recruiting-calendar/">Recruiting calendar</a>')
    pick_unit = f"{len(progs)} programmes, type to narrow them" if progs else "Data pending"

    body = f"""<main id="main" class="page at">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Application tracker</h1>
      <p class="lede">Your applications in one place: what to apply for, what you have sent, interviews and offers, with deadlines, the next step, contacts and notes.</p>
      <p class="note__meta"><span>Saved only in this browser, never sent</span><span>{source}</span></p>
    </header>
    <div class="at-nojs">
      <p>The tracker runs in your browser and needs JavaScript, which is off or blocked here. Every programme and date is in the <a href="../recruiting-calendar/">Recruiting calendar</a>.</p>
    </div>
    <div class="at-app" hidden>
      <div class="at-bar">
        <button type="button" class="btn at-add" aria-haspopup="dialog" aria-controls="at-adddlg"><span class="at-plus" aria-hidden="true"></span>Add from the Recruiting calendar</button>
      </div>
      <div class="at-warn" hidden>{icon("warning-circle")}<div><p class="at-warn__t">This browser is not keeping your entries.</p><p>Its storage is blocked or full (a private window, or site data turned off), so what you add here lasts only until you close or reload the page. Export a copy before you leave.</p></div></div>
      <p class="visually-hidden" id="at-live" role="status" aria-live="polite"></p>
      <div class="at-board">{cols}</div>
      <div class="at-foot">
        <p class="at-foot__t">Saved only in this browser. Nothing you enter is sent.</p>
        <div class="at-foot__acts">
          <button type="button" class="btn btn--ghost btn--sm at-export">Export a copy</button>
          <button type="button" class="btn btn--ghost btn--sm at-import">Import a copy</button>
          <input type="file" class="at-file" accept=".json,application/json" hidden>
          <button type="button" class="btn btn--ghost btn--sm at-clear">Delete all</button>
        </div>
        <p class="at-foot__st" role="status" aria-live="polite"></p>
      </div>
    </div>
    <div class="page__body">
      <section aria-labelledby="at-how"><h2 id="at-how">How it works</h2><p>Add a programme from the Recruiting calendar and it comes with the closing date the firm has posted; where there is none yet, the card shows the calendar's expected window, rolling review or "Not announced". You can change any date, and a date you set is marked as yours. Add anything else as your own, with a firm and a role.</p><p>Move each application through To apply, Applied, Interview and Offer with its Status menu. In each column the nearest date comes first, and a deadline within two weeks counts down, as on the calendar. Details hold the date you applied, the next step and its date, your contacts and your notes.</p></section>
      <section aria-labelledby="at-priv"><h2 id="at-priv">Kept in this browser</h2><p>What you enter is saved in this browser's storage on this device, and only there. It is never sent to Andra Markets or anyone else: there is no account and no server behind the tracker, and the page loads nothing from other sites. Clearing this site's data in your browser deletes it, and so does closing a private window. To keep a copy, or to move to another device, export it as a file and import it there.</p><p>For information only: always confirm dates on the firm's site.</p></section>
    </div>
  </div>
</main>
<dialog class="at-dlg" id="at-adddlg" aria-labelledby="at-a-h">
  <div class="at-dlg__panel">
    <div class="at-dlg__head"><h2 class="at-dlg__title" id="at-a-h">Add an application</h2><button type="button" class="at-x" data-close aria-label="Close">{icon("x")}</button></div>
    <div class="at-sec at-pick">
      <label for="at-q">From the Recruiting calendar <span class="at-unit">{pick_unit}</span></label>
      <input id="at-q" type="search" role="combobox" aria-expanded="true" aria-controls="at-opts" aria-autocomplete="list" aria-describedby="at-q-st" autocomplete="off" spellcheck="false" placeholder="Firm or programme">
      <ul class="at-opts" id="at-opts" role="listbox" aria-label="Programmes in the Recruiting calendar"></ul>
      <p class="at-qst" id="at-q-st" role="status" aria-live="polite"></p>
    </div>
    <form class="at-sec at-own" novalidate>
      <h3 class="at-sec__h">Or add your own</h3>
      <div class="at-fields">
        <div class="at-field"><label for="at-o-firm">Firm</label><input id="at-o-firm" type="text" maxlength="120" autocomplete="organization"></div>
        <div class="at-field"><label for="at-o-role">Programme or role</label><input id="at-o-role" type="text" maxlength="200"></div>
        <div class="at-field"><label for="at-o-dl">Deadline <span class="at-unit">optional</span></label><input id="at-o-dl" type="date"></div>
      </div>
      <p class="at-err" role="status" aria-live="polite"></p>
      <button type="submit" class="btn btn--ghost">Add to the tracker</button>
    </form>
    <div class="at-dlg__foot"><span></span><button type="button" class="btn" data-close>Done</button></div>
  </div>
</dialog>
<dialog class="at-dlg" id="at-editdlg" aria-labelledby="at-e-h">
  <form class="at-dlg__panel" novalidate>
    <div class="at-dlg__head"><div><h2 class="at-dlg__title" id="at-e-h"></h2><p class="at-dlg__sub" id="at-e-sub"></p></div><button type="button" class="at-x" data-close aria-label="Close">{icon("x")}</button></div>
    <p class="at-dlg__links"></p>
    <div class="at-sec">
      <div class="at-fields">
        <div class="at-field"><label for="at-e-status">Status</label><span class="at-select"><select id="at-e-status">{status_opts}</select>{caret}</span></div>
        <div class="at-field"><label for="at-e-dl">Deadline</label><input id="at-e-dl" type="date" aria-describedby="at-e-dl-src"><p class="at-hint" id="at-e-dl-src"></p><button type="button" class="at-textbtn at-e-cal" hidden>Use the calendar's date</button></div>
        <div class="at-field"><label for="at-e-applied">Date applied</label><input id="at-e-applied" type="date"></div>
      </div>
      <div class="at-fields at-fields--next">
        <div class="at-field"><label for="at-e-next">Next step</label><input id="at-e-next" type="text" maxlength="120" placeholder="Online test, first round, superday"></div>
        <div class="at-field"><label for="at-e-nextd">Date of the next step</label><input id="at-e-nextd" type="date"></div>
      </div>
    </div>
    <fieldset class="at-sec at-contacts"><legend class="at-sec__h">Contacts</legend><ol class="at-clist"></ol><button type="button" class="btn btn--ghost btn--sm at-c-add">Add a contact</button></fieldset>
    <div class="at-sec at-field"><label for="at-e-notes">Notes</label><textarea id="at-e-notes" rows="5" maxlength="4000"></textarea></div>
    <div class="at-sec">
      <div class="at-fields at-fields--name">
        <div class="at-field"><label for="at-e-firm">Firm</label><input id="at-e-firm" type="text" maxlength="120" aria-describedby="at-e-name-err"></div>
        <div class="at-field"><label for="at-e-role">Programme or role</label><input id="at-e-role" type="text" maxlength="200" aria-describedby="at-e-name-err"></div>
      </div>
      <p class="at-err" id="at-e-name-err" role="status" aria-live="polite"></p>
    </div>
    <p class="at-dlg__note">Changes are saved as you make them, in this browser only.</p>
    <div class="at-dlg__foot"><button type="button" class="btn btn--ghost at-del">Delete this application</button><button type="button" class="btn" data-close>Done</button></div>
  </form>
</dialog>
<dialog class="at-dlg at-dlg--sm" id="at-confirm" role="alertdialog" aria-labelledby="at-c-h" aria-describedby="at-c-p">
  <div class="at-dlg__panel">
    <h2 class="at-dlg__title" id="at-c-h"></h2>
    <p class="at-dlg__sub" id="at-c-p"></p>
    <div class="at-dlg__acts"><button type="button" class="btn at-c-yes"></button><button type="button" class="btn btn--ghost at-c-no"></button></div>
  </div>
</dialog>
{data_block({"checked": checked, "progs": progs})}"""
    return {"application-tracker/": site.shell(
        title="Application tracker: Andra Markets",
        desc="Track your applications to banks, boutiques, asset managers, hedge funds and trading firms: deadlines from the Recruiting calendar, status, contacts and notes, kept only in your browser.",
        body=body, home="../", base="../", path="application-tracker/", scripts=("tracker.js",))}
