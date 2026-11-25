// Andra Markets Simulators: the question games (owner, 25 Nov 2026). Ten rounds; each shows something from the
// record without saying what it is, asks one question and takes one answer, then says what happened. One engine for
// every game of this shape, in Guess the Fed's layout; a game is a "kind" below: how its rounds are drawn from the
// data, what a round shows, its choices and what it says afterwards. The data come from assets/simdata-<key>.js
// (written by tools/build_site.py). Runs in the browser; games stay in localStorage.
(function () {
  "use strict";
  var main = document.querySelector(".sim-page"), cfgEl = document.getElementById("quiz-config");
  if (!main || !cfgEl) return;
  var CFG = JSON.parse(cfgEl.textContent), ROUNDS = CFG.rounds || 10, STORE = "andra-quiz-" + CFG.key, MINUS = "−";
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  function $(name) { return main.querySelector('[data-quiz="' + name + '"]'); }
  function rng(seed) { var a = seed >>> 0; return function () { a = (a + 0x6d2b79f5) >>> 0; var t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function hash(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function today() { return new Date().toISOString().slice(0, 10); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function shuffle(a, r) { for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(r() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
  // A signed move, coloured (the Rise and Fall Rule): +3.2% in green, −33.5% in red, always with its sign.
  function move(v, dec) { var n = Number((v * 100).toFixed(dec == null ? 1 : dec)); return '<span class="' + (n > 0 ? "up" : n < 0 ? "down" : "") + '">' + (n > 0 ? "+" : n < 0 ? MINUS : "") + Math.abs(n).toFixed(dec == null ? 1 : dec) + "%</span>"; }
  function plain(v, dec) { var n = Number((v * 100).toFixed(dec == null ? 1 : dec)); return (n > 0 ? "+" : n < 0 ? MINUS : "") + Math.abs(n).toFixed(dec == null ? 1 : dec) + "%"; }

  var KINDS = {
    // Name the crash: one of the S&P 500's great falls, drawn from its high without dates; which was it, of four?
    crash: {
      rounds: function (D, r) {
        var all = shuffle(D.items.map(function (_, i) { return i; }), r);
        return all.slice(0, ROUNDS).map(function (a) {
          var others = shuffle(D.items.map(function (_, i) { return i; }).filter(function (i) { return i !== a; }), r).slice(0, 3);
          return { a: a, opts: shuffle([a].concat(others), r).sort(function (x, y) { return x - y; }) };   // the choices in order of date
        });
      },
      show: function (el, R, D) {
        var it = D.items[R.a], p = it.p, W = 960, H = 380, L = 56, B = 34, T = 14, lo = Math.min.apply(null, p), top = 1000, bot = Math.floor(lo / 100) * 100;
        function X(i) { return L + i / (p.length - 1) * (W - L - 8); }
        function Y(v) { return T + (top - v) / (top - bot) * (H - T - B); }
        var grid = "", step = (top - bot) > 500 ? 200 : 100;
        for (var v = top; v >= bot; v -= step) grid += '<line class="qz-grid" x1="' + L + '" x2="' + (W - 8) + '" y1="' + Y(v).toFixed(1) + '" y2="' + Y(v).toFixed(1) + '"/><text class="qz-tick" x="' + (L - 10) + '" y="' + (Y(v) + 4).toFixed(1) + '" text-anchor="end">' + (v === top ? "High" : MINUS + (top - v) / 10 + "%") + "</text>";
        var months = it.d / 21, mstep = months > 60 ? 24 : months > 24 ? 12 : months > 10 ? 6 : 3, ticks = "";
        for (var m = mstep; m < months; m += mstep) { var x = X(m * 21 / it.d * (p.length - 1)); ticks += '<line class="qz-grid" x1="' + x.toFixed(1) + '" x2="' + x.toFixed(1) + '" y1="' + (H - B) + '" y2="' + (H - B + 5) + '"/><text class="qz-tick" x="' + x.toFixed(1) + '" y="' + (H - 10) + '" text-anchor="middle">' + (m % 12 ? m + " months" : m / 12 + (m === 12 ? " year" : " years")) + "</text>"; }
        var d = p.map(function (v, i) { return (i ? "L" : "M") + X(i).toFixed(1) + " " + Y(v).toFixed(1); }).join("");
        el.innerHTML = '<svg class="qz-chart" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="An unnamed fall of the S&amp;P 500, as a line from its high: the lowest point is ' + ((1000 - lo) / 10).toFixed(0) + ' percent below it, about ' + Math.round(it.m) + ' months later.">' + grid + ticks +
          '<path class="qz-area" d="' + d + "L" + X(p.length - 1).toFixed(1) + " " + Y(top).toFixed(1) + "L" + X(0).toFixed(1) + " " + Y(top).toFixed(1) + 'Z"/><path class="qz-line" pathLength="1" d="' + d + '"/></svg>' +
          '<p class="lens-read qz-read">S&amp;P 500, daily closes · from the high before the fall · time from the first day shown</p>';
      },
      choices: function (R, D) { return R.opts.map(function (i) { return { id: i, label: D.items[i].t, sub: D.items[i].y }; }); },
      right: function (R) { return R.a; },
      said: function (R, D, pick) { return D.items[pick].t; },
      after: function (R, D) {
        var it = D.items[R.a];
        return { h: it.t + ", " + it.y + ".", p: "The S&amp;P 500 fell " + move(it.f) + " from its high, over " + (it.m < 1.5 ? "a few weeks" : Math.round(it.m) + " months") + ". " + (it.b ? "It was back at that high " + it.b + " after the low." : "") + ' <a class="link" href="' + CFG.base + "market-history/" + it.s + '/">Read the episode</a>' };
      },
      cols: ["Episode", "Fall", "You said"],
      row: function (R, D, pick) { var it = D.items[R.a]; return [esc(it.t) + ", " + it.y, move(it.f), esc(D.items[pick].t)]; }
    }
  };
  // Recession call: a month end with its yield curve, Sahm rule reading and jobless claims; does the cycle peak within a year?
  var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  function mname(m) { return MONTHS[+m.slice(5, 7) - 1] + " " + m.slice(0, 4); }
  function madd(m, n) { var y = +m.slice(0, 4), k = +m.slice(5, 7) - 1 + n; y += Math.floor(k / 12); k = ((k % 12) + 12) % 12; return y + "-" + (k < 9 ? "0" : "") + (k + 1); }
  function mdiff(a, b) { return (+b.slice(0, 4) - +a.slice(0, 4)) * 12 + (+b.slice(5, 7) - +a.slice(5, 7)); }
  function spark(vals, zero) {
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals); if (zero != null) { lo = Math.min(lo, zero); hi = Math.max(hi, zero); } var sp = hi - lo || 1;
    var d = vals.map(function (v, i) { return (i ? "L" : "M") + (i / (vals.length - 1) * 100).toFixed(1) + " " + (38 - (v - lo) / sp * 36).toFixed(1); }).join("");
    return '<svg viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true">' + (zero != null ? '<line class="qz-zero" x1="0" x2="100" y1="' + (38 - (zero - lo) / sp * 36).toFixed(1) + '" y2="' + (38 - (zero - lo) / sp * 36).toFixed(1) + '"/>' : "") + '<path d="' + d + '"/></svg>';
  }
  KINDS.recession = {
    prep: function (D) {
      if (D.ok) return;
      // the peak of each cycle is the month before the first month the NBER marks as recession
      D.peaks = D.rec.map(function (p) { return madd(p[0], -1); });
      D.ok = []; D.rows.forEach(function (r, i) {
        var m = r[0], inside = D.rec.some(function (p) { return m >= madd(p[0], -1) && m < p[1]; });
        if (i < 24 || inside || mdiff(m, D.rows[D.rows.length - 1][0]) < 13) return;
        var next = D.peaks.filter(function (p) { return p > m; })[0];
        D.ok.push({ i: i, yes: !!next && mdiff(m, next) <= 12, next: next || "" });
      });
    },
    rounds: function (D, r) {
      this.prep(D);
      var yes = shuffle(D.ok.filter(function (x) { return x.yes; }), r), no = shuffle(D.ok.filter(function (x) { return !x.yes; }), r), n = 4 + Math.floor(r() * 3);
      return shuffle(yes.slice(0, n).concat(no.slice(0, ROUNDS - n)), r);
    },
    show: function (el, R, D) {
      var i = R.i, row = D.rows[i], span = D.rows.slice(i - 23, i + 1), c = row[1] / 100, ago = D.rows[i - 12];
      function card(t, v, note, vals, zero) { return "<div><span>" + t + "</span><b>" + v + "</b><em>" + note + "</em>" + spark(vals, zero) + "</div>"; }
      el.innerHTML = '<div class="fed-grid qz-grid3">' +
        card("Yield curve, 10-year less 3-month", (c < 0 ? MINUS : "") + Math.abs(c).toFixed(2) + " points", c < 0 ? "Inverted" : c < 0.5 ? "Nearly flat" : "Upward sloping", span.map(function (x) { return x[1]; }), 0) +
        card("Sahm rule indicator", row[2].toFixed(2) + " points", row[2] >= 0.5 ? "At or above its 0.50 threshold" : "Below its 0.50 threshold", span.map(function (x) { return x[2]; }), 0.5) +
        card("Jobless claims, 4-week average", Math.round(row[3]).toLocaleString("en-US") + ",000", "A year before: " + Math.round(ago[3]).toLocaleString("en-US") + ",000", span.map(function (x) { return x[3]; })) +
        '</div><p class="lens-read qz-read">A month end, undated · each line is its last 24 months</p>';
    },
    choices: function () { return [{ id: "yes", label: "Recession within 12 months" }, { id: "no", label: "No recession" }]; },
    right: function (R) { return R.yes ? "yes" : "no"; },
    said: function (R, D, pick) { return pick === "yes" ? "recession" : "no recession"; },
    after: function (R, D) {
      var m = D.rows[R.i][0];
      return { h: mname(m) + ": " + (R.yes ? "a recession followed." : "no recession within twelve months."),
        p: (R.yes ? "The NBER puts the peak of the cycle in " + mname(R.next) + ", " + mdiff(m, R.next) + (mdiff(m, R.next) === 1 ? " month" : " months") + " later." : R.next ? "The next peak of the cycle came in " + mname(R.next) + ", " + (mdiff(m, R.next) < 24 ? mdiff(m, R.next) + " months" : Math.round(mdiff(m, R.next) / 12) + " years") + " later." : "No recession has been dated since.") +
          ' <a class="link" href="' + CFG.base + 'recession-watch/">Today\u2019s readings</a>' };
    },
    cols: ["Month", "Curve", "Sahm", "You said", "What happened"],
    row: function (R, D, pick) { var r = D.rows[R.i]; return [mname(r[0]), (r[1] < 0 ? MINUS : "") + Math.abs(r[1] / 100).toFixed(2), r[2].toFixed(2), pick === "yes" ? "Recession" : "No recession", R.yes ? "Recession" : "No recession"]; }
  };
  // Higher or lower: two companies; which share rose more over the last twelve months?
  KINDS.higher = {
    rounds: function (D, r) {
      var out = [], used = {}, tries = 0;
      while (out.length < ROUNDS && tries++ < 4000) {
        var a = Math.floor(r() * D.items.length), b = Math.floor(r() * D.items.length);
        if (a === b || used[a] || used[b] || Math.abs(D.items[a].r - D.items[b].r) < 0.05) continue;
        used[a] = used[b] = 1; out.push({ a: a, b: b });
      }
      return out;
    },
    card: function (it, open) {
      return "<div><span>" + esc(it.s) + (it.c ? " · " + esc(it.c) : "") + "</span><b>" + esc(it.n) + "</b><em>" + (open ? "Twelve months: " + move(it.r) : "Twelve months: hidden") + "</em>" +
        (open ? spark(it.p, 1000) : '<svg viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true"><line class="qz-zero" x1="0" x2="100" y1="20" y2="20"/></svg>') + "</div>";
    },
    show: function (el, R, D, open) {
      el.innerHTML = '<div class="fed-grid qz-grid2">' + this.card(D.items[R.a], open) + this.card(D.items[R.b], open) + '</div><p class="lens-read qz-read">Share price, in its own currency · the twelve months to ' + esc(D.to) + "</p>";
    },
    reveal: function (el, R, D) { this.show(el, R, D, true); },
    choices: function (R, D) { return [{ id: "a", label: D.items[R.a].n, sub: D.items[R.a].s }, { id: "b", label: D.items[R.b].n, sub: D.items[R.b].s }]; },
    right: function (R, D) { return D.items[R.a].r > D.items[R.b].r ? "a" : "b"; },
    said: function (R, D, pick) { return D.items[R[pick]].n; },
    after: function (R, D) {
      var w = D.items[this.right(R, D) === "a" ? R.a : R.b], l = D.items[this.right(R, D) === "a" ? R.b : R.a];
      return { h: esc(w.n) + " did better.", p: esc(w.n) + " " + move(w.r) + ", " + esc(l.n) + " " + move(l.r) + ", over the twelve months to " + esc(D.to) + "." };
    },
    cols: ["The better share", "", "The other", "", "You picked"],
    row: function (R, D, pick) { var ra = this.right(R, D), w = D.items[ra === "a" ? R.a : R.b], l = D.items[ra === "a" ? R.b : R.a]; return [esc(w.n), move(w.r), esc(l.n), move(l.r), esc(D.items[R[pick]].n)]; }
  };
  // Lump sum or drip: $12,000 at a hidden month; all at once, or a twelfth a month for a year? Valued five years on.
  function money(v) { return "$" + (Math.round(v / 10) * 10).toLocaleString("en-US"); }
  KINDS.lump = {
    prep: function (D) { if (D.R) return; D.R = D.s.split(",").map(function (x) { return +x / 1e5; }); },
    value: function (D, i) {   // [all at once, in twelve parts], five years after month i
      var lump = 12000, drip = 0, k, j;
      for (j = i; j < i + 60; j++) lump *= 1 + D.R[j];
      for (k = 0; k < 12; k++) { var v = 1000; for (j = i + k; j < i + 60; j++) v *= 1 + D.R[j]; drip += v; }
      return [lump, drip];
    },
    rounds: function (D, r) {
      this.prep(D); var out = [], used = {}, n = D.R.length, tries = 0;
      while (out.length < ROUNDS && tries++ < 2000) { var i = 60 + Math.floor(r() * (n - 120)), y = Math.floor(i / 30); if (used[y]) continue; used[y] = 1; out.push({ i: i }); }
      return out;
    },
    show: function (el, R, D, open) {
      var W = 960, H = 340, L = 8, T = 16, B = 30, i = R.i, lv = [1], k;
      for (k = i - 60; k < (open ? i + 60 : i); k++) lv.push(lv[lv.length - 1] * (1 + D.R[k]));
      var at = lv[60], lg = lv.map(function (v) { return Math.log(v / at); }), lo = Math.min.apply(null, lg), hi = Math.max.apply(null, lg); if (!open) { hi = Math.max(hi, 0.4); lo = Math.min(lo, -0.4); }
      function X(j) { return L + j / 120 * (W - L - 8); } function Y(v) { return T + (hi - v) / (hi - lo || 1) * (H - T - B); }
      var d = lg.map(function (v, j) { return (j ? "L" : "M") + X(j).toFixed(1) + " " + Y(v).toFixed(1); }).join("");
      el.innerHTML = '<svg class="qz-chart" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="The S&amp;P 500 with dividends over the five years before the moment you invest' + (open ? ", and the five years after" : "") + '.">' +
        '<line class="qz-grid" x1="' + L + '" x2="' + (W - 8) + '" y1="' + Y(0).toFixed(1) + '" y2="' + Y(0).toFixed(1) + '"/>' +
        '<line class="qz-now" x1="' + X(60).toFixed(1) + '" x2="' + X(60).toFixed(1) + '" y1="' + T + '" y2="' + (H - B) + '"/>' +
        '<text class="qz-tick" x="' + (X(60) - 10).toFixed(1) + '" y="' + (H - 9) + '" text-anchor="end">The five years before</text><text class="qz-tick" x="' + (X(60) + 10).toFixed(1) + '" y="' + (H - 9) + '">' + (open ? "The five years after" : "You invest here. The next five years are hidden") + "</text>" +
        '<path class="qz-line' + (open ? " qz-line--still" : "") + '" pathLength="1" d="' + d + '"/><circle class="qz-dot" cx="' + X(60).toFixed(1) + '" cy="' + Y(0).toFixed(1) + '" r="4"/></svg>' +
        '<p class="lens-read qz-read">S&amp;P 500 with dividends · month ends, ratio scale · undated</p>';
    },
    reveal: function (el, R, D) { this.show(el, R, D, true); },
    choices: function () { return [{ id: "lump", label: "All at once", sub: "$12,000 today" }, { id: "drip", label: "Over twelve months", sub: "$1,000 a month" }]; },
    right: function (R, D) { var v = this.value(D, R.i); return v[0] >= v[1] ? "lump" : "drip"; },
    said: function (R, D, pick) { return pick === "lump" ? "all at once" : "over twelve months"; },
    when: function (D, i) { return mname(madd(D.first, i)); },
    after: function (R, D) {
      var v = this.value(D, R.i), lump = v[0] >= v[1];
      return { h: this.when(D, R.i) + ": " + (lump ? "all at once" : "the drip") + " was worth more.",
        p: "Five years on, $12,000 all at once was worth " + money(v[0]) + " (" + move(v[0] / 12000 - 1, 0) + "); in twelve monthly parts, " + money(v[1]) + " (" + move(v[1] / 12000 - 1, 0) + ")." + (lump ? "" : " On balance the later parts bought at lower prices than the first day\u2019s.") };
    },
    cols: ["You invest in", "All at once", "Over twelve months", "You picked"],
    row: function (R, D, pick) { var v = this.value(D, R.i); return [this.when(D, R.i), money(v[0]) + " " + move(v[0] / 12000 - 1, 0), money(v[1]) + " " + move(v[1] / 12000 - 1, 0), pick === "lump" ? "All at once" : "Over twelve months"]; }
  };
  var K = KINDS[CFG.kind]; if (!K) return;

  var D = null, game = null, mode = "daily";
  function load(done) {
    if (D) return done();
    var have = window.ANDRA_SIMDATA && window.ANDRA_SIMDATA[CFG.key]; if (have) { D = have; return done(); }
    var s = document.createElement("script"); s.src = (main.getAttribute("data-base") || "../../") + "assets/" + CFG.file;
    s.onload = function () { D = window.ANDRA_SIMDATA && window.ANDRA_SIMDATA[CFG.key]; if (D) done(); else $("tag").textContent = "The data did not load. Try again."; };
    s.onerror = function () { $("tag").textContent = "The data did not load. Try again."; };
    document.head.appendChild(s);
  }
  function games() { try { return JSON.parse(localStorage.getItem(STORE)) || []; } catch (e) { return []; } }
  function save(g) { var all = games(); all.unshift(g); try { localStorage.setItem(STORE, JSON.stringify(all.slice(0, 100))); } catch (e) {} return all; }
  function tag() { $("tag").textContent = game ? "Round " + Math.min(game.round + 1, ROUNDS) + " of " + ROUNDS + " · Score " + game.score : mode === "daily" ? "Today's challenge" : "Random game"; }

  function round() {
    var R = game.list[game.round];
    K.show($("stage"), R, D);
    $("btns").innerHTML = K.choices(R, D).map(function (c) { return '<button class="btn btn--ghost" type="button" data-pick="' + c.id + '" aria-pressed="false"><span>' + esc(c.label) + "</span>" + (c.sub ? "<small>" + esc(c.sub) + "</small>" : "") + "</button>"; }).join("");
    $("answer").hidden = true; tag();
  }
  function answer(pick) {
    var R = game.list[game.round], want = K.right(R, D), ok = String(pick) === String(want), last = game.round === ROUNDS - 1, a = $("answer"), t = K.after(R, D);
    if (ok) game.score++; game.picks.push(pick);
    [].forEach.call($("btns").querySelectorAll("[data-pick]"), function (b) { b.disabled = true; b.setAttribute("aria-pressed", b.getAttribute("data-pick") === String(pick) ? "true" : "false"); if (b.getAttribute("data-pick") === String(want)) b.classList.add("is-right"); });
    a.innerHTML = '<p class="sim-tag">' + (ok ? "Correct" : "Not this time: you said " + esc(K.said(R, D, pick))) + "</p><h2>" + t.h + "</h2><p>" + t.p + "</p>" +
      '<button class="btn" type="button">' + (last ? "See your score" : "Next") + ' <svg class="icon" aria-hidden="true"><use href="#i-arrow-right"/></svg></button>';
    if (K.reveal) K.reveal($("stage"), R, D);
    a.hidden = false; game.round++; tag();
    a.querySelector("button").addEventListener("click", function () { if (game.round < ROUNDS) { round(); window.scrollTo(0, 0); } else finish(); });
    a.querySelector("button").focus({ preventScroll: true }); a.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
  function start() {
    load(function () {
      var seed = mode === "daily" ? hash("andra-" + CFG.key + "-" + today()) : Math.floor(Math.random() * 4294967296);
      game = { list: K.rounds(D, rng(seed)), round: 0, score: 0, picks: [] };
      if (game.list.length < ROUNDS) ROUNDS = game.list.length;
      $("intro").hidden = true; $("round").hidden = false; round();
    });
  }
  function finish() {
    var day = today(), all = save({ t: Date.now(), mode: mode, day: day, score: game.score }), best = all.reduce(function (m, x) { return Math.max(m, x.score); }, 0);
    var link = location.origin + location.pathname, v = CFG.verdicts || ["", "", ""];
    var text = CFG.name + " by Andra Markets" + (mode === "daily" ? ", daily challenge " + day : "") + ": " + CFG.share.replace("{score}", game.score).replace("{rounds}", ROUNDS);
    var table = game.list.map(function (R, k) { return "<tr>" + K.row(R, D, game.picks[k]).map(function (c) { return "<td>" + c + "</td>"; }).join("") + "</tr>"; }).join("");
    var mine = all.slice(0, 10).map(function (x) { var d = new Date(x.t); return "<tr><td>" + d.getDate() + " " + MON[d.getMonth()] + "</td><td>" + (x.mode === "daily" ? "Daily challenge" : "Random game") + "</td><td>" + x.score + " of " + ROUNDS + "</td></tr>"; }).join("");
    var fin = main.querySelector(".sim-final");
    fin.innerHTML = main.querySelector(".sim-head").outerHTML.replace('data-quiz="tag"', "").replace(/<h1 class="sim-title">/, '<h1 class="sim-title" id="sim-final-title" tabindex="-1">') +
      '<section class="sim-v"><div><p class="sim-word sim-word--long">' + game.score + " of " + ROUNDS + '</p><p class="sim-sub">' + esc(game.score >= ROUNDS * 0.8 ? v[0] : game.score >= ROUNDS * 0.5 ? v[1] : v[2]) + "</p>" +
      '<div class="sim-act"><button class="btn" type="button" data-act="again">Play again</button><button class="btn btn--ghost" type="button" data-act="share" aria-expanded="false">Share</button></div></div>' +
      '<div><table class="sim-games"><thead><tr>' + K.cols.map(function (c) { return '<th scope="col">' + c + "</th>"; }).join("") + "</tr></thead><tbody>" + table + "</tbody></table></div></section>" +
      '<section class="sim-share sim-share--text" data-act="panel" hidden><div><p class="sim-text">' + esc(text) + " " + esc(link) + '</p></div><div><div class="sim-btns" style="margin-top:0">' +
      '<a class="btn btn--ghost btn--sm" target="_blank" rel="noopener" href="https://www.linkedin.com/sharing/share-offsite/?url=' + encodeURIComponent(link) + '">LinkedIn</a>' +
      '<a class="btn btn--ghost btn--sm" target="_blank" rel="noopener" href="https://x.com/intent/post?text=' + encodeURIComponent(text) + "&url=" + encodeURIComponent(link) + '">X</a>' +
      '<a class="btn btn--ghost btn--sm" target="_blank" rel="noopener" href="https://wa.me/?text=' + encodeURIComponent(text + " " + link) + '">WhatsApp</a>' +
      '<button class="btn btn--ghost btn--sm" type="button" data-act="copy">Copy text</button></div><p class="sim-status" role="status" aria-live="polite"></p></div></section>' +
      '<details class="sim-more"><summary>Your games and record</summary><div><table class="sim-games"><thead><tr><th scope="col">Date</th><th scope="col">Game</th><th scope="col">Score</th></tr></thead><tbody>' + mine + "</tbody></table>" +
      '<p class="sim-rec">Best: ' + best + " of " + ROUNDS + '. Saved in this browser only.</p><p class="sim-src">' + esc(CFG.src) + ". Not investment advice.</p></div></details>";
    fin.querySelector('[data-act="again"]').addEventListener("click", function () { fin.hidden = true; main.querySelector(".fed-game").hidden = false; $("round").hidden = true; $("intro").hidden = false; game = null; tag(); window.scrollTo(0, 0); });
    fin.querySelector('[data-act="share"]').addEventListener("click", function (e) { var p = fin.querySelector('[data-act="panel"]'); p.hidden = !p.hidden; e.currentTarget.setAttribute("aria-expanded", p.hidden ? "false" : "true"); });
    fin.querySelector('[data-act="copy"]').addEventListener("click", function () { var st = fin.querySelector(".sim-status"); if (navigator.clipboard) navigator.clipboard.writeText(text + " " + link).then(function () { st.textContent = "Copied to the clipboard."; }, function () { st.textContent = "Copy failed: select the text instead."; }); });
    main.querySelector(".fed-game").hidden = true; fin.hidden = false; window.scrollTo(0, 0); fin.querySelector("#sim-final-title").focus({ preventScroll: true });
  }
  $("modes").addEventListener("click", function (e) { var b = e.target.closest("[data-mode]"); if (!b) return; mode = b.getAttribute("data-mode"); [].forEach.call($("modes").querySelectorAll("[data-mode]"), function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); }); tag(); });
  $("start").addEventListener("click", start);
  $("btns").addEventListener("click", function (e) { var b = e.target.closest("[data-pick]"); if (b && game && !b.disabled) answer(b.getAttribute("data-pick")); });
  tag();
})();
