/* Andra Markets: Your fund (simulators/your-fund/), a paper long-short fund the reader runs.
   The fund is a ledger kept in this browser (localStorage, andra-fund) and nowhere else: cash,
   positions at their last marked value, pending orders, every trade and the fund's value on
   each day. On each visit the ledger is rolled forward one day at a time from the daily returns
   baked into assets/lab-risk-<market>.js and the dollar rates in assets/lab-risk-fx.js: every
   position moves by its day's return in US dollars, and an order is filled at the first close
   of its company that comes after it was placed, never at one already known. Layout and colour
   follow DESIGN.md (Your fund). */
(function () {
  "use strict";
  var page = document.querySelector('[data-tool="fund"]');
  var src = document.getElementById("fd-data");
  if (!page || !src) return;
  var P = JSON.parse(src.textContent);
  var KEY = "andra-fund", MINUS = "−", DASH = "—", MIN_TRADE = 1000, MAX_LINES = 40, MIN_DAYS = 20, STALE = 7;
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var by = {};
  P.companies.forEach(function (c) { by[c.s] = c; });
  var data = {}, loading = {}, parsed = {};
  var F = null;               // the fund's ledger
  var stored = true;          // false when this browser will not keep it
  var side = "buy", pick = null, view = null;

  function q(sel) { return page.querySelector(sel); }
  var root = q(".fd"), status = q(".fd-status"), foot = q(".fd-foot"), plot = q(".fd-plot"), readout = q(".fd-read");
  var find = document.getElementById("fd-find"), opts = document.getElementById("fd-opts");
  var amtIn = document.getElementById("fd-amt"), pctIn = document.getElementById("fd-pct"), fileIn = q(".fd-file");

  function esc(t) {
    return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function num(v, dec) {
    var s = v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec });
    if (/^-[0.,]+$/.test(s)) s = s.slice(1);
    return s.replace("-", MINUS);
  }
  function money(v, sign) {
    var r = Math.round(v);
    return (r < 0 ? MINUS : sign && r > 0 ? "+" : "") + "$" + Math.abs(r).toLocaleString("en-US");
  }
  function pct(v, dec, sign) {
    var r = Number((v * 100).toFixed(dec));
    return (r > 0 && sign ? "+" : r < 0 ? MINUS : "") + num(Math.abs(r), dec) + "%";
  }
  // A rise or a fall in green or red, its sign kept (The Rise and Fall Rule).
  function mv(text) {
    var c = text.charAt(0) === "+" ? "mv mv--up" : text.charAt(0) === MINUS ? "mv mv--down" : "";
    return c ? '<span class="' + c + '">' + text + "</span>" : text;
  }
  function parse(iso) {
    var p = iso.split("-");
    return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2]));
  }
  // The weekday axis starts on a Monday.
  function axisIso(i) {
    var d = parse(data.us.start);
    d.setUTCDate(d.getUTCDate() + Math.floor(i / 5) * 7 + i % 5);
    return d.toISOString().slice(0, 10);
  }
  // The axis index of a date; a weekend counts as the Friday before, a date before the axis as -1.
  function axisIndex(iso) {
    var days = Math.round((parse(iso) - parse(data.us.start)) / 864e5);
    if (days < 0) return -1;
    return Math.floor(days / 7) * 5 + Math.min(days % 7, 4);
  }
  function dayLabel(iso) {
    var d = parse(iso);
    return d.getUTCDate() + " " + MONTHS[d.getUTCMonth()] + " " + d.getUTCFullYear();
  }
  function mean(a) { var t = 0; for (var i = 0; i < a.length; i++) t += a[i]; return t / a.length; }
  function cov(a, b) {
    var ma = mean(a), mb = mean(b), t = 0;
    for (var i = 0; i < a.length; i++) t += (a[i] - ma) * (b[i] - mb);
    return t / (a.length - 1);
  }
  function say(text, where) {
    var el = where || status;
    el.textContent = "";
    window.setTimeout(function () { el.textContent = text; }, 30);
  }

  /* The returns ------------------------------------------------------------- */

  function load(key, done) {
    if (data[key]) { done(); return; }
    if (loading[key]) { loading[key].push(done); return; }
    loading[key] = [done];
    var sc = document.createElement("script");
    sc.src = (document.body.getAttribute("data-base") || "") + "assets/" + P.files[key];
    sc.onload = function () {
      data[key] = (window.ANDRA_RISK || {})[key];
      var waiting = loading[key];
      loading[key] = null;
      if (!data[key]) { say("The prices did not load. Reload the page to try again."); return; }
      waiting.forEach(function (f) { f(); });
    };
    sc.onerror = function () {
      loading[key] = null;
      say("The prices did not load. Check your connection and try again.");
    };
    document.head.appendChild(sc);
  }
  // A series' daily log returns in basis points on the weekday axis; NaN where its market was shut.
  function series(key, sym) {
    var k = key + ":" + sym;
    if (!parsed[k]) {
      parsed[k] = ((data[key] && data[key].series[sym]) || "").split(",").map(function (x) { return x === "" ? NaN : +x; });
    }
    return parsed[k];
  }
  function lastIdx(a) {
    var i = a.length - 1;
    while (i >= 0 && isNaN(a[i])) i--;
    return i;
  }
  function own(c) { return series(c.m, c.s); }
  // A company's return on day k in US dollars: its own, less the move in its currency's units per dollar.
  function usd(c, k) {
    var r = own(c)[k], f = c.u === "USD" ? 0 : series("fx", c.u)[k];
    return (isNaN(r) ? 0 : r) - (isNaN(f) || f == null ? 0 : f);
  }
  function need() {
    var keys = { us: 1 };
    (F ? F.lots.concat(F.orders) : []).forEach(function (x) {
      var c = by[x.s];
      if (!c) return;
      keys[c.m] = 1;
      if (c.u !== "USD") keys.fx = 1;
    });
    if (pick) { keys[pick.m] = 1; if (pick.u !== "USD") keys.fx = 1; }
    return Object.keys(keys).filter(function (k) { return P.files[k] && !data[k]; });
  }
  function ready(done) {
    var missing = need();
    if (!missing.length) { done(); return; }
    var left = missing.length;
    missing.forEach(function (k) { load(k, function () { if (--left === 0) done(); }); });
  }

  /* The ledger -------------------------------------------------------------- */

  function read() {
    try {
      var f = JSON.parse(localStorage.getItem(KEY) || "null");
      return tidy(f);
    } catch (e) { return null; }
  }
  function write() {
    try { localStorage.setItem(KEY, JSON.stringify(F)); stored = true; } catch (e) { stored = false; }
  }
  // A ledger read from storage or a file, or null when it is not one.
  function tidy(f) {
    if (!f || f.v !== 1 || typeof f.cash !== "number" || !isFinite(f.cash) || !/^\d{4}-\d\d-\d\d$/.test(f.d || "") ||
        !Array.isArray(f.lots) || !Array.isArray(f.navs) || !f.navs.length) return null;
    var iso = /^\d{4}-\d\d-\d\d$/;
    f.name = String(f.name || "Your fund").slice(0, 40);
    f.started = iso.test(f.started || "") ? f.started : f.navs[0][0];
    f.lots = f.lots.filter(function (l) { return l && typeof l.s === "string" && isFinite(l.v) && isFinite(l.cost) && l.v; })
      .map(function (l) { return { s: l.s.slice(0, 20), v: +l.v, cost: +l.cost, opened: iso.test(l.opened || "") ? l.opened : f.d, n: l.n ? String(l.n).slice(0, 80) : "" }; });
    f.orders = (Array.isArray(f.orders) ? f.orders : []).filter(function (o) {
      return o && typeof o.s === "string" && /^(buy|short|close)$/.test(o.side) && iso.test(o.after || "") && (o.side === "close" || (isFinite(o.amt) && o.amt > 0));
    }).map(function (o) { return { s: o.s.slice(0, 20), side: o.side, amt: +o.amt || 0, after: o.after }; });
    f.navs = f.navs.filter(function (r) { return Array.isArray(r) && iso.test(r[0]) && isFinite(r[1]); })
      .map(function (r) { return [r[0], +r[1], isFinite(r[2]) ? +r[2] : 100, isFinite(r[3]) ? +r[3] : 100]; });
    f.log = (Array.isArray(f.log) ? f.log : []).filter(function (t) { return t && iso.test(t.d || "") && typeof t.s === "string"; })
      .map(function (t) { return { d: t.d, kind: String(t.kind || "").slice(0, 20), s: t.s.slice(0, 20), n: String(t.n || t.s).slice(0, 80), amt: +t.amt || 0, res: isFinite(t.res) && t.res != null ? +t.res : null }; });
    f.gain = { l: +(f.gain && f.gain.l) || 0, s: +(f.gain && f.gain.s) || 0 };
    return f.navs.length ? f : null;
  }
  function value() {
    return F.lots.reduce(function (t, l) { return t + l.v; }, F.cash);
  }
  function lot(sym) { return F.lots.filter(function (l) { return l.s === sym; })[0]; }
  function nameOf(sym) { var c = by[sym], l = F && lot(sym); return c ? c.n : l && l.n ? l.n : sym; }

  // Roll the ledger forward to the last day every series it needs has closed.
  function roll() {
    var bench = series("us", P.bench), world = P.world ? series("us", P.world) : null;
    var end = lastIdx(bench);
    var used = {};
    F.lots.concat(F.orders).forEach(function (x) { if (by[x.s]) used[x.s] = by[x.s]; });
    Object.keys(used).forEach(function (s) {
      var c = used[s], li = lastIdx(own(c));
      // A company whose prices stopped some days ago is left where it is: it must not hold the fund back.
      if (lastIdx(bench) - li <= STALE) end = Math.min(end, li);
      if (c.u !== "USD") { var fi = lastIdx(series("fx", c.u)); if (lastIdx(bench) - fi <= STALE) end = Math.min(end, fi); }
    });
    var from = axisIndex(F.d), changed = false;
    var last = F.navs[F.navs.length - 1], sp = last[2], wd = last[3];
    for (var k = Math.max(from + 1, 0); k <= end; k++) {
      var iso = axisIso(k);
      F.lots.forEach(function (l) { var c = by[l.s]; if (c) l.v *= Math.exp(usd(c, k) / 1e4); });
      fill(k, iso);
      if (!isNaN(bench[k])) sp *= Math.exp(bench[k] / 1e4);
      if (world && !isNaN(world[k])) wd *= Math.exp(world[k] / 1e4);
      F.navs.push([iso, Math.round(value() * 100) / 100, Math.round(sp * 1e4) / 1e4, Math.round(wd * 1e4) / 1e4]);
      F.d = iso;
      changed = true;
    }
    // An order for a company that has left the list can never be filled.
    var gone = F.orders.filter(function (o) { return !by[o.s] && o.side !== "close"; });
    if (gone.length) { F.orders = F.orders.filter(function (o) { return by[o.s] || o.side === "close"; }); changed = true; }
    if (changed) write();
  }
  // Orders whose company closed on day k, after they were placed, are filled at that close.
  function fill(k, iso) {
    F.orders = F.orders.filter(function (o) {
      var c = by[o.s];
      if (!c || iso <= o.after || isNaN(own(c)[k])) return true;
      var l = lot(o.s);
      if (o.side === "close") {
        if (l) close(l, iso);
        return false;
      }
      var sign = o.side === "buy" ? 1 : -1;
      if (l && l.v * sign < 0) return false;  // the other side was opened meanwhile: the order lapses
      if (l) { l.v += sign * o.amt; l.cost += sign * o.amt; }
      else F.lots.push({ s: o.s, v: sign * o.amt, cost: sign * o.amt, opened: iso, n: c.n });
      F.cash -= sign * o.amt;
      F.log.push({ d: iso, kind: o.side === "buy" ? "Buy" : "Short", s: o.s, n: c.n, amt: o.amt, res: null });
      return false;
    });
  }
  function close(l, iso) {
    var res = l.v - l.cost;
    F.cash += l.v;
    F.gain[l.v > 0 ? "l" : "s"] += res;
    F.log.push({ d: iso, kind: l.v > 0 ? "Sell" : "Close short", s: l.s, n: nameOf(l.s), amt: Math.abs(l.v), res: res });
    F.lots = F.lots.filter(function (x) { return x !== l; });
  }

  /* The record -------------------------------------------------------------- */

  function render() {
    var has = !!F;
    q(".fd-new").hidden = has;
    q(".fd-run").hidden = !has;
    if (!has) return;
    var V = value(), start = F.navs[0][1], n = F.navs.length - 1, last = F.navs[n];
    q(".fd-name b").textContent = F.name;
    q(".fd-name span").textContent = "Started " + dayLabel(F.started) + " with " + money(start) + " of paper money";
    q(".fd-period").textContent = n ? "The record, " + dayLabel(F.navs[0][0]) + " to " + dayLabel(last[0]) : "The record starts at the next close";

    var rf = [], rb = [], peak = start, dd = 0;
    for (var i = 1; i <= n; i++) {
      rf.push(F.navs[i][1] / F.navs[i - 1][1] - 1);
      rb.push(F.navs[i][2] / F.navs[i - 1][2] - 1);
    }
    F.navs.forEach(function (r) { if (r[1] > peak) peak = r[1]; if (r[1] / peak - 1 < dd) dd = r[1] / peak - 1; });
    var enough = n >= MIN_DAYS, wait = "After " + MIN_DAYS + " sessions";
    var vol = enough ? Math.sqrt(cov(rf, rf) * 252) : 0, vb = enough ? cov(rb, rb) : 0;
    function kpi(name, v, sub) { return "<li><span>" + name + "</span><b>" + v + "</b><i>" + sub + "</i></li>"; }
    q(".fd-kpis").innerHTML =
      kpi("Value", money(V), n ? money(V - start, true) + " since the start" : "At the start") +
      kpi("Return", n ? mv(pct(V / start - 1, 1, true)) : DASH, n ? "S&amp;P 500 " + pct(last[2] / 100 - 1, 1, true) + (P.world ? ", MSCI World " + pct(last[3] / 100 - 1, 1, true) : "") : "From the next close") +
      kpi("Sharpe ratio", enough && vol ? num(mean(rf) * 252 / vol, 2) : DASH, enough ? "Return for each unit of risk" : wait) +
      kpi("Volatility", enough ? pct(vol, 1) : DASH, enough ? "A year" : wait) +
      kpi("Deepest fall", n ? mv(pct(dd, 1)) : DASH, "From a high to a low") +
      kpi("Beta", enough && vb ? num(cov(rf, rb) / vb, 2) : DASH, enough ? "To the S&amp;P 500" : wait);

    // pending orders
    q(".fd-orders").innerHTML = F.orders.length ? '<ul class="fd-pend">' + F.orders.map(function (o, i) {
      var what = o.side === "close" ? "Close " + esc(nameOf(o.s)) : (o.side === "buy" ? "Buy " : "Short ") + esc(nameOf(o.s)) + ", " + money(o.amt);
      return "<li><span><b>" + what + "</b><i>Pending: filled at its next close</i></span>" +
        '<button type="button" class="co-reset" data-cancel="' + i + '">Cancel</button></li>';
    }).join("") + "</ul>" : "";

    // the book: longs, then shorts, then cash
    var longV = 0, shortV = 0, open = { l: 0, s: 0 }, gains = [], body = "";
    [[1, "Long"], [-1, "Short"]].forEach(function (g) {
      var rows = F.lots.filter(function (l) { return l.v * g[0] > 0; }).sort(function (a, b) { return Math.abs(b.v) - Math.abs(a.v); });
      if (!rows.length) return;
      body += '<tr class="fd-grp"><th scope="rowgroup" colspan="7">' + g[1] + "</th></tr>";
      rows.forEach(function (l) {
        var gain = l.v - l.cost, c = by[l.s], closing = F.orders.some(function (o) { return o.s === l.s && o.side === "close"; });
        if (g[0] > 0) { longV += l.v; open.l += gain; } else { shortV += -l.v; open.s += gain; }
        gains.push([l.s, gain]);
        body += '<tr><th scope="row">' + esc(nameOf(l.s)) + "<span>" + esc(l.s) + (c ? "" : " · no longer followed") + '</span></th><td class="fd-wide">' + dayLabel(l.opened) +
          "</td><td>" + money(Math.abs(l.v)) + '</td><td class="fd-wide">' + pct(Math.abs(l.v) / V, 1) + "</td><td>" + mv(money(gain, true)) + '</td><td class="fd-pc">' + mv(pct(gain / Math.abs(l.cost), 1, true)) +
          '</td><td class="fd-x">' + (closing ? '<span class="fd-closing">Closing</span>' : '<button type="button" class="co-reset" data-close="' + esc(l.s) + '" aria-label="Close ' + esc(nameOf(l.s)) + '">Close</button>') + "</td></tr>";
      });
    });
    if (!F.lots.length) body += '<tr class="fd-none"><td colspan="7">No positions yet. The fund is all cash.</td></tr>';
    body += '<tr class="fd-tot"><th scope="row">Cash</th><td class="fd-wide"></td><td>' + money(F.cash) + '</td><td class="fd-wide">' + pct(F.cash / V, 1) + "</td><td></td><td></td><td></td></tr>";
    q(".fd-book tbody").innerHTML = body;

    // exposure
    var L = longV / V, S = shortV / V;
    function cell(name, v, sub) { return "<li><span>" + name + "</span><b>" + v + "</b>" + (sub ? "<i>" + sub + "</i>" : "") + "</li>"; }
    q(".fd-expo").innerHTML = cell("Long", pct(L, 0)) + cell("Short", pct(S, 0)) + cell("Net", pct(L - S, 0, true)) + cell("Gross", pct(L + S, 0));
    var gs = q(".fd-gauge__s"), gl = q(".fd-gauge__l");
    gs.style.left = (Math.max(0, 1 - S) / 3 * 100).toFixed(1) + "%";
    gs.style.width = (Math.min(1, S) / 3 * 100).toFixed(1) + "%";
    gl.style.width = (Math.min(2, L) / 3 * 100).toFixed(1) + "%";

    // where the result came from
    var lg = open.l + F.gain.l, sg = open.s + F.gain.s;
    var nl = F.lots.filter(function (l) { return l.v > 0; }).length, ns = F.lots.length - nl;
    gains.sort(function (a, b) { return b[1] - a[1]; });
    q(".fd-attr").innerHTML = cell("Longs", mv(money(lg, true)), nl + " open") + cell("Shorts", mv(money(sg, true)), ns + " open") +
      cell("Best position", gains.length ? mv(money(gains[0][1], true)) : DASH, gains.length ? esc(nameOf(gains[0][0])) : "None open") +
      cell("Worst position", gains.length > 1 ? mv(money(gains[gains.length - 1][1], true)) : DASH, gains.length > 1 ? esc(nameOf(gains[gains.length - 1][0])) : "With two or more open");

    // the log, newest first
    q(".fd-log tbody").innerHTML = F.log.length ? F.log.slice().reverse().map(function (t) {
      return "<tr><td>" + dayLabel(t.d) + "</td><td>" + esc(t.kind) + " " + esc(t.n) + "</td><td>" + money(t.amt) + "</td><td>" + (t.res != null ? mv(money(t.res, true)) : "") + "</td></tr>";
    }).join("") : '<tr class="fd-none"><td colspan="4">No trades yet.</td></tr>';

    q(".fd-key-w").hidden = !P.world;
    view = { at: -1 };
    chart();
    fan(V);
    estimate();
  }

  /* Where it could go: the book as it stands, on each of the past year's days (assets/lens.js) */

  function fan(V) {
    var band = q(".fd-fan"), Lens = window.AndraLens;
    var lots = F.lots.filter(function (l) { return by[l.s]; });
    var end = axisIndex(F.d), from = Math.max(1, end - 251), ret = [];
    if (Lens && lots.length && data.us) {
      for (var k = from; k <= end; k++) {
        var r = 0;
        for (var i = 0; i < lots.length; i++) r += lots[i].v / V * (Math.exp(usd(by[lots[i].s], k) / 1e4) - 1);
        ret.push(r);
      }
    }
    band.hidden = ret.length < 120;
    if (band.hidden) return;
    var cv = q(".fd-fan-cv"), f = Lens.weave(cv, { returns: ret, steps: 252, block: 5, ticks: ["Today", "3 months", "6 months", "9 months", "1 year"] });
    q(".fd-fan-stats").textContent = num(f.paths, 0) + " strands \u00b7 252 sessions \u00b7 blocks of 5 \u00b7 from " + ret.length + " past days";
    q(".fd-fan-read").innerHTML = "Middle " + mv(pct(f.p50, 0, true)) + " \u00b7 1 in 20 above " + mv(pct(f.p95, 0, true)) + " \u00b7 1 in 20 below " + mv(pct(f.p5, 0, true)) +
      " \u00b7 ends lower in <b>" + pct(f.lower, 0) + "</b> of them";
    cv.setAttribute("aria-label", "A fan of " + f.paths + " possible one-year paths of the fund as it is positioned now, each starting at 100. The middle path ends " + pct(f.p50, 0, true) +
      "; one in twenty ends above " + pct(f.p95, 0, true) + " and one in twenty below " + pct(f.p5, 0, true) + ". " + pct(f.lower, 0) + " of them end lower than they began.");
  }

  /* The chart: the fund, the S&P 500 and the MSCI World, each from 100 -------- */

  function chart() {
    if (!F || !view) return;
    var W = plot.clientWidth;
    if (!W) return;
    var n = F.navs.length - 1;
    if (n < 1) {
      plot.innerHTML = '<p class="fd-wait">The line starts at the next close.</p>';
      readout.textContent = "";
      return;
    }
    var base = F.navs[0][1];
    var f = F.navs.map(function (r) { return r[1] / base * 100; }), b = F.navs.map(function (r) { return r[2]; }), w = P.world ? F.navs.map(function (r) { return r[3]; }) : null;
    var H = W < 600 ? 220 : 300, L = 40, R = 6, T = 8, B = 24;
    var all = f.concat(b, w || []), lo = Math.min.apply(null, all), hi = Math.max.apply(null, all);
    var step = [1, 2, 5, 10, 20, 25, 50, 100, 200, 500].filter(function (s) { return (hi - lo) / s <= 5; })[0] || 1000;
    lo = Math.floor(lo / step) * step; hi = Math.ceil(hi / step) * step;
    if (hi === lo) hi = lo + step;
    var X = function (i) { return L + i / n * (W - L - R); }, Y = function (v) { return T + (hi - v) / (hi - lo) * (H - T - B); };
    var line = function (a) { return a.map(function (v, i) { return (i ? "L" : "M") + X(i).toFixed(1) + " " + Y(v).toFixed(1); }).join(""); };
    var s = '<svg width="' + W + '" height="' + H + '" viewBox="0 0 ' + W + " " + H + '" aria-hidden="true">';
    for (var v = lo; v <= hi + 1e-9; v += step) {
      s += '<line class="g" x1="' + L + '" x2="' + (W - R) + '" y1="' + Y(v).toFixed(1) + '" y2="' + Y(v).toFixed(1) + '"/><text class="t" x="' + (L - 8) + '" y="' + (Y(v) + 4).toFixed(1) + '" text-anchor="end">' + v + "</text>";
    }
    // a label where a month begins (a year when the record is long), never closer than 56px
    var seen = "", lastX = -1e9, long = n > 400;
    F.navs.forEach(function (r, i) {
      var key = long ? r[0].slice(0, 4) : r[0].slice(0, 7);
      if (i && key !== seen && X(i) - lastX > 56 && X(i) < W - R - 20) {
        s += '<text class="t" x="' + X(i).toFixed(1) + '" y="' + (H - 6) + '" text-anchor="middle">' + (long ? key : MONTHS[+r[0].slice(5, 7) - 1]) + "</text>";
        lastX = X(i);
      }
      seen = key;
    });
    if (w) s += '<path class="w" d="' + line(w) + '"/>';
    s += '<path class="b" d="' + line(b) + '"/><path class="p" d="' + line(f) + '"/>';
    var days = {};
    F.navs.forEach(function (r, i) { days[r[0]] = i; });
    var rings = {};
    F.log.forEach(function (t) { if (days[t.d] != null) rings[days[t.d]] = 1; });
    Object.keys(rings).forEach(function (i) { s += '<circle class="r" cx="' + X(+i).toFixed(1) + '" cy="' + Y(f[+i]).toFixed(1) + '" r="3"/>'; });
    var at = view.at >= 0 ? view.at : n;
    if (view.at >= 0) s += '<line class="h" x1="' + X(at).toFixed(1) + '" x2="' + X(at).toFixed(1) + '" y1="' + T + '" y2="' + (H - B) + '"/>';
    s += '<circle class="d" cx="' + X(at).toFixed(1) + '" cy="' + Y(f[at]).toFixed(1) + '" r="2.5"/></svg>';
    plot.innerHTML = s;
    view.x0 = L; view.x1 = W - R;
    readout.textContent = dayLabel(F.navs[at][0]) + ": your fund " + num(f[at], 1) + ", S&P 500 " + num(b[at], 1) + (w ? ", MSCI World " + num(w[at], 1) : "") + ".";
    plot.setAttribute("aria-label", "Value of the fund from " + dayLabel(F.navs[0][0]) + " to " + dayLabel(F.navs[n][0]) + ", each starting at 100: your fund ends at " +
      num(f[n], 1) + ", the S&P 500 at " + num(b[n], 1) + (w ? ", the MSCI World at " + num(w[n], 1) : "") + ". Use the arrow keys to read each day.");
  }
  plot.addEventListener("pointermove", function (e) {
    if (!F || !view || F.navs.length < 2) return;
    var r = plot.getBoundingClientRect(), n = F.navs.length - 1;
    var i = Math.max(0, Math.min(n, Math.round((e.clientX - r.left - view.x0) / (view.x1 - view.x0) * n)));
    if (i !== view.at) { view.at = i; chart(); }
  });
  plot.addEventListener("pointerleave", function () { if (view && view.at >= 0) { view.at = -1; chart(); } });
  plot.addEventListener("keydown", function (e) {
    if (!F || !view || F.navs.length < 2) return;
    var n = F.navs.length - 1, i = view.at < 0 ? n : view.at;
    if (e.key === "ArrowLeft") i--; else if (e.key === "ArrowRight") i++; else if (e.key === "Home") i = 0; else if (e.key === "End") i = n; else return;
    e.preventDefault();
    view.at = Math.max(0, Math.min(n, i));
    chart();
  });

  /* A new trade ------------------------------------------------------------- */

  function gross(extra) {
    var t = F.lots.reduce(function (a, l) { return a + Math.abs(l.v); }, 0);
    F.orders.forEach(function (o) { if (o.side !== "close") t += o.amt; });
    return (t + (extra || 0)) / value();
  }
  function amount() { var v = parseFloat(amtIn.value); return isFinite(v) && v > 0 ? v : 0; }
  function estimate() {
    var a = amount(), el = q(".fd-est");
    if (!F) return;
    el.textContent = a ? "About " + pct(a / value(), 1) + " of the fund. Gross exposure would go from " + pct(gross(), 0) + " to " + pct(gross(a), 0) + "." :
      "Gross exposure is " + pct(gross(), 0) + " of the fund; a trade may take it to " + pct(P.gross, 0) + ".";
  }
  amtIn.addEventListener("input", function () { var a = amount(); pctIn.value = a ? Math.round(a / value() * 1000) / 10 : ""; estimate(); });
  pctIn.addEventListener("input", function () {
    var p = parseFloat(pctIn.value);
    amtIn.value = isFinite(p) && p > 0 ? Math.round(p / 100 * value() / 100) * 100 : "";
    estimate();
  });
  function place() {
    if (!pick) { say("Choose a company first."); find.focus(); return; }
    var a = Math.round(amount());
    if (a < MIN_TRADE) { say("The smallest trade is " + money(MIN_TRADE) + "."); amtIn.focus(); return; }
    var l = lot(pick.s), sign = side === "buy" ? 1 : -1;
    if (l && l.v * sign < 0) { say("The fund is " + (l.v > 0 ? "long" : "short") + " " + pick.n + ". Close that position first."); return; }
    if (F.orders.some(function (o) { return o.s === pick.s; })) { say("There is already an order waiting for " + pick.n + ". Cancel it to place another."); return; }
    if (F.lots.length + F.orders.length >= MAX_LINES) { say("Up to " + MAX_LINES + " positions and orders. Close one to add another."); return; }
    if (gross(a) > P.gross + 1e-9) { say("That would take gross exposure to " + pct(gross(a), 0) + ". The limit is " + pct(P.gross, 0) + " of the fund."); return; }
    var c = pick;
    ready(function () {
      var li = lastIdx(own(c));
      // The order waits for the first close of the company after the last one known now.
      F.orders.push({ s: c.s, side: side, amt: a, after: li >= 0 ? axisIso(li) : F.d });
      write();
      pick = null; find.value = ""; amtIn.value = ""; pctIn.value = "";
      render();
      say((side === "buy" ? "Buy " : "Short ") + c.n + ", " + money(a) + ": placed. It is filled at " + c.n + "'s next close." + (stored ? "" : " This browser is not saving the fund."));
    });
  }
  q(".fd-place").addEventListener("click", place);

  var active = -1, matches = [];
  function closeOpts() {
    opts.hidden = true;
    find.setAttribute("aria-expanded", "false");
    find.removeAttribute("aria-activedescendant");
    active = -1;
  }
  function renderOpts() {
    var term = find.value.trim().toLowerCase();
    if (!term) { closeOpts(); return; }
    matches = P.companies.filter(function (c) { return c.n.toLowerCase().indexOf(term) >= 0 || c.s.toLowerCase().indexOf(term) === 0; }).slice(0, 8);
    opts.innerHTML = matches.length ? matches.map(function (c, i) {
      return '<li role="option" id="fd-opt-' + i + '" aria-selected="' + (i === active) + '" data-s="' + esc(c.s) + '">' +
        '<span class="lt-opts__name">' + esc(c.n) + '</span><span class="lt-opts__meta">' + esc(c.s) + ", " + esc(c.c) + "</span></li>";
    }).join("") : '<li class="lt-opts__none">No company the site follows matches.</li>';
    opts.hidden = false;
    find.setAttribute("aria-expanded", "true");
    if (active >= 0) find.setAttribute("aria-activedescendant", "fd-opt-" + active);
  }
  function choose(sym) {
    pick = by[sym];
    find.value = pick.n;
    closeOpts();
    amtIn.focus();
  }
  find.addEventListener("input", function () { pick = null; active = -1; renderOpts(); });
  find.addEventListener("keydown", function (e) {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (!matches.length || opts.hidden) return;
      e.preventDefault();
      active = (active + (e.key === "ArrowDown" ? 1 : -1) + matches.length) % matches.length;
      renderOpts();
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (matches.length && !opts.hidden) choose(matches[Math.max(active, 0)].s);
    } else if (e.key === "Escape") {
      closeOpts();
    }
  });
  find.addEventListener("blur", function () { window.setTimeout(closeOpts, 150); });
  opts.addEventListener("mousedown", function (e) {
    var li = e.target.closest("[data-s]");
    if (li) { e.preventDefault(); choose(li.getAttribute("data-s")); }
  });

  /* Buttons ----------------------------------------------------------------- */

  var armed = null;  // "Start a new fund" asks twice
  page.addEventListener("click", function (e) {
    var chip = e.target.closest(".lt-chips .chip"), cancel = e.target.closest("[data-cancel]"), cl = e.target.closest("[data-close]"), act = e.target.closest("[data-fd]");
    if (act && act.getAttribute("data-fd") !== "reset") armed = null;
    if (chip) {
      side = chip.getAttribute("data-value");
      Array.prototype.forEach.call(chip.parentNode.querySelectorAll(".chip"), function (b) { b.setAttribute("aria-pressed", b === chip ? "true" : "false"); });
    } else if (cancel) {
      var o = F.orders[+cancel.getAttribute("data-cancel")];
      F.orders = F.orders.filter(function (x) { return x !== o; });
      write(); render();
      say("Order cancelled.");
    } else if (cl) {
      var sym = cl.getAttribute("data-close"), l = lot(sym), c = by[sym];
      if (!l) return;
      if (!c) {
        // No more prices for it: closed now, at its last value.
        close(l, F.d);
        write(); render();
        say(nameOf(sym) + " is closed at its last value.");
        return;
      }
      F.orders = F.orders.filter(function (x) { return x.s !== sym; });
      ready(function () {
        var li = lastIdx(own(c));
        F.orders.push({ s: sym, side: "close", amt: 0, after: li >= 0 ? axisIso(li) : F.d });
        write(); render();
        say("Close " + c.n + ": placed. It is filled at " + c.n + "'s next close.");
      });
    } else if (act) {
      var what = act.getAttribute("data-fd");
      if (what === "export") exportCopy();
      else if (what === "import") fileIn.click();
      else if (what === "reset") {
        if (armed !== act) {
          armed = act;
          say("This deletes " + F.name + " and its whole record from this browser. Press Start a new fund again to confirm.", foot);
          return;
        }
        armed = null;
        F = null;
        try { localStorage.removeItem(KEY); } catch (err) { /* nothing was stored */ }
        render();
        document.getElementById("fd-name").focus();
      }
    }
  });
  function exportCopy() {
    var name = "andra-markets-fund-" + F.d + ".json";
    var blob = new Blob([JSON.stringify({ fund: "Andra Markets paper fund", exported: F.d, ledger: F }, null, 2)], { type: "application/json" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    a.hidden = true;
    document.body.appendChild(a);
    a.click();
    window.setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    say("A copy of " + F.name + " is saved as " + name + " in your downloads.", foot);
  }
  fileIn.addEventListener("change", function () {
    var file = fileIn.files && fileIn.files[0];
    if (!file) return;
    var r = new FileReader();
    r.onload = function () {
      fileIn.value = "";
      var f = null;
      try { f = tidy((JSON.parse(String(r.result)) || {}).ledger); } catch (e) { f = null; }
      if (!f) { say("That file is not a copy of a fund.", F ? foot : status); return; }
      F = f;
      write();
      ready(function () { roll(); render(); say("Imported " + F.name + "." + (stored ? "" : " This browser is not saving it."), foot); });
    };
    r.onerror = function () { fileIn.value = ""; say("That file could not be read.", F ? foot : status); };
    r.readAsText(file);
  });
  q(".fd-newform").addEventListener("submit", function (e) {
    e.preventDefault();
    var name = document.getElementById("fd-name").value.trim().slice(0, 40) || "Your fund";
    ready(function () {
      var d = axisIso(lastIdx(series("us", P.bench)));
      F = { v: 1, name: name, started: d, d: d, cash: P.start, lots: [], orders: [], navs: [[d, P.start, 100, 100]], log: [], gain: { l: 0, s: 0 } };
      write();
      render();
      say(name + " has started with " + money(P.start) + "." + (stored ? "" : " This browser is not saving it: it will be gone when you leave the page."));
      find.focus();
    });
  });

  var lastW = 0;
  window.addEventListener("resize", function () {
    if (plot.clientWidth !== lastW) { lastW = plot.clientWidth; chart(); }
  });

  root.hidden = false;
  F = read();
  if (F) ready(function () { roll(); render(); });
  else render();
})();
