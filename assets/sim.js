// Andra Markets Trading Simulator: two hidden years of the S&P 500, played day
// by day against the Index. Runs entirely in the browser; the history comes
// from assets/sim-sp500.js (window.ANDRA_SIM, written by tools/build_site.py)
// and the games played are kept in this browser's localStorage only.
(function () {
  "use strict";
  var DATA = window.ANDRA_SIM;
  var main = document.querySelector(".sim-page");
  if (!DATA || !main || !main.querySelector(".sim-game")) return;

  var N = 504; // trading days in a game
  var START = 10000;
  var CASH = Math.log(1.02) / 252; // flat 2% a year, per trading day, as a log return
  var SPEEDS = { "0.5": 200, "1": 100, "2": 50, "4": 25 }; // ms per trading day
  var PLAYERS = 1000;
  var STORE = "andra-sim-games";
  var BASE = main.getAttribute("data-sim-base") || "../../";
  var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  var EPISODES = JSON.parse(document.getElementById("sim-episodes").textContent);

  // The history: session dates (UTC, as Date) and total returns.
  var dates = [], rets = [];
  (function () {
    var t = Date.parse(DATA.first + "T00:00:00Z");
    var r = DATA.r.split(",");
    for (var i = 0; i < r.length; i++) {
      t += parseInt(DATA.gaps.charAt(i), 36) * 864e5;
      dates.push(new Date(t));
      rets.push(+r[i] / 1e5);
    }
  })();
  var LAST_START = rets.length - N;

  function $(name) {
    return main.querySelector('[data-sim="' + name + '"]');
  }

  // Seeded random numbers (mulberry32) and a string hash (FNV-1a).
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
  function iso(d) {
    return d.toISOString().slice(0, 10);
  }
  function todayIso() {
    return iso(new Date());
  }
  function longDay(isoDay) {
    var d = new Date(isoDay + "T00:00:00Z");
    return d.getUTCDate() + " " + MONTHS[d.getUTCMonth()] + " " + d.getUTCFullYear();
  }
  function medDay(d) {
    return DAYS[d.getUTCDay()] + " " + d.getUTCDate() + " " + MON[d.getUTCMonth()] + " " + d.getUTCFullYear();
  }
  function monthYear(d) {
    return MONTHS[d.getUTCMonth()] + " " + d.getUTCFullYear();
  }

  // Figures. A rise or a fall carries its sign and its colour (DESIGN.md, The
  // Rise and Fall Rule); a figure that rounds to zero carries neither.
  function money(v) {
    return "$" + Math.round(v).toLocaleString("en-US");
  }
  function signed(v, dec, unit) {
    var s = Math.abs(v).toFixed(dec);
    if (+s === 0) return { text: (0).toFixed(dec) + unit, cls: "" };
    return { text: (v > 0 ? "+" : "−") + s + unit, cls: v > 0 ? "mv--up" : "mv--down" };
  }
  function setMove(el, v, dec, unit) {
    var m = signed(v, dec, unit);
    el.textContent = m.text;
    el.className = m.cls;
  }
  function moveHtml(v, dec, unit) {
    var m = signed(v, dec, unit);
    return '<span class="' + m.cls + '">' + m.text + "</span>";
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  // Storage, wrapped: private windows and blocked storage must not break a game.
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

  // ---- Choosing the period ------------------------------------------------
  function dailyStart(day) {
    return Math.floor(rng(hash("andra-sim-" + day))() * (LAST_START + 1));
  }
  function startFromDate(isoDay) {
    var t = Date.parse(isoDay + "T00:00:00Z");
    if (isNaN(t)) return -1;
    for (var i = 0; i < rets.length; i++) if (dates[i].getTime() >= t) return i <= LAST_START ? i : -1;
    return -1;
  }

  var params = new URLSearchParams(location.search);
  var shared = params.get("g") ? startFromDate(params.get("g")) : -1;
  var mode, start;
  function setMode(m, s) {
    mode = m;
    start = s;
    var modeText = {
      daily: "Daily challenge, " + longDay(todayIso()) + ". Two hidden years of the S&P 500, with dividends.",
      random: "Random period. Two hidden years of the S&P 500, with dividends.",
      shared: "A shared period. Two hidden years of the S&P 500, with dividends."
    }[m];
    $("mode").textContent = modeText;
    var goLabel = { daily: "Start today's challenge", random: "Start", shared: "Start" }[m];
    $("go").firstElementChild.textContent = goLabel;
    $("alt").textContent = m === "daily" ? "Play a random period instead" : "Play today's challenge instead";
    var played = m === "daily" && loadGames().filter(function (g) {
      return g.mode === "daily" && g.day === todayIso();
    })[0];
    state(
      "Ready",
      played
        ? "You played today's challenge: " + signed(played.pts, 1, " pts").text + " against the Index. Play it again for practice; your first result stands."
        : "You start fully invested, alongside the Index."
    );
  }

  // ---- Game state ---------------------------------------------------------
  var g = null; // the running game
  var timer = null;
  var speed = "1";
  var playing = false;

  function newGame() {
    return {
      start: start,
      day: 0, // returns applied so far
      inv: true, // position for the next day's return
      pos: [], // position held on each day played
      you: [START],
      idx: [START],
      trades: 0,
      lo: START * 0.9,
      hi: START * 1.1
    };
  }

  function state(head, text, cash) {
    var el = $("state");
    el.innerHTML = "<b>" + esc(head) + "</b>" + esc(text);
    el.classList.toggle("is-cash", !!cash);
  }

  function step() {
    var r = rets[g.start + g.day];
    g.pos.push(g.inv);
    g.idx.push(g.idx[g.idx.length - 1] * (1 + r));
    g.you.push(g.you[g.you.length - 1] * (g.inv ? 1 + r : Math.exp(CASH)));
    g.day++;
    var y = g.you[g.day], x = g.idx[g.day];
    g.lo = Math.min(g.lo, y, x);
    g.hi = Math.max(g.hi, y, x);
    draw();
    if (g.day >= N) finish();
  }

  function loop() {
    clearInterval(timer);
    timer = setInterval(step, SPEEDS[speed]);
  }

  function play() {
    if (!g) {
      g = newGame();
      $("alt").parentNode.hidden = true;
      $("pause").disabled = false;
      $("go").firstElementChild.textContent = "Move to cash";
    }
    playing = true;
    $("pause").textContent = "Pause";
    stateNow();
    loop();
  }

  function pause() {
    playing = false;
    clearInterval(timer);
    $("pause").textContent = "Resume";
    state("Paused", "Press Resume or P to carry on.", !g.inv);
  }

  function stateNow() {
    var m = Math.min(24, Math.floor(g.day / 21) + 1);
    if (g.inv) state("You are in the market", g.trades ? "since month " + m + "." : "alongside the Index.");
    else state("You are in cash", "since month " + m + ". Cash earns 2% a year.", true);
  }

  function toggle() {
    if (!g) return play();
    if (!playing) return;
    g.inv = !g.inv;
    g.trades++;
    $("go").firstElementChild.textContent = g.inv ? "Move to cash" : "Back in the market";
    stateNow();
    drawFacts();
  }

  // ---- Drawing ------------------------------------------------------------
  var W = 640, H = 300, PAD = 8;
  function niceStep(span) {
    var raw = span / 4, p = Math.pow(10, Math.floor(Math.log10(raw)));
    var n = raw / p;
    return (n < 1.5 ? 1 : n < 3 ? 2 : n < 7 ? 5 : 10) * p;
  }
  function chartSvg(svg, labs, game, lo, hi, now) {
    var n = game.day;
    var x = function (i) {
      return (i / N) * W;
    };
    var y = function (v) {
      return PAD + ((hi - v) / (hi - lo)) * (H - 2 * PAD);
    };
    var out = [], i;
    // Cash stretches as bands.
    var a = -1;
    for (i = 0; i <= n; i++) {
      var cash = i < n && !game.pos[i];
      if (cash && a < 0) a = i;
      if (!cash && a >= 0) {
        out.push('<rect class="sim-cash" x="' + x(a).toFixed(1) + '" y="0" width="' + (x(i) - x(a)).toFixed(1) + '" height="' + H + '"/>');
        a = -1;
      }
    }
    var st = niceStep(hi - lo), lab = [];
    for (var v = Math.ceil(lo / st) * st; v < hi; v += st) {
      out.push('<line class="sim-grid" x1="0" x2="' + W + '" y1="' + y(v).toFixed(1) + '" y2="' + y(v).toFixed(1) + '"/>');
      lab.push('<span style="top:' + ((y(v) / H) * 100).toFixed(1) + '%">' + money(v) + "</span>");
    }
    function path(s) {
      var d = "";
      for (var j = 0; j <= n; j++) d += (j ? "L" : "M") + x(j).toFixed(1) + "," + y(s[j]).toFixed(1);
      return d;
    }
    out.push('<path class="sim-idx" d="' + path(game.idx) + '"/>');
    out.push('<path class="sim-you" d="' + path(game.you) + '"/>');
    if (now) out.push('<line class="sim-now" x1="' + x(n).toFixed(1) + '" x2="' + x(n).toFixed(1) + '" y1="0" y2="' + H + '"/>');
    svg.innerHTML = out.join("");
    labs.innerHTML = lab.join("");
    return { x: x(n) / W, y: y(game.you[n]) / H };
  }

  function drawFacts() {
    var inv = 0;
    for (var i = 0; i < g.pos.length; i++) if (g.pos[i]) inv++;
    $("trades").textContent = g.trades;
    $("invested").textContent = (g.pos.length ? Math.round((inv / g.pos.length) * 100) : 100) + "%";
    setMove($("gap"), (g.you[g.day] - g.idx[g.day]) / 100, 1, " pts");
  }

  function draw() {
    var pad = (g.hi - g.lo) * 0.06;
    var p = chartSvg($("chart"), $("ylabs"), g, g.lo - pad, g.hi + pad, true);
    var dot = $("dot");
    dot.hidden = false;
    dot.style.left = p.x * 100 + "%";
    dot.style.top = p.y * 100 + "%";
    var m = Math.min(24, Math.floor(g.day / 21) + 1);
    $("month").innerHTML = "Month " + m + " <small>of 24</small>";
    $("prog").style.width = (g.day / N) * 100 + "%";
    $("day").textContent = "Trading day " + g.day + " of " + N;
    $("you").textContent = money(g.you[g.day]);
    $("idx").textContent = money(g.idx[g.day]);
    setMove($("you-chg"), (g.you[g.day] / START - 1) * 100, 1, "%");
    setMove($("idx-chg"), (g.idx[g.day] / START - 1) * 100, 1, "%");
    drawFacts();
  }

  // ---- The end ------------------------------------------------------------
  // Random players with the same number of trades and the same days invested:
  // the days in the market and the days in cash are each split at random
  // points into as many stretches as the player had, alternating from a start
  // in the market. Each result comes from prefix sums of log returns.
  function skill(game, invDays) {
    var L = [0];
    for (var i = 0; i < N; i++) L.push(L[i] + Math.log(1 + rets[game.start + i]));
    var k = game.trades;
    var nInv = Math.floor(k / 2) + 1, nCash = Math.ceil(k / 2), cashDays = N - invDays;
    var rand = rng(hash("players-" + game.start + "-" + k + "-" + invDays));
    function parts(total, count) {
      if (count === 0) return [];
      var cuts = [], pos = total >= count; // positive parts when there is room
      while (cuts.length < count - 1) {
        var c = pos ? 1 + Math.floor(rand() * (total - 1)) : Math.floor(rand() * (total + 1));
        if (!pos || cuts.indexOf(c) < 0) cuts.push(c);
      }
      cuts.sort(function (a, b) {
        return a - b;
      });
      var out = [], prev = 0;
      for (var j = 0; j < cuts.length; j++) {
        out.push(cuts[j] - prev);
        prev = cuts[j];
      }
      out.push(total - prev);
      return out;
    }
    var finals = [];
    for (var p = 0; p < PLAYERS; p++) {
      var a = parts(invDays, nInv), c = parts(cashDays, nCash), d = 0, lg = 0;
      for (var s = 0; s < a.length; s++) {
        lg += L[d + a[s]] - L[d];
        d += a[s];
        if (s < c.length) {
          lg += c[s] * CASH;
          d += c[s];
        }
      }
      finals.push(START * Math.exp(lg));
    }
    return finals;
  }

  function episodeFor(from, to) {
    var best = null, most = -1;
    var a = from.getUTCFullYear() * 12 + from.getUTCMonth(), b = to.getUTCFullYear() * 12 + to.getUTCMonth();
    EPISODES.forEach(function (e) {
      var ea = +e.from.slice(0, 4) * 12 + +e.from.slice(5, 7) - 1, eb = +e.to.slice(0, 4) * 12 + +e.to.slice(5, 7) - 1;
      var o = Math.min(b, eb) - Math.max(a, ea);
      if (o > most) {
        most = o;
        best = e;
      }
    });
    return best;
  }

  function histogram(finals, idxFinal, you) {
    var pts = finals.map(function (v) {
      return (v - idxFinal) / 100;
    });
    var me = (you - idxFinal) / 100;
    var sorted = pts.slice().sort(function (a, b) {
      return a - b;
    });
    var p90 = sorted[Math.floor(PLAYERS * 0.9)];
    var lo = Math.min(sorted[0], me), hi = Math.max(sorted[sorted.length - 1], me);
    if (hi - lo < 1) {
      lo -= 0.5;
      hi += 0.5;
    }
    var B = 32, bw = (hi - lo) / B, bins = [];
    for (var i = 0; i < B; i++) bins.push(0);
    pts.forEach(function (v) {
      bins[Math.min(B - 1, Math.floor((v - lo) / bw))]++;
    });
    var mx = Math.max.apply(null, bins), out = [], w = 640 / B;
    var meBin = Math.min(B - 1, Math.floor((me - lo) / bw));
    for (i = 0; i < B; i++) {
      var h = (bins[i] / mx) * 140;
      if (i === meBin && h < 4) h = 4;
      out.push('<rect class="sim-bar' + (i === meBin ? " sim-bar--you" : "") + '" x="' + (i * w + 1).toFixed(1) + '" y="' + (150 - h).toFixed(1) + '" width="' + (w - 2).toFixed(1) + '" height="' + h.toFixed(1) + '"><title>' + bins[i] + " players</title></rect>");
    }
    var xp = function (v) {
      return ((v - lo) / (hi - lo)) * 640;
    };
    var xm = Math.max(14, Math.min(626, (meBin + 0.5) * w));
    var x9 = xp(p90);
    out.push('<line class="sim-p90" x1="' + x9.toFixed(1) + '" x2="' + x9.toFixed(1) + '" y1="0" y2="152"/>');
    out.push('<line class="sim-base" x1="0" x2="640" y1="150.5" y2="150.5"/>');
    out.push('<text x="' + (x9 > 560 ? x9 - 5 : x9 + 5).toFixed(1) + '" y="12"' + (x9 > 560 ? ' text-anchor="end"' : "") + ">Top 10%</text>");
    out.push('<text class="sim-you-lab" x="' + xm.toFixed(1) + '" y="172" text-anchor="middle">You</text>');
    if (xm > 140) out.push('<text x="0" y="172">Worse</text>');
    if (xm < 520) out.push('<text x="640" y="172" text-anchor="end">Better</text>');
    return '<svg viewBox="0 0 640 180" preserveAspectRatio="none" role="img" aria-label="Results of ' + PLAYERS + " random players against the Index, from " + lo.toFixed(1) + " to " + hi.toFixed(1) + " points; yours is " + me.toFixed(1) + ' points">' + out.join("") + "</svg>";
  }

  function finish() {
    clearInterval(timer);
    playing = false;
    var game = g;
    var you = game.you[N], idx = game.idx[N];
    var invDays = game.pos.filter(Boolean).length;
    var pts = (you - idx) / 100;
    var finals = skill(game, invDays);
    var below = 0;
    finals.forEach(function (v) {
      if (v < you - 1e-6) below++;
      else if (Math.abs(v - you) <= 1e-6) below += 0.5;
    });
    var share = below / PLAYERS;
    var verdict = share >= 0.9 ? "Skill" : "Luck";
    var beat = Math.floor(below);
    var from = dates[game.start], to = dates[game.start + N - 1];
    var ep = episodeFor(from, to);

    // The ten best days of the period, and which of them were spent in cash.
    var order = [];
    for (var i = 0; i < N; i++) order.push(i);
    order.sort(function (a, b) {
      return rets[game.start + b] - rets[game.start + a];
    });
    var best = order.slice(0, 10), missed = best.filter(function (i) {
      return !game.pos[i];
    });

    var day = todayIso();
    var games = saveGame({ t: Date.now(), mode: mode, day: day, from: iso(from), to: iso(to), pts: +pts.toFixed(1), v: verdict, trades: game.trades });

    var title = Math.abs(pts) < 0.05
      ? "You finished level with the Index."
      : "You finished " + Math.abs(pts).toFixed(1) + " points " + (pts > 0 ? "ahead of" : "behind") + " the Index.";
    var sub = game.trades === 0
      ? "You never left the market, so you matched the Index exactly: there was no decision to test."
      : "You beat " + beat.toLocaleString("en-US") + " of " + PLAYERS.toLocaleString("en-US") + " random players who were invested for the same " + Math.round((invDays / N) * 100) + "% of days and traded " + (game.trades === 1 ? "once." : game.trades + " times.");
    var modeLine = mode === "daily" ? "Daily challenge, " + longDay(day) + "." : mode === "shared" ? "A shared period." : "Random period.";
    var period = monthYear(from) + " to " + monthYear(to);

    var stats = [
      ["Your final value", money(you), moveHtml((you / START - 1) * 100, 1, "%")],
      ["The Index", money(idx), moveHtml((idx / START - 1) * 100, 1, "%")],
      ["You against the Index", moveHtml(pts, 1, " pts"), (function (m) {
        return '<span class="' + m.cls + '">' + m.text.replace(/^([+\u2212]?)/, "$1$").replace(/\d{4,}/, function (n) {
          return (+n).toLocaleString("en-US");
        }) + "</span>";
      })(signed(you - idx, 0, ""))],
      ["Time invested", Math.round((invDays / N) * 100) + "%", invDays + " of " + N + " days"],
      ["Trades", String(game.trades), game.trades ? Math.ceil(game.trades / 2) + " to cash, " + Math.floor(game.trades / 2) + " back in" : "Bought and held"],
      ["Best days missed", missed.length + " of 10", "the period's ten best days"]
    ].map(function (s) {
      return "<div><span>" + s[0] + "</span><b>" + s[1] + "</b><em>" + s[2] + "</em></div>";
    }).join("");

    var missedHtml = missed.length
      ? '<ul class="sim-missed">' + missed.map(function (i) {
          return "<li><span>" + medDay(dates[game.start + i]) + "</span>" + moveHtml(rets[game.start + i] * 100, 1, "%") + "<span>in cash</span></li>";
        }).join("") + "</ul>"
      : '<p class="sim-missed-none">You were in the market on all ten of the best days.</p>';

    var links = ep.links.map(function (l) {
      return '<a class="link" href="' + BASE + l[1] + '">' + esc(l[0]) + ' <svg class="icon" aria-hidden="true"><use href="#i-arrow-right"/></svg></a>';
    }).join("");

    var link = location.origin + location.pathname + "?g=" + iso(from);
    var text = "Trading Simulator by Andra Markets, " + (mode === "daily" ? "daily challenge " + longDay(day) : "two hidden years") + ": " + verdict + ". " +
      signed(pts, 1, " pts").text + " against the S&P 500 in " + game.trades + (game.trades === 1 ? " trade" : " trades") +
      (game.trades ? ", beat " + Math.round(share * 100) + "% of random players" : "") + ". Can you beat the Index?";

    var record = games.reduce(function (m, x) {
      return !m || x.pts > m.pts ? x : m;
    }, null);
    var streak = 0, d0 = new Date(day + "T00:00:00Z");
    var dailyDays = {};
    games.forEach(function (x) {
      if (x.mode === "daily") dailyDays[x.day] = 1;
    });
    while (dailyDays[iso(new Date(d0.getTime() - streak * 864e5))]) streak++;
    var rows = games.slice(0, 10).map(function (x) {
      var dd = new Date(x.t);
      return "<tr><td>" + dd.getDate() + " " + MON[dd.getMonth()] + "</td><td>" + x.from.slice(0, 4) + "–" + x.to.slice(2, 4) + "</td><td>" + moveHtml(x.pts, 1, " pts") + "</td><td>" + x.v + "</td></tr>";
    }).join("");

    var fin = main.querySelector(".sim-final");
    fin.innerHTML =
      '<div class="sim-top"><div><p class="dd__crumbs"><a href="../">Simulators</a> <span aria-hidden="true">/</span> Trading Simulator</p>' +
      '<h1 class="sim-title" id="sim-final-title" tabindex="-1">' + title + '</h1><p class="sim-mode">' + modeLine + "</p></div></div>" +
      '<section class="sim-verdict" aria-label="Skill or luck"><div><p class="sim-word">' + verdict + '</p><p class="sim-word-sub">' + sub + "</p></div>" +
      '<div><div class="sim-hist">' + histogram(finals, idx, you) + "</div>" +
      '<p class="key sim-key"><span><i class="sim-sw sim-sw--bar"></i>' + PLAYERS.toLocaleString("en-US") + ' random players</span><span><i class="sim-sw--ref"></i>Top 10%, the line for Skill</span></p></div></section>' +
      '<div class="sim-grid2"><div><div class="sim-stats">' + stats + "</div>" +
      '<h2 class="sim-h2">The best days you missed</h2>' + missedHtml +
      '<h2 class="sim-h2">Share</h2><div class="sim-share"><div><canvas class="sim-card" width="1200" height="630" role="img" aria-label="Share image: ' + verdict + ", " + esc(signed(pts, 1, " pts").text) + ' against the Index"></canvas></div>' +
      '<div><p class="sim-text">' + esc(text) + " " + esc(link) + "</p>" +
      '<div class="sim-btns"><a class="btn btn--ghost btn--sm" target="_blank" rel="noopener" href="https://www.linkedin.com/sharing/share-offsite/?url=' + encodeURIComponent(link) + '">LinkedIn</a>' +
      '<a class="btn btn--ghost btn--sm" target="_blank" rel="noopener" href="https://x.com/intent/post?text=' + encodeURIComponent(text) + "&url=" + encodeURIComponent(link) + '">X</a>' +
      '<a class="btn btn--ghost btn--sm" target="_blank" rel="noopener" href="https://wa.me/?text=' + encodeURIComponent(text + " " + link) + '">WhatsApp</a>' +
      '<button class="btn btn--ghost btn--sm" type="button" data-share="copy">Copy link</button>' +
      '<button class="btn btn--ghost btn--sm" type="button" data-share="save">Save image</button></div>' +
      '<p class="sim-share-status" role="status" aria-live="polite"></p></div></div></div>' +
      '<div><section class="sim-reveal" aria-label="The period you traded"><h2>You traded ' + period + ": " + esc(ep.title) + ".</h2><p>" + esc(ep.text) + '</p><div class="sim-links">' + links + "</div></section>" +
      '<div class="sim-stage sim-final-chart"><svg class="sim-svg" viewBox="0 0 640 300" preserveAspectRatio="none" role="img" aria-label="You against the Index, ' + esc(period) + '"></svg><div class="sim-ylabs" aria-hidden="true"></div></div>' +
      '<p class="key sim-key"><span><i class="k-solid"></i>You</span><span><i class="k-dash"></i>The Index</span><span><i class="sim-sw"></i>In cash</span><span>' + period + "</span></p>" +
      '<div class="sim-again"><button class="btn" type="button" data-again="random">Play a random period</button>' +
      (mode === "daily" ? "" : '<button class="btn btn--ghost" type="button" data-again="daily">Play today\'s challenge</button>') + "</div>" +
      '<h2 class="sim-h2">Your games</h2><table class="sim-games"><thead><tr><th scope="col">Date</th><th scope="col">Period</th><th scope="col">Against the Index</th><th scope="col">Result</th></tr></thead><tbody>' + rows + "</tbody></table>" +
      '<p class="sim-rec">Record: ' + moveHtml(record.pts, 1, " pts") + ", " + record.from.slice(0, 4) + "–" + record.to.slice(2, 4) + ". Daily streak: " + streak + (streak === 1 ? " day" : " days") + ". Saved in this browser only.</p>" +
      '<p class="sim-rec">' + (main.getAttribute("data-sim-src") || "") + " Calculated in your browser. Not investment advice.</p></div></div>";

    var pad = (Math.max.apply(null, game.you.concat(game.idx)) - Math.min.apply(null, game.you.concat(game.idx))) * 0.06;
    chartSvg(fin.querySelector(".sim-svg"), fin.querySelector(".sim-ylabs"), game,
      Math.min.apply(null, game.you.concat(game.idx)) - pad, Math.max.apply(null, game.you.concat(game.idx)) + pad, false);

    var canvas = fin.querySelector("canvas");
    drawCard(canvas, verdict, pts, share, game.trades);
    fin.querySelector('[data-share="copy"]').addEventListener("click", function () {
      var status = fin.querySelector(".sim-share-status");
      var done = function () {
        status.textContent = "Copied to the clipboard.";
      };
      if (navigator.clipboard) navigator.clipboard.writeText(text + " " + link).then(done, function () {
        status.textContent = "Copy failed: select the text above instead.";
      });
      else status.textContent = "Select the text above to copy it.";
    });
    fin.querySelector('[data-share="save"]').addEventListener("click", function () {
      var a = document.createElement("a");
      a.href = canvas.toDataURL("image/png");
      a.download = "andra-trading-simulator.png";
      document.body.appendChild(a);
      a.click();
      a.remove();
    });
    fin.querySelectorAll("[data-again]").forEach(function (b) {
      b.addEventListener("click", function () {
        reset(b.getAttribute("data-again"));
      });
    });

    main.querySelector(".sim-game").hidden = true;
    fin.hidden = false;
    window.scrollTo(0, 0);
    fin.querySelector("#sim-final-title").focus({ preventScroll: true });
  }

  // The share image (owner-approved: black, 30 Oct 2026): the whole horse
  // screen-blended on the dark ground, as on the site's social card.
  var horse = new Image();
  horse.src = BASE + "assets/andra-horse.png";
  function drawCard(canvas, verdict, pts, share, trades) {
    var ctx = canvas.getContext("2d");
    var font = '"Schibsted Grotesk", "Helvetica Neue", Arial, sans-serif';
    function paint() {
      ctx.globalCompositeOperation = "source-over";
      ctx.fillStyle = "#0a0c0d";
      ctx.fillRect(0, 0, 1200, 630);
      if (horse.complete && horse.naturalWidth) {
        ctx.globalCompositeOperation = "screen";
        ctx.globalAlpha = 0.55;
        ctx.drawImage(horse, 560, -105, 840, 840);
        ctx.globalAlpha = 1;
        ctx.globalCompositeOperation = "source-over";
      }
      ctx.fillStyle = "#e9eceb";
      ctx.font = "650 30px " + font;
      ctx.fillText("Andra Markets", 64, 92);
      ctx.font = "560 168px " + font;
      ctx.fillText(verdict + ".", 56, 330);
      ctx.font = "400 34px " + font;
      ctx.fillStyle = "#a8b0b4";
      var m = signed(pts, 1, " pts");
      var lead = "I finished ";
      ctx.fillText(lead, 64, 410);
      var x = 64 + ctx.measureText(lead).width;
      ctx.fillStyle = m.cls === "mv--up" ? "#1fd27a" : m.cls === "mv--down" ? "#ff4b52" : "#e9eceb";
      ctx.font = "500 34px " + font;
      ctx.fillText(m.text, x, 410);
      x += ctx.measureText(m.text).width;
      ctx.fillStyle = "#a8b0b4";
      ctx.font = "400 34px " + font;
      ctx.fillText(" against the S&P 500", x, 410);
      ctx.fillText(trades ? "and beat " + Math.round(share * 100) + "% of random players." : "and never left the market.", 64, 458);
      ctx.font = "400 24px " + font;
      ctx.fillText("Trading Simulator, on Andra Markets", 64, 566);
    }
    paint();
    var redo = function () {
      paint();
    };
    horse.addEventListener("load", redo, { once: true });
    if (document.fonts && document.fonts.load) {
      Promise.all([document.fonts.load("560 168px 'Schibsted Grotesk'"), document.fonts.load("400 34px 'Schibsted Grotesk'"), document.fonts.load("650 30px 'Schibsted Grotesk'")]).then(redo, function () {});
    }
  }

  // ---- Controls -----------------------------------------------------------
  function reset(m) {
    clearInterval(timer);
    g = null;
    playing = false;
    if (m === "daily") setMode("daily", dailyStart(todayIso()));
    else setMode("random", Math.floor(Math.random() * (LAST_START + 1)));
    main.querySelector(".sim-final").hidden = true;
    main.querySelector(".sim-game").hidden = false;
    $("alt").parentNode.hidden = false;
    $("pause").disabled = true;
    $("pause").textContent = "Pause";
    $("chart").innerHTML = "";
    $("ylabs").innerHTML = "";
    $("dot").hidden = true;
    $("month").innerHTML = "Month 1 <small>of 24</small>";
    $("prog").style.width = "0";
    $("day").textContent = "Trading day 0 of " + N;
    ["you", "idx"].forEach(function (k) {
      $(k).textContent = money(START);
      setMove($(k + "-chg"), 0, 1, "%");
    });
    $("trades").textContent = "0";
    $("invested").textContent = "100%";
    setMove($("gap"), 0, 1, " pts");
    window.scrollTo(0, 0);
  }

  $("go").addEventListener("click", toggle);
  $("pause").addEventListener("click", function () {
    if (!g) return;
    if (playing) pause();
    else play();
  });
  $("alt").addEventListener("click", function () {
    reset(mode === "daily" ? "random" : "daily");
  });
  main.querySelectorAll("[data-speed]").forEach(function (b) {
    b.addEventListener("click", function () {
      setSpeed(b.getAttribute("data-speed"));
    });
  });
  function setSpeed(v) {
    speed = v;
    main.querySelectorAll("[data-speed]").forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-speed") === v ? "true" : "false");
    });
    if (playing) loop();
  }
  document.addEventListener("keydown", function (e) {
    if (main.querySelector(".sim-game").hidden || e.metaKey || e.ctrlKey || e.altKey) return;
    var tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || e.target.isContentEditable || document.querySelector(".pal:not([hidden])")) return;
    if (e.key === " " || e.code === "Space") {
      e.preventDefault();
      if (!e.repeat) toggle();
    } else if (e.key === "p" || e.key === "P") {
      if (g) (playing ? pause : play)();
    } else if (/^[1-4]$/.test(e.key)) {
      setSpeed(["0.5", "1", "2", "4"][+e.key - 1]);
    }
  });
  // A space released on a focused button must not click it a second time.
  document.addEventListener("keyup", function (e) {
    if ((e.key === " " || e.code === "Space") && !main.querySelector(".sim-game").hidden && /^(button|a)$/i.test(e.target.tagName)) e.preventDefault();
  });
  document.addEventListener("visibilitychange", function () {
    if (document.hidden && playing) pause();
  });

  if (shared >= 0) setMode("shared", shared);
  else setMode("daily", dailyStart(todayIso()));
})();
