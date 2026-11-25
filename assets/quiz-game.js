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
