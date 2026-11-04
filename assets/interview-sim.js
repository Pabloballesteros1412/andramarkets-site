// Interview simulator (interview-simulator/): a timed mock interview, answered
// aloud. Choose a track and a length; each question has its clock and an
// optional notes field, then the model answer, its key points and a rating
// (Nailed it, Partly, Missed). At the end, the result by topic with the page to
// review. The clock never moves on by itself. No microphone, nothing recorded or
// sent: progress, the questions already asked and best results stay in
// localStorage; notes are never saved. Without JavaScript the page says so and
// lists the pages that hold every question.
(function () {
  "use strict";
  var root = document.getElementById("isim");
  var dataEl = document.getElementById("isim-data");
  var card = document.getElementById("isim-card");
  if (!root || !dataEl || !card) return;
  var D = JSON.parse(dataEl.textContent);
  var live = document.getElementById("isim-live");
  var ctl = document.getElementById("isim-ctl");
  var tChips = [].slice.call(root.querySelectorAll("[data-isim-track]"));
  var lChips = [].slice.call(root.querySelectorAll("[data-isim-len]"));
  var KEY = "andra-isim";
  var RESUME_MS = 12 * 3600 * 1000; // an unfinished interview can be resumed for 12 hours
  var RATE = { n: "Nailed it", p: "Partly", m: "Missed" };
  var Q = {}, TRACK = {}, LEN = {};
  D.qs.forEach(function (q) { Q[q.id] = q; });
  D.tracks.forEach(function (t) { TRACK[t.id] = t; });
  D.lengths.forEach(function (l) { LEN[l.minutes] = l.questions; });

  function load() {
    try {
      var v = JSON.parse(localStorage.getItem(KEY));
      return v && typeof v === "object" ? v : {};
    } catch (e) { return {}; }
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) { /* private mode: progress lives for the visit */ }
  }
  var store = load();
  var track = TRACK[store.track] ? store.track : D.tracks[0].id;
  var len = LEN[store.len] ? +store.len : (D.lengths[1] || D.lengths[0]).minutes;
  var run = null, timer = null;

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }
  function icon(name) { return '<svg class="icon" aria-hidden="true"><use href="#i-' + name + '"/></svg>'; }
  function clock(s) { return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0"); }
  function minutesWords(s) {
    var w = ["", "one", "two", "three", "four", "five"][s / 60];
    return s % 60 === 0 && w ? w + " minute" + (s > 60 ? "s" : "") : clock(s);
  }
  function join(a) { return a.length < 2 ? a.join("") : a.slice(0, -1).join(", ") + " and " + a[a.length - 1]; }
  function topicName(id) { return (D.topics[id] || {}).name || ""; }
  function day(iso) {
    var m = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    var p = String(iso).split("-");
    return p.length === 3 ? +p[2] + " " + m[+p[1] - 1] + " " + p[0] : "";
  }
  function today() {
    var d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }
  function say(text) {
    live.textContent = "";
    setTimeout(function () { live.textContent = text; }, 60);
  }
  function focus(el) { if (el) el.focus({ preventScroll: false }); }
  function press(group, value, attr) {
    group.forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute(attr) === String(value) ? "true" : "false"); });
  }
  function lock(on) {
    ctl.classList.toggle("is-locked", on);
    tChips.concat(lChips).forEach(function (b) { b.disabled = on; });
  }

  // The draw: the track's topics in a random order, one question from each in
  // turn, so every topic gets its share; within a topic, questions not asked
  // before come first. Two questions that ask the same thing never meet.
  function shuffle(a) {
    for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  function draw(trackId, n) {
    var seen = {};
    (store.seen || []).forEach(function (id) { seen[id] = 1; });
    var topics = shuffle(TRACK[trackId].topics.slice()), pools = {};
    topics.forEach(function (t) {
      var all = D.qs.filter(function (q) { return q.t === t; });
      pools[t] = shuffle(all.filter(function (q) { return !seen[q.id]; })).concat(shuffle(all.filter(function (q) { return seen[q.id]; })));
    });
    var out = [], used = {}, active = topics.filter(function (t) { return pools[t].length; }), k = 0;
    while (out.length < n && active.length) {
      var at = k % active.length, pool = pools[active[at]], q = null;
      while (pool.length && !q) { var c = pool.shift(); if (!c.g || !used[c.g]) q = c; }
      if (!q) { active.splice(at, 1); continue; }
      out.push(q.id);
      if (q.g) used[q.g] = 1;
      k++;
    }
    return out;
  }

  // Saves the interview in progress (an ended one is deleted where it ends) and the choices.
  function persist() {
    if (run) { run.at = Date.now(); store.run = run; }
    store.track = track;
    store.len = len;
    save();
  }
  function saved() {
    var r = store.run;
    if (!r || !r.ids || !r.ids.length || !TRACK[r.track] || !LEN[r.len] || Date.now() - (r.at || 0) > RESUME_MS) return null;
    if (r.i >= r.ids.length || r.ids.some(function (id) { return !Q[id]; })) return null;
    return r;
  }

  // Ready: the plan for the chosen track and length, Start (or Resume).
  function renderReady(focusIt) {
    stopClock();
    lock(false);
    var t = TRACK[track], n = LEN[len], best = (store.best || {})[track + "-" + len], r = saved();
    var names = join(t.topics.map(topicName));
    var acts = r
      ? '<p class="isim__resume">Unfinished interview: question ' + (r.i + 1) + " of " + r.ids.length + ", " + esc(TRACK[r.track].name) + ", " + r.len + ' minutes.</p>'
        + '<div class="isim__acts isim__acts--start"><button type="button" class="btn" data-act="resume">Resume</button><button type="button" class="btn btn--ghost" data-act="start">Start a new one</button></div>'
      : '<div class="isim__acts isim__acts--start"><button type="button" class="btn" data-act="start">Start the interview</button></div>';
    card.innerHTML = '<p class="tq-card__meta"><span>' + n + " questions</span><span>" + esc(cap(minutesWords(D.secs))) + " each</span>"
      + '<span class="isim__time">' + clock(D.secs) + "</span></p>"
      + '<h3 class="tq-card__q isim__h" tabindex="-1">' + esc(t.name) + "</h3>"
      + '<p class="isim__txt">' + n + " questions from " + esc(names) + ". Answer each one aloud, as you would in the room. When you are ready, or when the clock runs out, show the model answer, check it against its key points and rate yourself.</p>"
      + (best ? '<p class="isim__best">Your best on this track and length: ' + best.s + "%, " + day(best.d) + ".</p>" : "")
      + acts;
    if (focusIt) focus(card.querySelector(".isim__h"));
  }
  function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

  // A question: meta with its clock, the question, notes and Show the model answer.
  function answerHtml(q) {
    var a = (q.a || []).map(function (b) {
      return b[0] === "ol"
        ? '<ol class="ruled">' + b[1].map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ol>"
        : "<p>" + esc(b[1]) + "</p>";
    }).join("");
    if (q.f) a += '<p class="ip-follow"><b>Likely follow-up:</b> ' + esc(q.f) + "</p>";
    if (q.s && q.s.length) {
      a += '<p class="isim__src">From the close notes of ' + join(q.s.map(function (s) {
        return s[1] ? '<a href="' + esc(s[1]) + '">' + esc(s[0]) + "</a>" : esc(s[0]);
      })) + ".</p>";
    }
    var kp = (q.k || []).length
      ? '<div class="isim__kp"><h4 class="isim__lab">Key points</h4><ul class="isim__kps">'
        + q.k.map(function (k) { return "<li>" + icon("check") + "<span>" + esc(k) + "</span></li>"; }).join("") + "</ul></div>"
      : "";
    var rated = run.rate[q.id];
    var btns = ["n", "p", "m"].map(function (r) {
      return '<button type="button" class="btn btn--ghost" data-rate="' + r + '" aria-pressed="' + (rated === r) + '">' + RATE[r] + "</button>";
    }).join("");
    var last = run.i === run.ids.length - 1;
    return '<div class="isim__ans" id="isim-ans">'
      + '<h4 class="isim__lab" id="isim-ans-h" tabindex="-1">Model answer</h4><div class="isim__a">' + a + "</div>"
      + kp
      + '<div class="isim__rate"><h4 class="isim__lab" id="isim-rate-l">How did you do?</h4>'
      + '<div class="isim__rbtns" role="group" aria-labelledby="isim-rate-l">' + btns + "</div></div>"
      + '<div class="isim__acts"><button type="button" class="tq-nav isim__end" data-act="end">End the interview</button>'
      + '<button type="button" class="btn" data-act="next"' + (rated ? "" : " disabled") + ">" + (last ? "See your results" : "Next question") + " " + icon("arrow-right") + "</button></div>"
      + "</div>";
  }
  function renderAsk() {
    var q = Q[run.ids[run.i]];
    lock(true);
    card.innerHTML = '<p class="tq-card__meta"><span>Question ' + (run.i + 1) + " of " + run.ids.length + "</span><span>" + esc(topicName(q.t)) + "</span>"
      + '<span class="isim__up" id="isim-up"' + (run.over ? "" : " hidden") + ">Time is up</span>"
      + '<span class="isim__time" id="isim-time" role="timer"><span class="visually-hidden">Time left </span><span id="isim-clock">' + clock(run.left) + "</span></span></p>"
      + '<h3 class="tq-card__q isim__q" id="isim-q" tabindex="-1">' + esc(q.q) + "</h3>"
      + (q.c ? '<p class="isim__ctx">' + esc(q.c) + "</p>" : "")
      + '<div class="isim__notes"><p class="isim__hint" id="isim-hint">Answer aloud; notes are optional.</p>'
      + '<label class="visually-hidden" for="isim-notes">Notes</label><textarea id="isim-notes" rows="3" aria-describedby="isim-hint" placeholder="Notes"></textarea></div>'
      + (run.shown ? answerHtml(q)
        : '<div class="isim__acts" id="isim-acts"><button type="button" class="tq-nav isim__end" data-act="end">End the interview</button>'
          + '<button type="button" class="btn" data-act="show">Show the model answer</button></div>');
  }

  // The clock: counts down from the answer time; at zero it says so once and
  // waits. It runs from the wall clock, so a hidden tab does not slow it.
  function stopClock() { clearInterval(timer); timer = null; }
  function startClock() {
    stopClock();
    if (run.left <= 0) return;
    var end = Date.now() + run.left * 1000;
    timer = setInterval(function () {
      var left = Math.max(0, Math.ceil((end - Date.now()) / 1000));
      if (left === run.left) return;
      run.left = left;
      var c = document.getElementById("isim-clock");
      if (c) c.textContent = clock(left);
      if (left === 30 && D.secs > 60) say("30 seconds left.");
      if (left % 5 === 0) persist();
      if (left === 0) {
        stopClock();
        run.over = true;
        var up = document.getElementById("isim-up");
        if (up) up.hidden = false;
        say("Time is up. Show the model answer when you are ready.");
        persist();
      }
    }, 250);
  }

  function ask(focusIt) {
    var id = run.ids[run.i];
    store.seen = (store.seen || []).filter(function (x) { return x !== id; }).concat([id]).slice(-500);
    renderAsk();
    persist();
    if (!run.shown) startClock();
    if (focusIt) focus(document.getElementById(run.shown ? "isim-ans-h" : "isim-q"));
  }
  function start() {
    var ids = draw(track, LEN[len]);
    if (!ids.length) return;
    run = { track: track, len: len, ids: ids, i: 0, rate: {}, shown: false, left: D.secs, over: false };
    ask(true);
  }
  function show() {
    stopClock();
    run.shown = true;
    var acts = document.getElementById("isim-acts");
    if (acts) acts.outerHTML = answerHtml(Q[run.ids[run.i]]);
    persist();
    focus(document.getElementById("isim-ans-h"));
  }
  function rate(r) {
    run.rate[run.ids[run.i]] = r;
    [].forEach.call(card.querySelectorAll("[data-rate]"), function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-rate") === r)); });
    var next = card.querySelector("[data-act=next]");
    next.disabled = false;
    persist();
    focus(next);
  }
  function next() {
    if (run.i >= run.ids.length - 1) { finish(); return; }
    run.i++;
    run.shown = false;
    run.over = false;
    run.left = D.secs;
    ask(true);
  }
  function end() {
    stopClock();
    var any = run.ids.some(function (id) { return run.rate[id]; });
    if (any) { finish(); return; }
    run = null;
    delete store.run;
    persist();
    renderReady(true);
  }

  // Results: counts per rating, each topic's ratings with its page, the topics to
  // review first and every question asked with its rating.
  function finish() {
    stopClock();
    lock(false);
    var r = run, rated = r.ids.filter(function (id) { return r.rate[id]; });
    var c = { n: 0, p: 0, m: 0 }, by = {}, order = [];
    rated.forEach(function (id) {
      var t = Q[id].t, v = r.rate[id];
      c[v]++;
      if (!by[t]) { by[t] = { n: 0, p: 0, m: 0 }; order.push(t); }
      by[t][v]++;
    });
    var score = Math.round(((c.n + c.p / 2) / rated.length) * 100);
    var key = r.track + "-" + r.len;
    store.best = store.best || {};
    var prev = store.best[key], isBest = !prev || score > prev.s;
    if (isBest) store.best[key] = { s: score, d: today() };
    run = null;
    delete store.run;
    persist();
    order.sort(function (a, b) { return by[b].m - by[a].m || by[b].p - by[a].p; });
    var review = order.filter(function (t) { return by[t].m || by[t].p; });
    var rows = order.map(function (t) {
      var tp = D.topics[t], todo = by[t].m || by[t].p;
      return '<tr><th scope="row"><a href="' + esc(tp.href) + '">' + esc(tp.name) + "</a>"
        + (todo ? ' <span class="tag">To review</span>' : "") + "<span>" + esc(tp.src) + "</span></th>"
        + '<td class="num">' + by[t].n + '</td><td class="num">' + by[t].p + '</td><td class="num">' + by[t].m + "</td></tr>";
    }).join("");
    var list = rated.map(function (id) {
      var q = Q[id];
      return '<li><span class="isim-list__q">' + esc(q.q) + (q.c ? " " + esc(q.c) : "") + '</span><span class="isim-list__m">'
        + esc(topicName(q.t)) + ". " + RATE[r.rate[id]] + "</span></li>";
    }).join("");
    var early = rated.length < r.ids.length ? '<p class="isim__txt">You ended after ' + rated.length + " of " + r.ids.length + " questions.</p>" : "";
    var bestLine = isBest
      ? (prev ? "Your best on this track and length so far." : "Your first result on this track and length.")
      : "Your best on this track and length: " + prev.s + "%, " + day(prev.d) + ".";
    card.innerHTML = '<p class="tq-card__meta"><span>Results</span><span>' + esc(TRACK[r.track].name) + "</span><span>" + r.len + " minutes</span></p>"
      + '<h3 class="tq-card__q isim__h" id="isim-res-h" tabindex="-1">' + c.n + " nailed, " + c.p + " partly, " + c.m + " missed</h3>"
      + early
      + '<p class="isim__txt">Score ' + score + "%. " + bestLine + "</p>"
      + '<h4 class="isim__lab isim__lab--sec">By topic</h4>'
      + '<div class="isim-res__wrap"><table class="isim-res"><caption class="visually-hidden">Ratings by topic, with the page to review</caption>'
      + '<thead><tr><th scope="col">Topic</th><th scope="col" class="num">Nailed it</th><th scope="col" class="num">Partly</th><th scope="col" class="num">Missed</th></tr></thead>'
      + "<tbody>" + rows + "</tbody></table></div>"
      + '<p class="isim__txt">' + (review.length
        ? "Review first: " + join(review.map(function (t) { return '<a href="' + esc(D.topics[t].href) + '">' + esc(D.topics[t].name) + "</a>"; })) + "."
        : "Nothing to review from this interview: every answer was nailed.") + "</p>"
      + '<h4 class="isim__lab isim__lab--sec">Your answers</h4><ol class="isim-list">' + list + "</ol>"
      + '<div class="isim__acts isim__acts--start"><button type="button" class="btn" data-act="start">Start again</button>'
      + '<button type="button" class="btn btn--ghost" data-act="change">Change track or length</button></div>';
    focus(document.getElementById("isim-res-h"));
  }

  card.addEventListener("click", function (e) {
    var b = e.target.closest("button");
    if (!b || b.disabled) return;
    var act = b.getAttribute("data-act"), r = b.getAttribute("data-rate");
    if (r) { rate(r); return; }
    if (act === "start") { delete store.run; start(); }
    else if (act === "resume") {
      run = saved();
      if (!run) { renderReady(true); return; }
      track = run.track;
      len = run.len;
      press(tChips, track, "data-isim-track");
      press(lChips, len, "data-isim-len");
      ask(true);
    }
    else if (act === "show") show();
    else if (act === "next") next();
    else if (act === "end") end();
    else if (act === "change") { renderReady(false); focus(root.querySelector('[data-isim-track][aria-pressed="true"]')); }
  });
  tChips.forEach(function (b) {
    b.addEventListener("click", function () {
      if (run) return;
      track = b.getAttribute("data-isim-track");
      press(tChips, track, "data-isim-track");
      persist();
      renderReady(false);
    });
  });
  lChips.forEach(function (b) {
    b.addEventListener("click", function () {
      if (run) return;
      len = +b.getAttribute("data-isim-len");
      press(lChips, len, "data-isim-len");
      persist();
      renderReady(false);
    });
  });
  document.getElementById("isim-clear").addEventListener("click", function () {
    stopClock();
    run = null;
    store = {};
    persist();
    renderReady(false);
    say("Saved progress cleared.");
  });

  press(tChips, track, "data-isim-track");
  press(lChips, len, "data-isim-len");
  renderReady(false);
})();
