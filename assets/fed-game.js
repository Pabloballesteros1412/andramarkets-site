// Andra Markets Simulators: Guess the Fed. Ten hidden months from the Fed's
// history since 1983; with the figures it had, will it cut, hold or hike? The
// figures come from assets/simdata-fed.js (FRED, written by
// tools/build_site.py). Runs in the browser; games stay in localStorage.
(function () {
  "use strict";
  var main = document.querySelector(".sim-page");
  var cfgEl = document.getElementById("fed-config");
  if (!main || !cfgEl) return;
  var CFG = JSON.parse(cfgEl.textContent);
  var BASE = main.getAttribute("data-base") || "../../";
  var ROUNDS = 10;
  var STORE = "andra-fed-games";
  var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var WORD = { cut: "Cut", hold: "Hold", hike: "Hike" };

  function $(name) {
    return main.querySelector('[data-fed="' + name + '"]');
  }
  function rng(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function hash(s) {
    var h = 2166136261;
    for (var i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }
  function todayIso() {
    return new Date().toISOString().slice(0, 10);
  }
  function monthName(m) {
    return MONTHS[+m.slice(5, 7) - 1] + " " + m.slice(0, 4);
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function pct(v) {
    return v.toFixed(v < 10 ? 1 : 1) + "%";
  }
  function rate(v) {
    return v.toFixed(2) + "%";
  }
  function target(r) {
    return r[3] === r[4] ? rate(r[4]) : r[3].toFixed(2) + "–" + rate(r[4]);
  }
  function pts(v) {
    return Math.abs(v).toFixed(2) + " point";
  }
  function loadGames() {
    try {
      return JSON.parse(localStorage.getItem(STORE)) || [];
    } catch (e) {
      return [];
    }
  }
  function saveGame(g) {
    var games = loadGames();
    games.unshift(g);
    try {
      localStorage.setItem(STORE, JSON.stringify(games.slice(0, 100)));
    } catch (e) {}
    return games;
  }

  var rows = null; // [month, cpi y/y, unemployment, target low, target high, 2-year]
  var mode = "daily", game = null;

  function load(done) {
    if (rows) return done();
    var have = window.ANDRA_SIMDATA && window.ANDRA_SIMDATA.fed;
    if (have) {
      rows = have.rows;
      return done();
    }
    var s = document.createElement("script");
    s.src = BASE + "assets/" + CFG.file;
    s.onload = function () {
      rows = window.ANDRA_SIMDATA.fed.rows;
      done();
    };
    document.head.appendChild(s);
  }

  function move(i) {
    var d = rows[i][4] - rows[i - 1][4];
    return d > 0.001 ? "hike" : d < -0.001 ? "cut" : "hold";
  }
  // Ten months from 1983 with two years of figures before them: four hikes,
  // three cuts and three holds where there are enough, in a random order.
  function pickRounds(rand) {
    var pools = { hike: [], cut: [], hold: [] };
    for (var i = 25; i < rows.length; i++) if (rows[i][0] >= "1983-01" && rows[i - 1][5] != null) pools[move(i)].push(i);
    var want = { hike: 4, cut: 3, hold: 3 }, out = [];
    Object.keys(want).forEach(function (k) {
      var pool = pools[k].slice();
      for (var j = 0; j < want[k] && pool.length; j++) out.push(pool.splice(Math.floor(rand() * pool.length), 1)[0]);
    });
    for (var a = out.length - 1; a > 0; a--) {
      var b = Math.floor(rand() * (a + 1)), t = out[a];
      out[a] = out[b];
      out[b] = t;
    }
    return out.slice(0, ROUNDS);
  }

  function spark(el, vals) {
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals), span = hi - lo || 1;
    el.setAttribute("d", "M" + vals.map(function (v, i) {
      return ((i / (vals.length - 1)) * 100).toFixed(1) + "," + (36 - ((v - lo) / span) * 32).toFixed(1);
    }).join(" L"));
  }

  function setTag() {
    $("tag").textContent = game && game.round < ROUNDS
      ? "Round " + (game.round + 1) + " of " + ROUNDS + " · Score " + game.score
      : (mode === "daily" ? "Daily challenge, " + todayIso().slice(8) * 1 + " " + MONTHS[+todayIso().slice(5, 7) - 1] + " " + todayIso().slice(0, 4) : "Random months");
  }

  function showRound() {
    var i = game.months[game.round], f = rows[i - 1], y = rows[i - 13];
    $("cpi").textContent = pct(f[1]);
    $("cpi-note").textContent = "a year earlier: " + pct(y[1]);
    $("un").textContent = pct(f[2]);
    $("un-note").textContent = "a year earlier: " + pct(y[2]);
    $("target").textContent = target(f);
    var k = i - 1, last = "";
    while (k > 1 && Math.abs(rows[k][4] - rows[k - 1][4]) < 0.001) k--;
    if (k > 1) {
      var d = rows[k][4] - rows[k - 1][4], ago = i - k;
      last = "last move: " + (d > 0 ? "a hike" : "a cut") + " of " + pts(d) + ", " + (ago === 1 ? "the month before" : ago + " months before");
    }
    $("target-note").textContent = last;
    $("gs2").textContent = rate(f[5]);
    $("gs2-note").textContent = "a year earlier: " + rate(y[5] == null ? f[5] : y[5]);
    var span = rows.slice(i - 24, i);
    spark($("cpi-spark"), span.map(function (r) {
      return r[1];
    }));
    spark($("un-spark"), span.map(function (r) {
      return r[2];
    }));
    spark($("target-spark"), span.map(function (r) {
      return r[4];
    }));
    spark($("gs2-spark"), span.map(function (r) {
      return r[5] == null ? r[4] : r[5];
    }));
    main.querySelectorAll("[data-pick]").forEach(function (b) {
      b.disabled = false;
      b.setAttribute("aria-pressed", "false");
    });
    $("answer").hidden = true;
    setTag();
  }

  function era(m) {
    var hit = null;
    CFG.episodes.forEach(function (e) {
      if (e.from <= m && m <= e.to) hit = e;
    });
    return hit;
  }

  function answer(pick) {
    var i = game.months[game.round], r = rows[i], f = rows[i - 1], did = move(i), d = r[4] - f[4];
    var right = pick === did;
    if (right) game.score++;
    game.picks.push(pick);
    main.querySelectorAll("[data-pick]").forEach(function (b) {
      b.disabled = true;
      b.setAttribute("aria-pressed", b.getAttribute("data-pick") === pick ? "true" : "false");
    });
    var what = did === "hold" ? "the Fed held its target at " + target(r) + "."
      : "the Fed " + (did === "hike" ? "raised" : "cut") + " its target by " + pts(d) + ", to " + target(r) + ".";
    var e = era(r[0]), last = game.round === ROUNDS - 1;
    var a = $("answer");
    a.innerHTML = '<p class="sim-tag">' + (right ? "Correct" : "Not this time: you said " + WORD[pick]) + "</p><h2>" + monthName(r[0]) + ": " + what + "</h2>" +
      "<p>Inflation was " + pct(f[1]) + " and unemployment " + pct(f[2]) + "." + (e ? " The period: " + esc(e.title) + "." : "") + "</p>" +
      '<button class="btn" type="button" data-fed="next">' + (last ? "See your score" : "Next month") + ' <svg class="icon" aria-hidden="true"><use href="#i-arrow-right"/></svg></button>';
    a.hidden = false;
    game.round++;
    setTag();
    if (game.round === ROUNDS) $("tag").textContent = "Round " + ROUNDS + " of " + ROUNDS + " · Score " + game.score;
    a.querySelector("button").addEventListener("click", function () {
      if (game.round < ROUNDS) showRound();
      else finish();
    });
    a.querySelector("button").focus({ preventScroll: true });
  }

  function start() {
    load(function () {
      var seed = mode === "daily" ? hash("andra-fed-" + todayIso()) : Math.floor(Math.random() * 4294967296);
      game = { months: pickRounds(rng(seed)), round: 0, score: 0, picks: [] };
      $("intro").hidden = true;
      $("round").hidden = false;
      showRound();
    });
  }

  function finish() {
    var day = todayIso();
    var games = saveGame({ t: Date.now(), mode: mode, day: day, score: game.score });
    var best = games.reduce(function (m, x) {
      return Math.max(m, x.score);
    }, 0);
    var link = location.origin + location.pathname;
    var text = "Guess the Fed by Andra Markets" + (mode === "daily" ? ", daily challenge " + day : "") + ": I called " + game.score + " of the Fed's " + ROUNDS + " decisions. Can you think like the Fed?";
    var table = game.months.map(function (i, k) {
      var r = rows[i], f = rows[i - 1], did = move(i);
      return "<tr><td>" + monthName(r[0]) + "</td><td>" + pct(f[1]) + "</td><td>" + pct(f[2]) + "</td><td>" + WORD[game.picks[k]] + "</td><td>" + WORD[did] + (did === "hold" ? "" : " " + Math.abs(r[4] - f[4]).toFixed(2)) + "</td></tr>";
    }).join("");
    var rowsH = games.slice(0, 10).map(function (x) {
      var d = new Date(x.t);
      return "<tr><td>" + d.getDate() + " " + MON[d.getMonth()] + "</td><td>" + (x.mode === "daily" ? "Daily challenge" : "Random months") + "</td><td>" + x.score + " of " + ROUNDS + "</td></tr>";
    }).join("");
    var fin = main.querySelector(".sim-final");
    fin.innerHTML =
      main.querySelector(".sim-head").outerHTML.replace('data-fed="tag"', "").replace(/<h1 class="sim-title">/, '<h1 class="sim-title" id="sim-final-title" tabindex="-1">') +
      '<section class="sim-v"><div><p class="sim-word sim-word--long">' + game.score + " of " + ROUNDS + '</p><p class="sim-sub">You called ' + game.score + " of the Fed's " + ROUNDS + " decisions" + (game.score >= 8 ? ": you think like the Fed." : game.score >= 5 ? "." : ". The Fed is harder to read than it looks.") + '</p>' +
      '<div class="sim-act"><button class="btn" type="button" data-act="again">Play again</button><button class="btn btn--ghost" type="button" data-act="share" aria-expanded="false">Share</button></div></div>' +
      '<div><table class="sim-games"><thead><tr><th scope="col">Month</th><th scope="col">Inflation</th><th scope="col">Unemployment</th><th scope="col">You</th><th scope="col">The Fed</th></tr></thead><tbody>' + table + "</tbody></table></div></section>" +
      '<section class="sim-share sim-share--text" data-act="panel" hidden><div><p class="sim-text">' + esc(text) + " " + esc(link) + '</p></div><div><div class="sim-btns" style="margin-top:0"><a class="btn btn--ghost btn--sm" target="_blank" rel="noopener" href="https://www.linkedin.com/sharing/share-offsite/?url=' + encodeURIComponent(link) + '">LinkedIn</a>' +
      '<a class="btn btn--ghost btn--sm" target="_blank" rel="noopener" href="https://x.com/intent/post?text=' + encodeURIComponent(text) + "&url=" + encodeURIComponent(link) + '">X</a>' +
      '<a class="btn btn--ghost btn--sm" target="_blank" rel="noopener" href="https://wa.me/?text=' + encodeURIComponent(text + " " + link) + '">WhatsApp</a>' +
      '<button class="btn btn--ghost btn--sm" type="button" data-act="copy">Copy text</button></div><p class="sim-status" role="status" aria-live="polite"></p></div></section>' +
      '<details class="sim-more"><summary>Your games and record</summary><div><table class="sim-games"><thead><tr><th scope="col">Date</th><th scope="col">Game</th><th scope="col">Score</th></tr></thead><tbody>' + rowsH + "</tbody></table>" +
      '<p class="sim-rec">Best: ' + best + " of " + ROUNDS + ". Saved in this browser only.</p><p class=\"sim-src\">" + esc(CFG.src) + ". Figures as revised since. Not investment advice.</p></div></details>";
    fin.querySelector('[data-act="again"]').addEventListener("click", function () {
      fin.hidden = true;
      main.querySelector(".fed-game").hidden = false;
      $("round").hidden = true;
      $("intro").hidden = false;
      game = null;
      setTag();
      window.scrollTo(0, 0);
    });
    fin.querySelector('[data-act="share"]').addEventListener("click", function (e) {
      var p = fin.querySelector('[data-act="panel"]');
      p.hidden = !p.hidden;
      e.currentTarget.setAttribute("aria-expanded", p.hidden ? "false" : "true");
    });
    fin.querySelector('[data-act="copy"]').addEventListener("click", function () {
      var status = fin.querySelector(".sim-status");
      if (navigator.clipboard) navigator.clipboard.writeText(text + " " + link).then(function () {
        status.textContent = "Copied to the clipboard.";
      }, function () {
        status.textContent = "Copy failed: select the text instead.";
      });
    });
    main.querySelector(".fed-game").hidden = true;
    fin.hidden = false;
    window.scrollTo(0, 0);
    fin.querySelector("#sim-final-title").focus({ preventScroll: true });
  }

  $("modes").addEventListener("click", function (e) {
    var b = e.target.closest("[data-mode]");
    if (!b) return;
    mode = b.getAttribute("data-mode");
    $("modes").querySelectorAll("[data-mode]").forEach(function (x) {
      x.setAttribute("aria-pressed", x === b ? "true" : "false");
    });
    setTag();
  });
  $("start").addEventListener("click", start);
  main.querySelectorAll("[data-pick]").forEach(function (b) {
    b.addEventListener("click", function () {
      if (game && !b.disabled) answer(b.getAttribute("data-pick"));
    });
  });
  setTag();
})();
