// Andra Markets Simulators: the chart game behind the Trading Simulator and the
// Panic Test. Runs entirely in the browser; each market's history comes from
// assets/simdata-<market>.js (window.ANDRA_SIMDATA, written by
// tools/build_site.py), loaded when the market is picked. Games played are kept
// in this browser's localStorage only.
(function () {
  "use strict";
  var main = document.querySelector(".sim-page");
  var cfgEl = document.getElementById("sim-config");
  if (!main || !cfgEl) return;
  var CFG = JSON.parse(cfgEl.textContent);
  var PANIC = CFG.game === "panic";
  var BASE = main.getAttribute("data-base") || "../../";
  var N = PANIC ? 756 : 504; // trading days in a game: three years or two
  var MONTHS_N = N / 21;
  var START = 10000;
  var CASH = Math.log(1.02) / 252; // a flat 2% a year, per trading day, as a log return
  var SPEEDS = ["0.5", "1", "2", "4"];
  var MS = { "0.5": 200, "1": 100, "2": 50, "4": 25 }; // ms per trading day
  var PLAYERS = 1000;
  var STORE = PANIC ? "andra-panic-games" : "andra-sim-games";
  var RIVAL = PANIC ? "holding on" : "the Index";
  var RIVAL_TAG = PANIC ? "Holding on" : "Index";
  var OUT_WORD = PANIC ? "Sold" : "Cash";
  var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  var W = 640, H = 300, PAD = 10;

  function $(name) {
    return main.querySelector('[data-sim="' + name + '"]');
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
  function money(v) {
    return "$" + Math.round(v).toLocaleString("en-US");
  }
  // A rise or a fall carries its sign and its colour (DESIGN.md, The Rise and
  // Fall Rule); a figure that rounds to zero carries neither.
  function signed(v, dec, unit) {
    var s = Math.abs(v).toFixed(dec);
    if (+s === 0) return { text: (0).toFixed(dec) + unit, cls: "" };
    return { text: (v > 0 ? "+" : "−") + s + unit, cls: v > 0 ? "mv--up" : "mv--down" };
  }
  function moveHtml(v, dec, unit) {
    var m = signed(v, dec, unit);
    return '<span class="' + m.cls + '">' + m.text + "</span>";
  }
  function dollarsHtml(v) {
    var m = signed(v, 0, "");
    return '<span class="' + m.cls + '">' + m.text.replace(/^([+−]?)(\d+)/, function (_, s, n) {
      return s + "$" + (+n).toLocaleString("en-US");
    }) + "</span>";
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
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
  function icon(name) {
    return '<svg class="icon" aria-hidden="true"><use href="#i-' + name + '"/></svg>';
  }

  // ---- Markets ------------------------------------------------------------
  var markets = {};
  CFG.markets.forEach(function (m) {
    markets[m.key] = m;
  });
  var hist = {}; // key -> { dates, rets, crashes }
  function loadMarket(key, done) {
    if (hist[key]) return done(hist[key]);
    var have = window.ANDRA_SIMDATA && window.ANDRA_SIMDATA[key];
    if (have) return done(unpack(key, have));
    var s = document.createElement("script");
    s.src = BASE + "assets/" + markets[key].file;
    s.onload = function () {
      done(unpack(key, window.ANDRA_SIMDATA[key]));
    };
    s.onerror = function () {
      $("intro-note").textContent = "This market's history did not load. Try again later.";
    };
    document.head.appendChild(s);
  }
  function unpack(key, data) {
    var dates = [], rets = [];
    var t = Date.parse(data.first + "T00:00:00Z");
    var r = data.r.split(",");
    for (var i = 0; i < r.length; i++) {
      t += parseInt(data.gaps.charAt(i), 36) * 864e5;
      dates.push(new Date(t));
      rets.push(+r[i] / 1e5);
    }
    hist[key] = { dates: dates, rets: rets, crashes: PANIC ? crashes(rets) : null };
    return hist[key];
  }
  // Every fall of 25% or more from a record close: the game starts at that
  // record. level[i] is the close after return i.
  function crashes(rets) {
    var level = [], v = 1, i;
    for (i = 0; i < rets.length; i++) level.push((v *= 1 + rets[i]));
    var out = [], peak = 0, low = 0, deep = false;
    for (i = 1; i < level.length; i++) {
      if (level[i] >= level[peak]) {
        if (deep) out.push({ peak: peak, low: low, back: i });
        peak = i;
        low = i;
        deep = false;
      } else {
        if (level[i] < level[low]) low = i;
        if (level[low] / level[peak] <= 0.75) deep = true;
      }
    }
    if (deep) out.push({ peak: peak, low: low, back: -1 });
    return out
      .filter(function (c) {
        return c.peak + 252 < rets.length;
      })
      .map(function (c) {
        c.fall = level[c.low] / level[c.peak] - 1;
        return c;
      });
  }

  // ---- Setup --------------------------------------------------------------
  var params = new URLSearchParams(location.search);
  var mode = PANIC ? "crash" : "daily";
  var market = markets[params.get("m")] ? params.get("m") : CFG.markets[0].key;
  var start = 0, n = N, crash = null;
  var H_ = null; // the loaded market

  function dailyStart(h) {
    return Math.floor(rng(hash("andra-sim-" + todayIso() + (market === "sp500" ? "" : "-" + market)))() * (h.rets.length - N + 1));
  }
  function startFromDate(h, isoDay) {
    var t = Date.parse(isoDay + "T00:00:00Z");
    if (isNaN(t)) return -1;
    for (var i = 0; i < h.dates.length; i++) if (h.dates[i].getTime() >= t) return i;
    return -1;
  }
  function pickCrash(h, avoid) {
    var list = h.crashes.filter(function (c) {
      return c.peak !== avoid;
    });
    return list[Math.floor(Math.random() * list.length)] || h.crashes[0];
  }

  function setTag() {
    var name = markets[market].name;
    $("tag").textContent = PANIC ? "A hidden crash · " + name
      : (mode === "daily" ? "Daily challenge, " + longDay(todayIso()) : mode === "shared" ? "Shared period" : "Random period") + " · " + name;
  }

  function intro() {
    var m = markets[market];
    $("intro").hidden = false;
    $("intro-title").textContent = PANIC ? "A crash is coming" : "Two hidden years of the " + m.name;
    $("intro-text").textContent = PANIC
      ? "You hold $10,000 in the " + m.name + " at its last high before one of its great falls. You won't know which. Sell when you can't take any more, buy back when you are ready. Can you beat simply holding on?"
      : "You start with $10,000 invested, just like the Index. Step out to cash and back in as often as you like. Finish ahead of the Index.";
    var note = m.note === "with dividends" ? "Returns include dividends." : "Prices only: dividends are not included.";
    $("intro-note").textContent = note;
    if (PANIC && hist[market]) $("intro-note").textContent = hist[market].crashes.length + " falls of 25% or more on record in the " + m.name + ". " + note;
    var modes = $("modes");
    modes.hidden = PANIC;
    if (!PANIC) modes.querySelectorAll("[data-mode]").forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-mode") === mode || (mode === "shared" && b.getAttribute("data-mode") === "random") ? "true" : "false");
    });
    $("markets").querySelectorAll("[data-market]").forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-market") === market ? "true" : "false");
    });
    setTag();
  }

  $("markets").hidden = CFG.markets.length < 2;
  $("markets").addEventListener("click", function (e) {
    var b = e.target.closest("[data-market]");
    if (!b || g) return;
    market = b.getAttribute("data-market");
    if (mode === "shared") mode = "random";
    loadMarket(market, function () {
      intro();
    });
    intro();
  });
  $("modes").addEventListener("click", function (e) {
    var b = e.target.closest("[data-mode]");
    if (!b || g) return;
    mode = b.getAttribute("data-mode");
    intro();
  });

  // ---- Game ---------------------------------------------------------------
  var g = null, timer = null, speed = "1", playing = false;

  function begin() {
    loadMarket(market, function (h) {
      H_ = h;
      if (PANIC) {
        var last = loadGames()[0];
        var shared = params.get("g") && markets[params.get("m")] === markets[market] ? startFromDate(h, params.get("g")) : -1;
        crash = h.crashes.filter(function (c) {
          return c.peak === shared;
        })[0] || pickCrash(h, last && last.market === market ? startFromDate(h, last.from) : -1);
        start = crash.peak + 1;
        n = Math.min(N, h.rets.length - start);
      } else {
        var s = mode === "shared" ? startFromDate(h, params.get("g")) : -1;
        if (mode === "shared" && (s < 0 || s > h.rets.length - N)) mode = "random";
        start = mode === "daily" ? dailyStart(h) : mode === "shared" ? s : Math.floor(Math.random() * (h.rets.length - N + 1));
        n = N;
      }
      params.delete("g");
      g = { start: start, n: n, day: 0, inv: true, pos: [], you: [START], idx: [START], trades: 0, lo: START * 0.94, hi: START * 1.06, since: 0 };
      $("intro").hidden = true;
      $("row").hidden = false;
      setTag();
      play();
      draw();
    });
  }

  function step() {
    var r = H_.rets[g.start + g.day];
    g.pos.push(g.inv);
    g.idx.push(g.idx[g.day] * (1 + r));
    g.you.push(g.you[g.day] * (g.inv ? 1 + r : Math.exp(CASH)));
    g.day++;
    g.lo = Math.min(g.lo, g.you[g.day], g.idx[g.day]);
    g.hi = Math.max(g.hi, g.you[g.day], g.idx[g.day]);
    draw();
    if (g.day >= g.n) finish();
  }
  function loop() {
    clearInterval(timer);
    timer = setInterval(step, MS[speed]);
  }
  function play() {
    playing = true;
    $("pause").innerHTML = icon("pause");
    $("pause").setAttribute("aria-label", "Pause");
    loop();
  }
  function pause() {
    playing = false;
    clearInterval(timer);
    $("pause").innerHTML = icon("play");
    $("pause").setAttribute("aria-label", "Resume");
  }
  function toggle() {
    if (!g) return begin();
    if (!playing) return;
    g.inv = !g.inv;
    g.trades++;
    g.since = g.day;
    $("live").textContent = PANIC ? (g.inv ? "Bought back" : "Sold") : g.inv ? "Back in the market" : "Moved to cash";
    draw();
  }
  function setSpeed(v) {
    speed = v;
    $("speed").textContent = v + "x";
    $("speed").setAttribute("aria-label", "Speed, " + v + "x");
    if (playing) loop();
  }

  // ---- Drawing ------------------------------------------------------------
  function niceStep(span) {
    var raw = span / 4, p = Math.pow(10, Math.floor(Math.log10(raw)));
    var k = raw / p;
    return (k < 1.5 ? 1 : k < 3 ? 2 : k < 7 ? 5 : 10) * p;
  }
  function stateWords(inv) {
    return PANIC ? (inv ? "holding" : "sold") : inv ? "in the market" : "in cash";
  }
  // The chart: cash stretches as labelled bands, the rival dashed, your line
  // heavy in the market and light out of it; with `now`, the day's line, the
  // dot (hollow out of the market) and labels at the head of both lines.
  function chart(svg, labs, marks, game, now) {
    var len = game.day, span = game.n;
    var lo = game.lo, hi = game.hi, pad = (hi - lo) * 0.06;
    lo -= pad;
    hi += pad;
    var x = function (i) {
      return (i / span) * W;
    };
    var y = function (v) {
      return PAD + ((hi - v) / (hi - lo)) * (H - 2 * PAD);
    };
    var out = [], tags = [], i, a = -1;
    for (i = 0; i <= len; i++) {
      var off = i < len && !game.pos[i];
      if (off && a < 0) a = i;
      if (!off && a >= 0) {
        out.push('<rect class="sim-cash" x="' + x(a).toFixed(1) + '" y="0" width="' + (x(i) - x(a)).toFixed(1) + '" height="' + H + '"/>');
        if ((i - a) / span > 0.04) tags.push('<span class="sim-bandlab" style="left:' + ((x(a) / W) * 100).toFixed(2) + '%">' + OUT_WORD + "</span>");
        a = -1;
      }
    }
    var st = niceStep(hi - lo), lab = [];
    for (var v = Math.ceil(lo / st) * st; v < hi; v += st) {
      out.push('<line class="sim-grid" x1="0" x2="' + W + '" y1="' + y(v).toFixed(1) + '" y2="' + y(v).toFixed(1) + '"/>');
      lab.push('<span style="top:' + ((y(v) / H) * 100).toFixed(1) + '%">' + money(v) + "</span>");
    }
    var d = "";
    for (i = 0; i <= len; i++) d += (i ? "L" : "M") + x(i).toFixed(1) + "," + y(game.idx[i]).toFixed(1);
    out.push('<path class="sim-idx" d="' + d + '"/>');
    // Your line in runs: day i's return is drawn from point i to i + 1.
    var runStart = 0;
    for (i = 1; i <= len; i++) {
      if (i === len || game.pos[i] !== game.pos[runStart]) {
        d = "";
        for (var j = runStart; j <= i; j++) d += (j > runStart ? "L" : "M") + x(j).toFixed(1) + "," + y(game.you[j]).toFixed(1);
        out.push('<path class="' + (game.pos[runStart] ? "sim-in" : "sim-out") + '" d="' + d + '"/>');
        runStart = i;
      }
    }
    if (len === 0) out.push('<path class="sim-in" d="M0,' + y(START).toFixed(1) + 'L1,' + y(START).toFixed(1) + '"/>');
    if (now) {
      out.push('<line class="sim-now" x1="' + x(len).toFixed(1) + '" x2="' + x(len).toFixed(1) + '" y1="0" y2="' + H + '"/>');
      var px = (x(len) / W) * 100, yy = (y(game.you[len]) / H) * 100, yi = (y(game.idx[len]) / H) * 100;
      var gapPct = Math.abs(yy - yi), minGap = 7;
      if (gapPct < minGap) {
        var mid = (yy + yi) / 2, sgn = yy <= yi ? -1 : 1;
        yy = mid + (sgn * minGap) / 2;
        yi = mid - (sgn * minGap) / 2;
      }
      var side = px > 72 ? " sim-label--left" : "";
      tags.push('<i class="sim-dot' + (game.inv ? "" : " sim-dot--out") + '" style="left:' + px.toFixed(2) + "%;top:" + ((y(game.you[len]) / H) * 100).toFixed(2) + '%"></i>');
      tags.push('<span class="sim-label sim-label--you' + side + '" style="left:' + px.toFixed(2) + "%;top:" + yy.toFixed(2) + '%"><b>You, ' + stateWords(game.inv) + "</b>" + money(game.you[len]) + "</span>");
      tags.push('<span class="sim-label' + side + '" style="left:' + px.toFixed(2) + "%;top:" + yi.toFixed(2) + '%">' + RIVAL_TAG + " " + money(game.idx[len]) + "</span>");
    }
    svg.innerHTML = out.join("");
    labs.innerHTML = lab.join("");
    marks.innerHTML = tags.join("");
  }
  function ribbon(el, game) {
    var out = [], a = 0;
    for (var i = 1; i <= game.day; i++) {
      if (i === game.day || game.pos[i] !== game.pos[a]) {
        out.push('<i class="' + (game.pos[a] ? "" : "sim-r-out") + '" style="left:' + ((a / game.n) * 100).toFixed(2) + "%;width:" + (((i - a) / game.n) * 100).toFixed(2) + '%"></i>');
        a = i;
      }
    }
    el.innerHTML = out.join("");
  }
  function gapWords(pts) {
    return Math.abs(pts) < 0.05 ? "level with " + RIVAL : (pts > 0 ? "ahead of " : "behind ") + RIVAL;
  }
  function draw() {
    chart($("chart"), $("ylabs"), $("marks"), g, true);
    ribbon($("ribbon"), g);
    var pts = (g.you[g.day] - g.idx[g.day]) / 100, m = signed(pts, 1, " pts");
    $("gap").textContent = m.text;
    $("gap").className = m.cls;
    $("gap-sub").textContent = gapWords(pts);
    var month = Math.min(MONTHS_N, Math.floor(g.day / 21) + 1), since = Math.min(MONTHS_N, Math.floor(g.since / 21) + 1);
    $("month").textContent = "Month " + month + " of " + Math.ceil(g.n / 21);
    $("since").textContent = PANIC
      ? (g.inv ? (g.trades ? "Back in since month " + since : "Holding since the start") : "Sold in month " + since)
      : (g.inv ? (g.trades ? "In the market since month " + since : "In the market since the start") : "In cash since month " + since);
    $("go").firstElementChild.textContent = PANIC ? (g.inv ? "Sell" : "Buy back") : g.inv ? "Go to cash" : "Back in the market";
  }
  function idle() {
    var blank = { day: 0, n: N, pos: [], you: [START], idx: [START], lo: START * 0.94, hi: START * 1.06, inv: true };
    chart($("chart"), $("ylabs"), $("marks"), blank, false);
    $("ribbon").innerHTML = "";
    $("gap").textContent = "0.0 pts";
    $("gap").className = "";
    $("gap-sub").textContent = gapWords(0);
    $("month").textContent = "Month 1 of " + MONTHS_N;
    $("since").textContent = "Ready";
  }

  // ---- The end ------------------------------------------------------------
  // Random players with the same number of trades and the same days invested:
  // the days in and out are each split at random points into as many stretches
  // as the player had, alternating from a start in the market.
  function skill(game, invDays) {
    var L = [0];
    for (var i = 0; i < game.n; i++) L.push(L[i] + Math.log(1 + H_.rets[game.start + i]));
    var k = game.trades, nInv = Math.floor(k / 2) + 1, nOut = Math.ceil(k / 2), outDays = game.n - invDays;
    var rand = rng(hash("players-" + market + "-" + game.start + "-" + k + "-" + invDays));
    function parts(total, count) {
      if (count === 0) return [];
      var cuts = [], pos = total >= count;
      while (cuts.length < count - 1) {
        var c = pos ? 1 + Math.floor(rand() * (total - 1)) : Math.floor(rand() * (total + 1));
        if (!pos || cuts.indexOf(c) < 0) cuts.push(c);
      }
      cuts.sort(function (a, b) {
        return a - b;
      });
      var out = [], prev = 0;
      cuts.forEach(function (c) {
        out.push(c - prev);
        prev = c;
      });
      out.push(total - prev);
      return out;
    }
    var finals = [];
    for (var p = 0; p < PLAYERS; p++) {
      var a = parts(invDays, nInv), o = parts(outDays, nOut), d = 0, lg = 0;
      for (var s = 0; s < a.length; s++) {
        lg += L[d + a[s]] - L[d];
        d += a[s];
        if (s < o.length) {
          lg += o[s] * CASH;
          d += o[s];
        }
      }
      finals.push(START * Math.exp(lg));
    }
    return finals;
  }
  function episodeFor(from, to) {
    var best = null, most = -1;
    var a = from.getUTCFullYear() * 12 + from.getUTCMonth(), b = to.getUTCFullYear() * 12 + to.getUTCMonth();
    (CFG.episodes[market] || []).forEach(function (e) {
      var ea = +e.from.slice(0, 4) * 12 + +e.from.slice(5, 7) - 1, eb = +e.to.slice(0, 4) * 12 + +e.to.slice(5, 7) - 1;
      var o = Math.min(b, eb) - Math.max(a, ea);
      if (o > most) {
        most = o;
        best = e;
      }
    });
    return best;
  }

  function finish() {
    clearInterval(timer);
    playing = false;
    var game = g, name = markets[market].name;
    var you = game.you[game.n], idx = game.idx[game.n], pts = (you - idx) / 100;
    var invDays = game.pos.filter(Boolean).length;
    var from = H_.dates[game.start - (PANIC ? 1 : 0)], to = H_.dates[game.start + game.n - 1];
    var ep = episodeFor(from, PANIC ? H_.dates[crash.low] : to);
    var period = PANIC ? monthYear(from) : monthYear(from) + " to " + monthYear(to);
    var word, sub, share = 0, verdict;

    if (PANIC) {
      word = game.trades === 0 ? "Steady" : pts > 0.05 ? "Well timed" : pts < -0.05 ? "Panic" : "Even";
      sub = "You finished " + (Math.abs(pts) < 0.05 ? "level with holding on." : moveHtml(pts, 1, " pts") + (pts > 0 ? " ahead of holding on." : " behind holding on.")) +
        (game.trades === 0 ? " You never sold." : " You sold " + Math.ceil(game.trades / 2) + (Math.ceil(game.trades / 2) === 1 ? " time." : " times."));
      verdict = word;
    } else {
      var finals = skill(game, invDays), below = 0;
      finals.forEach(function (v) {
        if (v < you - 1e-6) below++;
        else if (Math.abs(v - you) <= 1e-6) below += 0.5;
      });
      share = below / PLAYERS;
      word = verdict = share >= 0.9 ? "Skill" : "Luck";
      sub = "You finished " + (Math.abs(pts) < 0.05 ? "level with the Index" : moveHtml(pts, 1, " pts") + (pts > 0 ? " ahead of the Index" : " behind the Index")) +
        (game.trades === 0 ? ". You never left the market, so there was no decision to test." : ", better than " + Math.floor(below).toLocaleString("en-US") + " of 1,000 random players who were invested as long and traded as often.");
    }

    var day = todayIso();
    var games = saveGame({ t: Date.now(), mode: PANIC ? "crash" : mode, market: market, day: day, from: iso(from), to: iso(to), pts: +pts.toFixed(1), v: verdict, trades: game.trades });

    var link = location.origin + location.pathname + "?g=" + iso(PANIC ? H_.dates[crash.peak] : from) + "&m=" + market;
    var text = PANIC
      ? "Panic Test by Andra Markets: " + word + ". I finished " + signed(pts, 1, " pts").text + " against holding on through a hidden " + name + " crash. Could you hold on?"
      : "Trading Simulator by Andra Markets, " + (mode === "daily" ? "daily challenge " + longDay(day) : "two hidden years") + ": " + word + ". " + signed(pts, 1, " pts").text + " against the " + name + " in " + game.trades + (game.trades === 1 ? " trade" : " trades") + (game.trades ? ", beat " + Math.round(share * 100) + "% of random players" : "") + ". Can you beat the Index?";

    var right = '<div class="sim-stage"><svg class="sim-svg" viewBox="0 0 640 300" preserveAspectRatio="none" role="img" aria-label="You against ' + RIVAL + ", " + esc(period) + '"></svg><div class="sim-ylabs" aria-hidden="true"></div><div></div></div><div class="sim-ribbon" aria-hidden="true"></div>' + $("key").outerHTML.replace(' data-sim="key"', "");

    var links = (ep ? ep.links : []).map(function (l) {
      return '<a class="link" href="' + BASE + l[1] + '">' + esc(l[0]) + " " + icon("arrow-right") + "</a>";
    }).join("");
    var reveal;
    if (PANIC) {
      var back = crash.back >= 0 ? H_.dates[crash.back] : null;
      var yrs = back ? (back - H_.dates[crash.peak]) / (365.25 * 864e5) : 0;
      var fallLine = "From its record on " + longDay(iso(H_.dates[crash.peak])) + " the " + name + " fell " + Math.abs(Math.round(crash.fall * 100)) + "% by " + monthYear(H_.dates[crash.low]) +
        (back ? " and regained its record in " + monthYear(back) + ", " + (yrs < 1.5 ? Math.max(1, Math.round(yrs * 12)) + " months" : (Math.round(yrs * 10) / 10).toString().replace(/\.0$/, "") + " years") + " later." : " and has not regained it yet.") +
        (markets[market].note === "with dividends" ? " Figures include dividends." : " Prices only.");
      reveal = '<section class="sim-r"><div><h2>This was ' + monthYear(H_.dates[crash.peak]) + (ep ? ": " + esc(ep.title) : "") + '.</h2></div><div><p><b>' + esc(fallLine) + "</b></p>" + (ep ? "<p>" + esc(ep.text) + "</p>" : "") + '<div class="sim-links">' + links + "</div></div></section>";
    } else {
      reveal = '<section class="sim-r"><div><h2>You traded ' + period + (ep ? ": " + esc(ep.title) : "") + '.</h2></div><div>' + (ep ? "<p>" + esc(ep.text) + "</p>" : "") + '<div class="sim-links">' + links + "</div></div></section>";
    }

    var line;
    if (PANIC) {
      line = "<span>You <b>" + money(you) + "</b> " + moveHtml((you / START - 1) * 100, 1, "%") + "</span><span>Holding on <b>" + money(idx) + "</b> " + moveHtml((idx / START - 1) * 100, 1, "%") + "</span><span>Out of the market <b>" + Math.round(((game.n - invDays) / game.n) * 100) + "%</b> of days</span><span>Difference " + dollarsHtml(you - idx) + "</span>";
    } else {
      var order = [];
      for (var i = 0; i < game.n; i++) order.push(i);
      order.sort(function (a, b) {
        return H_.rets[game.start + b] - H_.rets[game.start + a];
      });
      var missed = order.slice(0, 10).filter(function (i) {
        return !game.pos[i];
      });
      line = "<span>You <b>" + money(you) + "</b> " + moveHtml((you / START - 1) * 100, 1, "%") + "</span><span>The Index <b>" + money(idx) + "</b> " + moveHtml((idx / START - 1) * 100, 1, "%") + "</span><span>Invested <b>" + Math.round((invDays / game.n) * 100) + "%</b>, " + game.trades + (game.trades === 1 ? " trade" : " trades") + "</span><span>Missed <b>" + missed.length + "</b> of the 10 best days" +
        (missed.length ? " (" + missed.slice(0, 3).map(function (i) {
          return medDay(H_.dates[game.start + i]) + " " + moveHtml(H_.rets[game.start + i] * 100, 1, "%");
        }).join(", ") + (missed.length > 3 ? ", …" : "") + ")" : "") + "</span>";
    }

    var rows = games.slice(0, 10).map(function (x) {
      var d = new Date(x.t);
      return "<tr><td>" + d.getDate() + " " + MON[d.getMonth()] + "</td><td>" + esc((markets[x.market] || markets[CFG.markets[0].key]).name) + "</td><td>" + x.from.slice(0, 4) + (PANIC ? "" : "–" + x.to.slice(2, 4)) + "</td><td>" + moveHtml(x.pts, 1, " pts") + "</td><td>" + x.v + "</td></tr>";
    }).join("");
    var record = games.reduce(function (m, x) {
      return !m || x.pts > m.pts ? x : m;
    }, null);
    var streak = 0;
    if (!PANIC) {
      var dd = {};
      games.forEach(function (x) {
        if (x.mode === "daily") dd[x.day] = 1;
      });
      var d0 = new Date(day + "T00:00:00Z");
      while (dd[iso(new Date(d0.getTime() - streak * 864e5))]) streak++;
    }

    var fin = main.querySelector(".sim-final");
    fin.innerHTML =
      main.querySelector(".sim-head").outerHTML.replace('data-sim="tag"', "").replace(/<h1 class="sim-title">/, '<h1 class="sim-title" id="sim-final-title" tabindex="-1">') +
      '<section class="sim-v"><div><p class="sim-word' + (word.length > 6 ? " sim-word--long" : "") + '">' + word + '</p><p class="sim-sub">' + sub + '</p><div class="sim-act"><button class="btn" type="button" data-act="again">Play again</button><button class="btn btn--ghost" type="button" data-act="share" aria-expanded="false">Share</button></div></div>' +
      "<div>" + right + "</div></section>" +
      '<section class="sim-share" data-act="panel" hidden><div><canvas class="sim-card" width="1200" height="630" role="img" aria-label="Share image: ' + esc(word) + ", " + esc(signed(pts, 1, " pts").text) + ", with the chart of your game against " + RIVAL + '"></canvas></div><div><p class="sim-text">' + esc(text) + " " + esc(link) + "</p>" +
      '<div class="sim-btns"><a class="btn btn--ghost btn--sm" target="_blank" rel="noopener" href="https://www.linkedin.com/sharing/share-offsite/?url=' + encodeURIComponent(link) + '">LinkedIn</a>' +
      '<a class="btn btn--ghost btn--sm" target="_blank" rel="noopener" href="https://x.com/intent/post?text=' + encodeURIComponent(text) + "&url=" + encodeURIComponent(link) + '">X</a>' +
      '<a class="btn btn--ghost btn--sm" target="_blank" rel="noopener" href="https://wa.me/?text=' + encodeURIComponent(text + " " + link) + '">WhatsApp</a>' +
      '<button class="btn btn--ghost btn--sm" type="button" data-act="copy">Copy link</button><button class="btn btn--ghost btn--sm" type="button" data-act="save">Save image</button></div><p class="sim-status" role="status" aria-live="polite"></p></div></section>' +
      reveal +
      '<p class="sim-line">' + line + "</p>" +
      '<details class="sim-more"><summary>Your games and record</summary><div><table class="sim-games"><thead><tr><th scope="col">Date</th><th scope="col">Market</th><th scope="col">' + (PANIC ? "Crash" : "Period") + '</th><th scope="col">Against ' + RIVAL + '</th><th scope="col">Result</th></tr></thead><tbody>' + rows + "</tbody></table>" +
      '<p class="sim-rec">Record: ' + moveHtml(record.pts, 1, " pts") + ", " + esc((markets[record.market] || markets[CFG.markets[0].key]).name) + " " + record.from.slice(0, 4) + "." + (PANIC ? "" : " Daily streak: " + streak + (streak === 1 ? " day." : " days.")) + " Saved in this browser only.</p>" +
      '<p class="sim-src">' + esc(CFG.src) + ". Calculated in your browser. Not investment advice.</p></div></details>";

    var stages = fin.querySelectorAll(".sim-stage");
    var last = stages[stages.length - 1];
    chart(last.querySelector("svg"), last.querySelector(".sim-ylabs"), last.lastElementChild, game, false);
    ribbon(last.nextElementSibling, game);

    var canvas = fin.querySelector("canvas");
    fin.querySelector('[data-act="share"]').addEventListener("click", function (e) {
      var panel = fin.querySelector('[data-act="panel"]');
      panel.hidden = !panel.hidden;
      e.currentTarget.setAttribute("aria-expanded", panel.hidden ? "false" : "true");
      if (!panel.hidden) drawCard(canvas, game, word, pts, share, name);
    });
    fin.querySelector('[data-act="copy"]').addEventListener("click", function () {
      var status = fin.querySelector(".sim-status");
      if (navigator.clipboard) navigator.clipboard.writeText(text + " " + link).then(function () {
        status.textContent = "Copied to the clipboard.";
      }, function () {
        status.textContent = "Copy failed: select the text above instead.";
      });
      else status.textContent = "Select the text above to copy it.";
    });
    fin.querySelector('[data-act="save"]').addEventListener("click", function () {
      var a = document.createElement("a");
      a.href = canvas.toDataURL("image/png");
      a.download = PANIC ? "andra-panic-test.png" : "andra-trading-simulator.png";
      document.body.appendChild(a);
      a.click();
      a.remove();
    });
    fin.querySelector('[data-act="again"]').addEventListener("click", reset);

    main.querySelector(".sim-play").hidden = true;
    fin.hidden = false;
    window.scrollTo(0, 0);
    fin.querySelector("#sim-final-title").focus({ preventScroll: true });
  }

  // The share image (owner-approved, 1 Nov 2026; black since 30 Oct): the
  // mark and the wordmark, the word and the sentence across the top, and the
  // game's chart the full width below it, drawn as on the end screen.
  var mark = new Image();
  mark.src = BASE + "assets/andra-mark-dark.png";
  var CARD = { ground: "#0a0c0d", ink: "#e9eceb", ink2: "#a8b0b4", ink3: "#899196", grid: "rgba(233,236,235,0.09)", fill: "rgba(233,236,235,0.08)", up: "#1fd27a", down: "#ff4b52" };

  // The chart in the box (bx, by, bw, bh): stretches out of the market as
  // bands labelled at their top, the grid with its dollar labels, the rival
  // dashed, your line heavy in the market and light out of it, then the strip.
  function cardChart(ctx, game, bx, by, bw, bh, font) {
    var span = game.n, lo = game.lo, hi = game.hi, pad = (hi - lo) * 0.06;
    lo -= pad;
    hi += pad;
    var x = function (i) {
      return bx + (i / span) * bw;
    };
    var y = function (v) {
      return by + 8 + ((hi - v) / (hi - lo)) * (bh - 16);
    };
    var i, j, a = -1;
    ctx.font = "400 18px " + font;
    for (i = 0; i <= span; i++) {
      var off = i < span && !game.pos[i];
      if (off && a < 0) a = i;
      if (!off && a >= 0) {
        ctx.fillStyle = CARD.fill;
        ctx.fillRect(x(a), by, x(i) - x(a), bh);
        if (x(i) - x(a) > ctx.measureText(OUT_WORD).width + 16) {
          ctx.fillStyle = CARD.ink2;
          ctx.fillText(OUT_WORD, x(a) + 8, by + 24);
        }
        a = -1;
      }
    }
    var st = niceStep(hi - lo);
    for (var v = Math.ceil(lo / st) * st; v < hi; v += st) {
      ctx.fillStyle = CARD.grid;
      ctx.fillRect(bx, Math.round(y(v)), bw, 1);
      ctx.fillStyle = CARD.ink3;
      ctx.fillText(money(v), bx, y(v) - 7);
    }
    ctx.lineJoin = "round";
    ctx.strokeStyle = CARD.ink3;
    ctx.lineWidth = 1.6;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    for (i = 0; i <= span; i++) ctx[i ? "lineTo" : "moveTo"](x(i), y(game.idx[i]));
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.strokeStyle = CARD.ink;
    var runStart = 0;
    for (i = 1; i <= span; i++) {
      if (i === span || game.pos[i] !== game.pos[runStart]) {
        ctx.lineWidth = game.pos[runStart] ? 3.4 : 1.6;
        ctx.beginPath();
        for (j = runStart; j <= i; j++) ctx[j > runStart ? "lineTo" : "moveTo"](x(j), y(game.you[j]));
        ctx.stroke();
        runStart = i;
      }
    }
    var sy = by + bh + 14;
    a = 0;
    for (i = 1; i <= span; i++) {
      if (i === span || game.pos[i] !== game.pos[a]) {
        ctx.fillStyle = game.pos[a] ? CARD.ink : CARD.ink3;
        if (game.pos[a]) ctx.fillRect(x(a), sy, x(i) - x(a), 12);
        else ctx.fillRect(x(a), sy + 5, x(i) - x(a), 2);
        a = i;
      }
    }
  }

  // The key: your line, a band (only when you left the market), the rival.
  function cardKey(ctx, kx, ky, font, trades) {
    ctx.font = "400 20px " + font;
    ctx.fillStyle = CARD.ink;
    ctx.fillRect(kx, ky - 8.5, 22, 3);
    ctx.fillStyle = CARD.ink2;
    ctx.fillText("You", kx + 32, ky);
    kx += 32 + ctx.measureText("You").width + 28;
    if (trades) {
      var out = PANIC ? "Sold" : "In cash";
      ctx.fillStyle = CARD.fill;
      ctx.fillRect(kx, ky - 16, 22, 20);
      ctx.fillStyle = CARD.ink2;
      ctx.fillText(out, kx + 32, ky);
      kx += 32 + ctx.measureText(out).width + 28;
    }
    ctx.strokeStyle = CARD.ink3;
    ctx.lineWidth = 1.6;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(kx, ky - 7);
    ctx.lineTo(kx + 22, ky - 7);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillText(PANIC ? "Holding on" : "The Index", kx + 32, ky);
  }

  // Runs of text, each with its colour and weight, wrapped word by word.
  function cardWrap(ctx, runs, x0, y0, maxW, lh, fs, font) {
    var x = x0, y = y0;
    runs.forEach(function (r) {
      r[0].split(/(?= )/).forEach(function (t) {
        ctx.font = (r[2] || 400) + " " + fs + "px " + font;
        var w = ctx.measureText(t).width;
        if (x > x0 && x + w > x0 + maxW) {
          x = x0;
          y += lh;
          t = t.replace(/^ /, "");
          w = ctx.measureText(t).width;
        }
        ctx.fillStyle = r[1];
        ctx.fillText(t, x, y);
        x += w;
      });
    });
  }

  function drawCard(canvas, game, word, pts, share, name) {
    var ctx = canvas.getContext("2d");
    var font = '"Schibsted Grotesk", "Helvetica Neue", Arial, sans-serif';
    var m = signed(pts, 1, " pts");
    var sub = [["I finished ", CARD.ink2], [m.text, m.cls === "mv--up" ? CARD.up : m.cls === "mv--down" ? CARD.down : CARD.ink, 500],
      [PANIC ? " against holding on through a hidden " + name + " crash." : " against the " + name + (game.trades ? " and beat " + Math.round(share * 100) + "% of random players." : " and never left the market."), CARD.ink2]];
    function paint() {
      ctx.fillStyle = CARD.ground;
      ctx.fillRect(0, 0, 1200, 630);
      var bx = 64;
      if (mark.complete && mark.naturalWidth) {
        ctx.drawImage(mark, 64, 52, 30, 34);
        bx = 104;
      }
      ctx.fillStyle = CARD.ink;
      ctx.font = "650 28px " + font;
      ctx.fillText("Andra Markets", bx, 80);
      var size = 124;
      ctx.font = "560 " + size + "px " + font;
      while (ctx.measureText(word + ".").width > 430 && size > 60) {
        size -= 4;
        ctx.font = "560 " + size + "px " + font;
      }
      ctx.fillText(word + ".", 56, 214);
      cardWrap(ctx, sub, 520, 136, 616, 40, 30, font);
      cardChart(ctx, game, 64, 262, 1072, 254, font);
      cardKey(ctx, 64, 590, font, game.trades);
      ctx.font = "400 20px " + font;
      ctx.fillStyle = CARD.ink2;
      var foot = (PANIC ? "Panic Test" : "Trading Simulator") + ", on Andra Markets";
      ctx.fillText(foot, 1136 - ctx.measureText(foot).width, 590);
    }
    paint();
    mark.addEventListener("load", paint, { once: true });
    if (document.fonts && document.fonts.load) {
      Promise.all([document.fonts.load("560 124px 'Schibsted Grotesk'"), document.fonts.load("400 30px 'Schibsted Grotesk'"), document.fonts.load("650 28px 'Schibsted Grotesk'")]).then(paint, function () {});
    }
  }

  function reset() {
    clearInterval(timer);
    g = null;
    playing = false;
    if (mode === "shared") mode = "random";
    main.querySelector(".sim-final").hidden = true;
    main.querySelector(".sim-play").hidden = false;
    $("row").hidden = true;
    idle();
    intro();
    window.scrollTo(0, 0);
  }

  // ---- Controls -----------------------------------------------------------
  $("start").addEventListener("click", begin);
  $("go").addEventListener("click", toggle);
  $("speed").addEventListener("click", function () {
    setSpeed(SPEEDS[(SPEEDS.indexOf(speed) + 1) % SPEEDS.length]);
  });
  $("pause").addEventListener("click", function () {
    if (!g) return;
    if (playing) pause();
    else play();
  });
  function inGame() {
    return !main.querySelector(".sim-play").hidden;
  }
  document.addEventListener("keydown", function (e) {
    if (!inGame() || e.metaKey || e.ctrlKey || e.altKey) return;
    var tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || tag === "summary" || e.target.isContentEditable || document.querySelector(".pal:not([hidden])")) return;
    if (e.key === " " || e.code === "Space") {
      if (!g && /^(button|a)$/i.test(e.target.tagName) && e.target !== $("start")) return;
      e.preventDefault();
      if (!e.repeat) toggle();
    } else if ((e.key === "p" || e.key === "P") && g) {
      (playing ? pause : play)();
    } else if (/^[1-4]$/.test(e.key)) {
      setSpeed(SPEEDS[+e.key - 1]);
    }
  });
  document.addEventListener("keyup", function (e) {
    if ((e.key === " " || e.code === "Space") && inGame() && g && /^(button|a)$/i.test(e.target.tagName)) e.preventDefault();
  });
  document.addEventListener("visibilitychange", function () {
    if (document.hidden && playing) pause();
  });

  if (!PANIC && params.get("g") && markets[market]) mode = "shared";
  idle();
  intro();
  loadMarket(market, function () {
    intro();
  });
})();
