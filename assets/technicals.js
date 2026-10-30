// Technical preparation (break-into-wall-street/technicals/<topic>/): the
// practice cards, with progress kept in this browser, and on Brainteasers the
// timed mental maths drill. Without JavaScript every question and answer
// shows as a list.
(function () {
  "use strict";
  var main = document.querySelector("[data-topic]");
  var slug = main ? main.getAttribute("data-topic") : "topic";
  function load(k, d) {
    try { var v = JSON.parse(localStorage.getItem(k)); return v == null ? d : v; } catch (e) { return d; }
  }
  function save(k, v) {
    try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private mode: progress lives for the visit */ }
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }
  function press(group, btn) {
    group.forEach(function (b) { b.setAttribute("aria-pressed", b === btn ? "true" : "false"); });
  }

  // Practice cards --------------------------------------------------------
  var dataEl = document.getElementById("tq-data");
  if (dataEl) {
    var Q = JSON.parse(dataEl.textContent);
    var KEY = "andra-tq-" + slug;
    var marks = load(KEY, {});
    var level = "all", order = "review", deck = [], pos = 0, open = false;
    var card = document.getElementById("tq-card");
    var prog = document.getElementById("tq-prog"), bar = document.getElementById("tq-prog-bar");

    function build() {
      var ids = Q.map(function (_, i) { return i; }).filter(function (i) { return level === "all" || Q[i].level === level; });
      if (order === "shuffle") {
        for (var i = ids.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = ids[i]; ids[i] = ids[j]; ids[j] = t; }
      } else {
        var rank = { review: 0, undefined: 1, got: 2 };
        ids.sort(function (a, b) { return rank[marks[a]] - rank[marks[b]] || a - b; });
      }
      deck = ids;
      pos = 0;
      open = false;
      draw();
    }
    function progress() {
      var inLevel = Q.filter(function (q) { return level === "all" || q.level === level; }).length;
      var got = 0, rev = 0;
      Q.forEach(function (q, i) {
        if (level !== "all" && q.level !== level) return;
        if (marks[i] === "got") got++;
        if (marks[i] === "review") rev++;
      });
      prog.textContent = got + " of " + inLevel + " marked Got it, " + rev + " to review";
      bar.style.width = (inLevel ? (got / inLevel) * 100 : 0) + "%";
    }
    function draw() {
      progress();
      if (!deck.length) { card.innerHTML = '<p class="tq-card__meta">No questions at this level.</p>'; return; }
      var i = deck[pos], q = Q[i];
      var mark = marks[i] === "got" ? "You marked this Got it." : marks[i] === "review" ? "You marked this to review." : "";
      var ans = q.a.map(function (p) { return "<p>" + esc(p) + "</p>"; }).join("")
        + (q.follow ? '<p class="ip-follow"><b>Likely follow-up:</b> ' + esc(q.follow) + "</p>" : "");
      card.innerHTML = '<p class="tq-card__meta"><span>Question ' + (pos + 1) + " of " + deck.length + '</span><span class="tag">'
        + (q.level === "core" ? "Core" : "Advanced") + "</span>" + (mark ? "<span>" + mark + "</span>" : "") + "</p>"
        + '<h3 class="tq-card__q">' + esc(q.q) + "</h3>"
        + '<div class="tq-card__a"' + (open ? "" : " hidden") + ">" + ans + "</div>"
        + '<div class="tq-card__acts">'
        + (open
          ? '<button type="button" class="btn" data-act="got">Got it</button><button type="button" class="btn btn--ghost" data-act="review">Review again</button>'
          : '<button type="button" class="btn" data-act="show">Show answer</button>')
        + '<span class="tq-card__nav"><button type="button" class="tq-nav" data-act="prev"' + (pos ? "" : " disabled") + '>Previous</button>'
        + '<button type="button" class="tq-nav" data-act="next"' + (pos < deck.length - 1 ? "" : " disabled") + ">Next</button></span></div>";
    }
    card.addEventListener("click", function (e) {
      var b = e.target.closest("[data-act]");
      if (!b) return;
      var act = b.getAttribute("data-act");
      if (act === "show") { open = true; draw(); card.querySelector("[data-act=got]").focus(); return; }
      if (act === "got" || act === "review") {
        marks[deck[pos]] = act;
        save(KEY, marks);
        if (pos < deck.length - 1) pos++;
        open = false;
        draw();
        var s = card.querySelector("[data-act=show]");
        if (s) s.focus();
        return;
      }
      if (act === "prev" && pos > 0) pos--;
      if (act === "next" && pos < deck.length - 1) pos++;
      open = false;
      draw();
    });
    var lv = Array.prototype.slice.call(document.querySelectorAll("[data-lv]"));
    lv.forEach(function (b) { b.addEventListener("click", function () { press(lv, b); level = b.getAttribute("data-lv"); build(); }); });
    var od = Array.prototype.slice.call(document.querySelectorAll("[data-or]"));
    od.forEach(function (b) { b.addEventListener("click", function () { press(od, b); order = b.getAttribute("data-or"); build(); }); });
    document.getElementById("tq-reset").addEventListener("click", function () {
      marks = {};
      save(KEY, marks);
      build();
    });
    build();
  }

  // Mental maths drill ------------------------------------------------------
  var form = document.getElementById("md-form");
  if (!form) return;
  var input = document.getElementById("md-in"), go = document.getElementById("md-go");
  var qEl = document.getElementById("md-q"), timeEl = document.getElementById("md-time");
  var scoreEl = document.getElementById("md-score"), bestEl = document.getElementById("md-best"), log = document.getElementById("md-log");
  var secs = 60, kind = "all", running = false, score = 0, left = 0, timer = null, cur = null;
  function r(a, b) { return a + Math.floor(Math.random() * (b - a + 1)); }
  function pick(a) { return a[Math.floor(Math.random() * a.length)]; }
  var GEN = {
    mul: function () {
      if (Math.random() < 0.5) { var a = r(12, 99), b = r(3, 9); return { q: a + " × " + b, a: a * b }; }
      var c = r(11, 29), d = r(11, 29); return { q: c + " × " + d, a: c * d };
    },
    pct: function () {
      var p = pick([5, 10, 12.5, 15, 20, 25, 30, 40, 45, 60, 75]), n = r(5, 120) * 8;
      return { q: p + "% of " + n.toLocaleString("en-US"), a: Math.round(p * n) / 100 };
    },
    frac: function () {
      var den = pick([3, 4, 6, 7, 8, 9, 12, 16]), num = r(1, den - 1);
      return { q: num + "/" + den + " as a decimal", a: Math.round((num / den) * 100) / 100 };
    },
  };
  function next() {
    var k = kind === "all" ? pick(["mul", "mul", "pct", "frac"]) : kind;
    cur = GEN[k]();
    qEl.textContent = cur.q + " =";
  }
  function bestKey() { return "andra-md-" + secs + "-" + kind; }
  function showBest() { bestEl.textContent = load(bestKey(), 0); }
  function fmt(s) { return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0"); }
  function stop() {
    clearInterval(timer);
    running = false;
    input.disabled = true;
    go.textContent = "Start again";
    var best = load(bestKey(), 0);
    if (score > best) { save(bestKey(), score); best = score; }
    bestEl.textContent = best;
    qEl.textContent = "Time. You scored " + score + ".";
    go.focus();
  }
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!running) {
      running = true;
      score = 0;
      left = secs;
      scoreEl.textContent = "0";
      timeEl.textContent = fmt(left);
      log.textContent = "";
      input.disabled = false;
      input.value = "";
      go.textContent = "Answer";
      next();
      input.focus();
      timer = setInterval(function () {
        left--;
        timeEl.textContent = fmt(left);
        if (left <= 0) stop();
      }, 1000);
      return;
    }
    var v = parseFloat(input.value.replace(/,/g, ""));
    if (isNaN(v)) return;
    var ok = Math.abs(v - cur.a) < 0.006;
    if (ok) score++;
    scoreEl.textContent = score;
    log.textContent = ok ? "Correct: " + cur.q + " = " + cur.a : "Not quite: " + cur.q + " = " + cur.a;
    input.value = "";
    next();
  });
  var tb = Array.prototype.slice.call(document.querySelectorAll("[data-mdtime]"));
  tb.forEach(function (b) { b.addEventListener("click", function () { if (running) return; press(tb, b); secs = +b.getAttribute("data-mdtime"); timeEl.textContent = fmt(secs); showBest(); }); });
  var kb = Array.prototype.slice.call(document.querySelectorAll("[data-mdkind]"));
  kb.forEach(function (b) { b.addEventListener("click", function () { if (running) return; press(kb, b); kind = b.getAttribute("data-mdkind"); showBest(); }); });
  showBest();
})();
