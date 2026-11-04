// Application tracker (application-tracker/): the reader's own applications, kept in
// this browser's localStorage and never sent anywhere. The Recruiting calendar's
// programmes and closing dates are embedded in the page at build time (#at-data).
// Without storage the tracker still works until the page is closed, and says so.
(function () {
  "use strict";
  var app = document.querySelector(".at-app");
  var dataEl = document.getElementById("at-data");
  if (!app || !dataEl) return;

  var CAL = { progs: [] };
  try { CAL = JSON.parse(dataEl.textContent) || CAL; } catch (e) { /* the picker stays empty */ }
  var PROGS = Array.isArray(CAL.progs) ? CAL.progs : [];
  var BY = {};
  PROGS.forEach(function (p) { BY[p.id] = p; });

  var KEY = "andra-tracker";
  var ST = [["toapply", "To apply"], ["applied", "Applied"], ["interview", "Interview"], ["offer", "Offer"]];
  var ST_NAME = {};
  ST.forEach(function (s) { ST_NAME[s[0]] = s[1]; });
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var base = document.body.getAttribute("data-base") || "../";

  // Today in New York, as the Recruiting calendar counts.
  var ny = new Date(new Date().toLocaleString("en-US", { timeZone: "America/New_York" }));
  var TODAY = Date.UTC(ny.getFullYear(), ny.getMonth(), ny.getDate());
  var TODAY_ISO = new Date(TODAY).toISOString().slice(0, 10);

  function isDate(s) { return typeof s === "string" && /^\d{4}-\d{2}-\d{2}$/.test(s) && !isNaN(Date.parse(s)); }
  function days(s) { return Math.round((Date.parse(s) - TODAY) / 864e5); }
  function fmt(s) { var d = new Date(Date.parse(s)); return d.getUTCDate() + " " + MON[d.getUTCMonth()] + " " + d.getUTCFullYear(); }
  function esc(t) {
    return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function str(v, n) { return typeof v === "string" ? v.slice(0, n) : ""; }
  function plural(n, one, many) { return n + " " + (n === 1 ? one : many); }
  function newId() { return "a" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8); }
  function norm(t) {
    t = String(t).toLowerCase();
    return t.normalize ? t.normalize("NFD").replace(/[̀-ͯ]/g, "") : t;
  }

  // Storage: every access in try/catch; the page works without it -------------------

  var stored = (function () {
    try {
      var k = KEY + ":probe";
      localStorage.setItem(k, "1");
      localStorage.removeItem(k);
      return true;
    } catch (e) {
      return false;
    }
  })();
  var warnEl = app.querySelector(".at-warn");
  function warn() { warnEl.hidden = stored; }

  // An entry as the tracker keeps it, from storage or an imported file: anything
  // else in it is dropped, and text is cut to length.
  function tidy(list) {
    if (!Array.isArray(list)) return [];
    var out = [], seen = {};
    list.slice(0, 500).forEach(function (a) {
      if (!a || typeof a !== "object") return;
      var firm = str(a.firm, 120).trim(), role = str(a.role, 200).trim();
      if (!firm || !role) return;
      var id = /^[a-z0-9]{4,40}$/.test(a.id) && !seen[a.id] ? a.id : newId();
      seen[id] = 1;
      var cal = a.cal && typeof a.cal === "object" ? a.cal : {};
      out.push({
        id: id,
        ref: str(a.ref, 200),
        firm: firm,
        role: role,
        url: /^https?:\/\//i.test(str(a.url, 600).trim()) ? str(a.url, 600).trim() : "",
        status: ST_NAME[a.status] ? a.status : "toapply",
        own: !!a.own,
        deadline: isDate(a.deadline) ? a.deadline : "",
        cal: { closes: isDate(cal.closes) ? cal.closes : "", win: str(cal.win, 80) },
        applied: isDate(a.applied) ? a.applied : "",
        next: str(a.next, 120),
        nextDate: isDate(a.nextDate) ? a.nextDate : "",
        contacts: (Array.isArray(a.contacts) ? a.contacts : []).slice(0, 20).map(function (c) {
          c = c && typeof c === "object" ? c : {};
          return { name: str(c.name, 120), role: str(c.role, 120), reach: str(c.reach, 200) };
        }),
        notes: str(a.notes, 4000),
        added: isDate(a.added) ? a.added : "",
      });
    });
    return out;
  }
  function read() {
    if (!stored) return [];
    try {
      var raw = localStorage.getItem(KEY);
      return raw ? tidy((JSON.parse(raw) || {}).apps) : [];
    } catch (e) {
      return [];
    }
  }
  function write() {
    if (!stored) return;
    try {
      localStorage.setItem(KEY, JSON.stringify({ v: 1, apps: apps }));
    } catch (e) {
      stored = false;
      warn();
    }
  }

  var apps = read();

  // Dates: the reader's own, else the calendar's ---------------------------------

  // The calendar's word on a programme: today's data when the programme is still in
  // it, else what it said when the entry was added.
  function cal(a) {
    if (!a.ref) return null;
    var p = BY[a.ref];
    return p ? { closes: p.closes, win: p.win, re: p.re, url: p.url, f: p.f } : { closes: a.cal.closes, win: a.cal.win, re: false, old: true };
  }
  function due(a) {
    var c = cal(a);
    if (a.own) return { iso: a.deadline, txt: "", src: a.deadline ? "own" : "", c: c };
    if (c && c.closes) return { iso: c.closes, txt: "", src: "cal", c: c };
    if (c && c.win) return { iso: "", txt: c.win, src: "cal", c: c };
    return { iso: "", txt: "", src: "", c: c };
  }
  function soon(s) {
    var n = days(s);
    if (n < 0) return "Closed";
    if (n > 14) return "";
    return n === 0 ? "Closes today" : "Closes in " + plural(n, "day", "days");
  }
  function soonNext(s) {
    var n = days(s);
    if (n < 0 || n > 14) return "";
    return n === 0 ? "Today" : n === 1 ? "Tomorrow" : "In " + n + " days";
  }
  // Nearest date first: upcoming dates by date, then undated, then past dates, latest first.
  function sortKey(a) {
    var ds = [];
    if (a.nextDate) ds.push(a.nextDate);
    if (a.status === "toapply" && due(a).iso) ds.push(due(a).iso);
    if (!ds.length) return [1, 0];
    var up = ds.filter(function (s) { return days(s) >= 0; }).sort();
    if (up.length) return [0, Date.parse(up[0])];
    ds.sort();
    return [2, -Date.parse(ds[ds.length - 1])];
  }

  // The board ------------------------------------------------------------------

  var board = app.querySelector(".at-board");
  var live = document.getElementById("at-live");
  var addBtn = app.querySelector(".at-add");
  function say(msg, el) {
    el = el || live;
    el.textContent = "";
    window.setTimeout(function () { el.textContent = msg; }, 60);
  }
  function caret() { return '<svg class="icon" aria-hidden="true"><use href="#i-caret-down"/></svg>'; }
  function row(label, html) { return "<div><dt>" + label + "</dt><dd>" + html + "</dd></div>"; }

  function card(a) {
    var d = due(a), rows = [], name = esc(a.firm + ", " + a.role);
    if (a.status === "toapply") {
      var v = d.iso ? fmt(d.iso) : d.txt ? esc(d.txt) : "No deadline set";
      if (d.iso && soon(d.iso)) v += '<span class="at-soon">' + soon(d.iso) + "</span>";
      if (d.src === "cal") v += '<span class="at-src">From the Recruiting calendar</span>';
      rows.push(row("Closes", v));
    }
    if (a.applied && a.status !== "toapply") rows.push(row("Applied", fmt(a.applied)));
    if (a.next || a.nextDate) {
      var n = esc(a.next || "Next step") + (a.nextDate ? ", " + fmt(a.nextDate) : "");
      if (a.nextDate && soonNext(a.nextDate)) n += '<span class="at-soon">' + soonNext(a.nextDate) + "</span>";
      if (a.status === "interview" || a.status === "offer") rows.unshift(row("Next", n));
      else rows.push(row("Next", n));
    } else if (a.status === "interview") {
      rows.unshift(row("Next", '<span class="at-src">No next step yet</span>'));
    }
    var extra = [];
    var nc = a.contacts.filter(function (c) { return c.name || c.role || c.reach; }).length;
    if (nc) extra.push(plural(nc, "contact", "contacts"));
    if (a.notes.trim()) extra.push("Notes");
    var opts = ST.map(function (s) {
      return '<option value="' + s[0] + '"' + (s[0] === a.status ? " selected" : "") + ">" + s[1] + "</option>";
    }).join("");
    return '<li class="at-card" data-id="' + a.id + '">' +
      '<h3 class="at-card__firm">' + esc(a.firm) + "</h3>" +
      '<p class="at-card__role">' + esc(a.role) + "</p>" +
      (rows.length ? '<dl class="at-card__dl">' + rows.join("") + "</dl>" : "") +
      (extra.length ? '<p class="at-card__extra">' + extra.join(" · ") + "</p>" : "") +
      '<div class="at-card__acts">' +
      '<label class="at-card__lbl" for="s-' + a.id + '">Status<span class="visually-hidden"> of ' + name + "</span></label>" +
      '<span class="at-select"><select class="at-st" id="s-' + a.id + '">' + opts + "</select>" + caret() + "</span>" +
      '<button type="button" class="btn btn--ghost btn--sm at-open" aria-haspopup="dialog">Details<span class="visually-hidden">: ' + name + "</span></button>" +
      "</div></li>";
  }

  function render(focus) {
    ST.forEach(function (s) {
      var col = board.querySelector('[data-status="' + s[0] + '"]');
      var list = apps.filter(function (a) { return a.status === s[0]; }).map(function (a) { return [sortKey(a), a]; });
      list.sort(function (x, y) {
        return x[0][0] - y[0][0] || x[0][1] - y[0][1] || x[1].firm.localeCompare(y[1].firm) || x[1].role.localeCompare(y[1].role);
      });
      col.querySelector(".at-n").textContent = list.length;
      col.querySelector(".at-list").innerHTML = list.map(function (x) { return card(x[1]); }).join("");
      col.querySelector(".at-none").hidden = list.length > 0;
    });
    if (focus) {
      var el = board.querySelector('[data-id="' + focus.id + '"] ' + focus.sel);
      if (el) el.focus();
    }
  }
  function find(id) {
    for (var i = 0; i < apps.length; i++) if (apps[i].id === id) return apps[i];
    return null;
  }

  function setStatus(a, st) {
    if (!ST_NAME[st] || a.status === st) return "";
    var msg = a.firm + " moved to " + ST_NAME[st] + ".";
    if (st === "applied" && !a.applied) {
      a.applied = TODAY_ISO;
      msg += " Date applied set to today, " + fmt(TODAY_ISO) + ". You can change it in Details.";
    }
    a.status = st;
    write();
    return msg;
  }

  board.addEventListener("change", function (e) {
    var sel = e.target.closest(".at-st");
    if (!sel) return;
    var a = find(sel.closest(".at-card").getAttribute("data-id"));
    if (!a) return;
    var msg = setStatus(a, sel.value);
    render({ id: a.id, sel: ".at-st" });
    if (msg) say(msg);
  });
  board.addEventListener("click", function (e) {
    var b = e.target.closest(".at-open");
    if (!b) return;
    var a = find(b.closest(".at-card").getAttribute("data-id"));
    if (a) openEdit(a);
  });

  // Dialogs: native modal dialogs (focus stays inside, Escape closes); focus goes
  // back to what opened them, or to the place that replaced it.

  function show(d, returnTo) {
    d._returnTo = returnTo || document.activeElement;
    if (typeof d.showModal === "function") {
      if (!d.open) d.showModal();
    } else {
      d.setAttribute("open", "");
    }
    window.requestAnimationFrame(function () { d.classList.add("is-open"); });
  }
  function hide(d) {
    d.classList.remove("is-open");
    if (typeof d.close === "function") {
      if (d.open) d.close();
    } else {
      d.removeAttribute("open");
      d.dispatchEvent(new Event("close"));
    }
  }
  function wire(d, onClose) {
    // a press and release on the backdrop closes it; a text selection dragged out of a field does not
    var down = null;
    d.addEventListener("mousedown", function (e) { down = e.target; });
    d.addEventListener("click", function (e) {
      if ((e.target === d && down === d) || e.target.closest("[data-close]")) hide(d);
      down = null;
    });
    d.addEventListener("close", function () {
      d.classList.remove("is-open");
      if (onClose) onClose();
      var to = d._returnTo;
      d._returnTo = null;
      if (typeof to === "function") to = to();
      if (to && to.isConnected && !to.closest("dialog:not([open])")) to.focus();
    });
  }

  // Confirm: the safe choice has the focus.
  var conf = document.getElementById("at-confirm");
  var confYes = conf.querySelector(".at-c-yes"), confNo = conf.querySelector(".at-c-no");
  var onYes = null;
  wire(conf, function () { onYes = null; });
  function ask(title, text, yes, no, action) {
    conf.querySelector("#at-c-h").textContent = title;
    conf.querySelector("#at-c-p").textContent = text;
    confYes.textContent = yes;
    confNo.textContent = no;
    onYes = action;
    show(conf);
    confNo.focus();
  }
  confNo.addEventListener("click", function () { hide(conf); });
  confYes.addEventListener("click", function () {
    var act = onYes;
    onYes = null;
    conf._returnTo = null;
    hide(conf);
    if (act) act();
  });

  // Add: the calendar's programmes, typed to narrow, or the reader's own --------

  var addDlg = document.getElementById("at-adddlg");
  var q = document.getElementById("at-q"), opts = document.getElementById("at-opts");
  var qSt = document.getElementById("at-q-st");
  var matches = [], active = -1;
  wire(addDlg);

  function tracked(p) { return apps.some(function (a) { return a.ref === p.id; }); }
  function optMeta(p) {
    return [p.cycle, p.closes ? "Closes " + fmt(p.closes) : p.win].filter(Boolean).join(" · ");
  }
  function renderOpts() {
    var words = norm(q.value).split(/\s+/).filter(Boolean);
    matches = PROGS.filter(function (p) {
      var hay = norm(p.firm + " " + p.prog + " " + p.cycle);
      return words.every(function (w) { return hay.indexOf(w) > -1; });
    });
    if (active >= matches.length) active = matches.length - 1;
    opts.innerHTML = matches.length ? matches.map(function (p, i) {
      var on = tracked(p);
      return '<li role="option" id="at-opt-' + i + '" data-i="' + i + '" aria-selected="' + (i === active) + '"' + (on ? ' aria-disabled="true"' : "") + ">" +
        '<span class="at-o__firm">' + esc(p.firm) + "</span>" +
        '<span class="at-o__prog">' + esc(p.prog) + "</span>" +
        '<span class="at-o__meta">' + esc(optMeta(p)) + (on ? '<span class="at-o__on">In your tracker</span>' : "") + "</span></li>";
    }).join("") : '<li class="at-o__none" role="presentation">No programme in the Recruiting calendar matches. Add it below as your own.</li>';
    if (active >= 0) {
      q.setAttribute("aria-activedescendant", "at-opt-" + active);
      var el = document.getElementById("at-opt-" + active);
      if (el) el.scrollIntoView({ block: "nearest" });
    } else {
      q.removeAttribute("aria-activedescendant");
    }
  }
  function addFromCal(p) {
    if (tracked(p)) {
      say(p.firm + ", " + p.prog + " is already in your tracker.", qSt);
      return;
    }
    apps.push({
      id: newId(), ref: p.id, firm: p.firm, role: p.prog, url: p.url, status: "toapply", own: false, deadline: "",
      cal: { closes: p.closes || "", win: p.win || "" }, applied: "", next: "", nextDate: "", contacts: [], notes: "", added: TODAY_ISO,
    });
    write();
    render();
    renderOpts();
    say("Added " + p.firm + ", " + p.prog + ", to To apply." + (stored ? "" : " This browser is not saving it."), qSt);
  }
  q.addEventListener("input", function () { active = -1; renderOpts(); });
  q.addEventListener("keydown", function (e) {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (!matches.length) return;
      e.preventDefault();
      active = active < 0 ? (e.key === "ArrowDown" ? 0 : matches.length - 1)
        : (active + (e.key === "ArrowDown" ? 1 : -1) + matches.length) % matches.length;
      renderOpts();
    } else if (e.key === "Enter") {
      e.preventDefault();
      var p = active >= 0 ? matches[active] : matches.length === 1 ? matches[0] : null;
      if (p) addFromCal(p);
      else if (matches.length) say("Use the arrow keys to choose one of " + plural(matches.length, "programme", "programmes") + ", then Enter.", qSt);
    } else if (e.key === "Escape" && q.value) {
      // the first Escape clears the field; the next closes the dialog
      e.preventDefault();
      q.value = "";
      active = -1;
      renderOpts();
    }
  });
  opts.addEventListener("mousedown", function (e) { if (e.target.closest("[data-i]")) e.preventDefault(); });
  opts.addEventListener("click", function (e) {
    var li = e.target.closest("[data-i]");
    if (!li) return;
    active = +li.getAttribute("data-i");
    var p = matches[active];
    if (p) addFromCal(p);
    q.focus();
  });

  var own = addDlg.querySelector(".at-own");
  var ownFirm = document.getElementById("at-o-firm"), ownRole = document.getElementById("at-o-role"), ownDl = document.getElementById("at-o-dl");
  var ownErr = own.querySelector(".at-err");
  function invalid(input, on) { if (on) input.setAttribute("aria-invalid", "true"); else input.removeAttribute("aria-invalid"); }
  [ownFirm, ownRole].forEach(function (input) {
    input.addEventListener("input", function () { invalid(input, false); ownErr.textContent = ""; ownErr.classList.remove("is-error"); });
  });
  own.addEventListener("submit", function (e) {
    e.preventDefault();
    var firm = ownFirm.value.trim(), role = ownRole.value.trim();
    invalid(ownFirm, !firm);
    invalid(ownRole, !role);
    if (!firm || !role) {
      ownErr.classList.add("is-error");
      ownErr.innerHTML = '<svg class="icon" aria-hidden="true"><use href="#i-warning-circle"/></svg>' +
        (!firm && !role ? "Enter the firm and the programme or role." : !firm ? "Enter the firm." : "Enter the programme or role.");
      (!firm ? ownFirm : ownRole).focus();
      return;
    }
    apps.push({
      id: newId(), ref: "", firm: firm.slice(0, 120), role: role.slice(0, 200), url: "", status: "toapply",
      own: isDate(ownDl.value), deadline: isDate(ownDl.value) ? ownDl.value : "", cal: { closes: "", win: "" },
      applied: "", next: "", nextDate: "", contacts: [], notes: "", added: TODAY_ISO,
    });
    write();
    render();
    own.reset();
    ownErr.classList.remove("is-error");
    ownErr.textContent = "Added " + firm + ", " + role + ", to To apply." + (stored ? "" : " This browser is not saving it.");
    ownFirm.focus();
  });

  addBtn.addEventListener("click", function () {
    q.value = "";
    active = -1;
    qSt.textContent = "";
    ownErr.textContent = "";
    ownErr.classList.remove("is-error");
    renderOpts();
    show(addDlg, addBtn);
    q.focus();
  });

  // Details: every field saves as it changes --------------------------------------

  var edit = document.getElementById("at-editdlg");
  var cur = null;
  var f = {
    title: document.getElementById("at-e-h"), sub: document.getElementById("at-e-sub"), links: edit.querySelector(".at-dlg__links"),
    status: document.getElementById("at-e-status"), dl: document.getElementById("at-e-dl"), dlSrc: document.getElementById("at-e-dl-src"),
    useCal: edit.querySelector(".at-e-cal"), applied: document.getElementById("at-e-applied"),
    next: document.getElementById("at-e-next"), nextDate: document.getElementById("at-e-nextd"),
    notes: document.getElementById("at-e-notes"), firm: document.getElementById("at-e-firm"), role: document.getElementById("at-e-role"),
    nameErr: document.getElementById("at-e-name-err"), clist: edit.querySelector(".at-clist"), cAdd: edit.querySelector(".at-c-add"),
  };
  wire(edit, function () {
    if (!cur) return;
    cur.contacts = cur.contacts.filter(function (c) { return c.name.trim() || c.role.trim() || c.reach.trim(); });
    write();
    render();
    cur = null;
  });
  edit.querySelector("form").addEventListener("submit", function (e) { e.preventDefault(); });

  // Where the deadline comes from, in words: the calendar's date, its window, or the reader's own.
  function dlHint() {
    var d = due(cur), c = d.c, txt = "";
    var calSays = !c ? "" : c.closes ? "The Recruiting calendar has " + fmt(c.closes) + "."
      : c.win ? "The Recruiting calendar has no date yet (" + c.win + ")." : "";
    if (d.src === "cal" && d.iso) {
      txt = "From the Recruiting calendar" + (c.re ? "." : ", not yet re-checked: confirm it on the firm's site.");
    } else if (d.src === "cal") {
      txt = "No date in the Recruiting calendar yet (" + c.win + "). Add yours when the firm posts it.";
    } else if (cur.own) {
      txt = (cur.deadline ? "Your date. " : "") + calSays;
    }
    f.dlSrc.textContent = txt.trim();
    f.useCal.hidden = !(cur.own && c && (c.closes || c.win));
    f.useCal.textContent = c && c.closes ? "Use the calendar's date" : "Use the calendar's window";
  }
  function contactRows() {
    f.clist.innerHTML = cur.contacts.map(function (c, i) {
      var n = i + 1, id = "at-c" + i;
      function fld(k, label, v, extra) {
        return '<div class="at-field"><label for="' + id + "-" + k + '">' + label + '<span class="visually-hidden">, contact ' + n + "</span></label>" +
          '<input id="' + id + "-" + k + '" type="text" data-k="' + k + '" value="' + esc(v) + '"' + (extra || "") + "></div>";
      }
      return '<li class="at-contact" data-i="' + i + '">' +
        '<p class="at-contact__n">Contact ' + n + "</p>" +
        '<div class="at-fields at-fields--3">' +
        fld("name", "Name", c.name, ' maxlength="120" autocomplete="off"') +
        fld("role", "Role", c.role, ' maxlength="120" autocomplete="off"') +
        fld("reach", "Email or LinkedIn", c.reach, ' maxlength="200" autocomplete="off" spellcheck="false"') +
        '</div><button type="button" class="at-textbtn at-c-rm" data-i="' + i + '">Remove<span class="visually-hidden"> contact ' + n + "</span></button></li>";
    }).join("");
  }
  function fill() {
    var c = cal(cur);
    f.title.textContent = cur.firm;
    f.sub.textContent = cur.role;
    var url = (c && c.url) || cur.url, links = [];
    if (url) {
      links.push('<a class="rc-apply" href="' + esc(url) + '" rel="noopener">Apply on the firm\'s site <svg class="icon" aria-hidden="true"><use href="#i-arrow-up-right"/></svg></a>');
    }
    if (cur.ref) {
      links.push('<a class="rc-apply" href="' + esc(base + "recruiting-calendar/" + (c && c.f ? "#f-" + c.f : "")) + '">See in the Recruiting calendar <svg class="icon" aria-hidden="true"><use href="#i-arrow-right"/></svg></a>');
    }
    f.links.innerHTML = links.join("");
    f.links.hidden = !links.length;
    f.status.value = cur.status;
    f.dl.value = due(cur).iso || "";
    dlHint();
    f.applied.value = cur.applied;
    f.next.value = cur.next;
    f.nextDate.value = cur.nextDate;
    f.notes.value = cur.notes;
    f.firm.value = cur.firm;
    f.role.value = cur.role;
    invalid(f.firm, false);
    invalid(f.role, false);
    f.nameErr.textContent = "";
    contactRows();
  }
  function openEdit(a) {
    cur = a;
    fill();
    var id = a.id;
    show(edit, function () { return board.querySelector('[data-id="' + id + '"] .at-open') || addBtn; });
    f.status.focus();
  }
  function changed() { write(); render(); }

  f.status.addEventListener("change", function () {
    var msg = setStatus(cur, f.status.value);
    f.applied.value = cur.applied;
    render();
    if (msg) say(msg);
  });
  f.dl.addEventListener("change", function () {
    cur.own = true;
    cur.deadline = isDate(f.dl.value) ? f.dl.value : "";
    dlHint();
    changed();
  });
  f.useCal.addEventListener("click", function () {
    cur.own = false;
    cur.deadline = "";
    f.dl.value = due(cur).iso || "";
    dlHint();
    changed();
    f.dl.focus();
    say("Deadline set back to the Recruiting calendar's.");
  });
  f.applied.addEventListener("change", function () { cur.applied = isDate(f.applied.value) ? f.applied.value : ""; changed(); });
  f.next.addEventListener("input", function () { cur.next = f.next.value.slice(0, 120); changed(); });
  f.nextDate.addEventListener("change", function () { cur.nextDate = isDate(f.nextDate.value) ? f.nextDate.value : ""; changed(); });
  f.notes.addEventListener("input", function () { cur.notes = f.notes.value.slice(0, 4000); changed(); });
  [["firm", 120, "the firm"], ["role", 200, "the programme or role"]].forEach(function (k) {
    var input = f[k[0]];
    input.addEventListener("input", function () {
      var v = input.value.trim();
      invalid(input, !v);
      if (!v) {
        f.nameErr.textContent = "Enter " + k[2] + ". Until then it keeps its last name.";
        return;
      }
      f.nameErr.textContent = "";
      cur[k[0]] = v.slice(0, k[1]);
      f.title.textContent = cur.firm;
      f.sub.textContent = cur.role;
      changed();
    });
  });
  f.clist.addEventListener("input", function (e) {
    var input = e.target.closest("[data-k]");
    if (!input) return;
    var c = cur.contacts[+input.closest(".at-contact").getAttribute("data-i")];
    if (!c) return;
    c[input.getAttribute("data-k")] = input.value;
    changed();
  });
  f.clist.addEventListener("click", function (e) {
    var b = e.target.closest(".at-c-rm");
    if (!b) return;
    var i = +b.getAttribute("data-i");
    cur.contacts.splice(i, 1);
    contactRows();
    changed();
    var next = document.getElementById("at-c" + Math.min(i, cur.contacts.length - 1) + "-name");
    (next || f.cAdd).focus();
    say("Contact removed.");
  });
  f.cAdd.addEventListener("click", function () {
    if (cur.contacts.length >= 20) { say("Up to twenty contacts for each application."); return; }
    cur.contacts.push({ name: "", role: "", reach: "" });
    contactRows();
    document.getElementById("at-c" + (cur.contacts.length - 1) + "-name").focus();
  });
  edit.querySelector(".at-del").addEventListener("click", function () {
    var a = cur;
    ask("Delete this application?", "This removes " + a.firm + ", " + a.role + ", with its contacts and notes, from this browser. It cannot be undone.",
      "Delete it", "Keep it", function () {
        apps = apps.filter(function (x) { return x.id !== a.id; });
        cur = null;
        write();
        render();
        edit._returnTo = addBtn;
        hide(edit);
        say("Deleted " + a.firm + ", " + a.role + ".");
      });
  });

  // Your data: export, import, delete all ------------------------------------------

  var foot = app.querySelector(".at-foot");
  var footSt = foot.querySelector(".at-foot__st");
  var fileIn = foot.querySelector(".at-file");
  var importBtn = foot.querySelector(".at-import");
  var clearBtn = foot.querySelector(".at-clear");
  foot.querySelector(".at-export").addEventListener("click", function () {
    if (!apps.length) { say("There is nothing to export yet.", footSt); return; }
    var name = "andra-markets-applications-" + TODAY_ISO + ".json";
    var blob = new Blob([JSON.stringify({ tracker: "Andra Markets application tracker", v: 1, exported: TODAY_ISO, apps: apps }, null, 2)],
      { type: "application/json" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.hidden = true;
    document.body.appendChild(a);
    a.click();
    window.setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    say("Your copy of " + plural(apps.length, "application", "applications") + " is saved as " + name + " in your downloads.", footSt);
  });
  importBtn.addEventListener("click", function () { fileIn.click(); });
  fileIn.addEventListener("change", function () {
    var file = fileIn.files && fileIn.files[0];
    if (!file) return;
    var done = function (txt) {
      fileIn.value = "";
      var list = [];
      try { list = tidy((JSON.parse(txt) || {}).apps); } catch (e) { list = null; }
      if (!list) { say("That file is not a copy of this tracker.", footSt); importBtn.focus(); return; }
      if (!list.length) { say("That file holds no applications from this tracker.", footSt); importBtn.focus(); return; }
      var go = function () {
        apps = list;
        write();
        render();
        say("Imported " + plural(list.length, "application", "applications") + "." + (stored ? "" : " This browser is not saving them."), footSt);
        importBtn.focus();
      };
      if (apps.length) {
        ask("Replace your applications?", "This replaces the " + plural(apps.length, "application", "applications") + " in this browser with the " +
          plural(list.length, "application", "applications") + " in the file.", "Replace them", "Keep mine", go);
        conf._returnTo = importBtn;
      } else {
        go();
      }
    };
    if (file.size > 2e6) { fileIn.value = ""; say("That file is too large to be a copy of this tracker.", footSt); return; }
    if (file.text) file.text().then(done, function () { say("That file could not be read.", footSt); });
    else {
      var r = new FileReader();
      r.onload = function () { done(String(r.result)); };
      r.onerror = function () { say("That file could not be read.", footSt); };
      r.readAsText(file);
    }
  });
  clearBtn.addEventListener("click", function () {
    if (!apps.length) { say("There is nothing to delete.", footSt); return; }
    ask("Delete all your applications?", "This removes all " + plural(apps.length, "application", "applications") +
      ", with their contacts and notes, from this browser. It cannot be undone.", "Delete all", "Keep them", function () {
      apps = [];
      write();
      render();
      say("Deleted all applications.", footSt);
      clearBtn.focus();
    });
  });

  // Another tab changed the tracker: show its version (unless one is being edited here).
  window.addEventListener("storage", function (e) {
    if (e.key !== KEY || cur) return;
    apps = read();
    render();
  });

  document.querySelector(".at-nojs").hidden = true;
  app.hidden = false;
  warn();
  render();
})();
