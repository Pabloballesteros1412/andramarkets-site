/* Crypto: Bitcoin (owner-approved sketch, 27 Nov 2026; in dollars by default, after the owner's note that a ratio
   scale hid its course). Three charts in the dashboard style, from the JSON in the page: the price every day since
   July 2010 with the four halvings, how far below its record it stood each day, and the four cycles from each
   halving as multiples of the price that day. The range (1M to Max) and the scale (dollars or log) apply to the
   first two. Pointing at a chart, or the arrow keys on it, reads out that day under it; otherwise the line reads
   the latest. Red marks only a fall, with its sign. Without this script the page keeps its table and Latest panel. */
(function () {
  "use strict";
  var src = document.getElementById("btc-data"); if (!src) return;
  var D; try { D = JSON.parse(src.textContent); } catch (e) { return; }
  var MIN = "−", MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], DAY = 864e5;
  var t0 = Date.parse(D.start), P = D.p.slice(), N;
  // today's price from CoinGecko, when it is a day past the last close
  var nowT = Date.parse(D.now[0]), lastT = t0 + (P.length - 1) * DAY;
  if (nowT > lastT) { for (var g = lastT + DAY; g < nowT; g += DAY) P.push(P[P.length - 1]); P.push(D.now[1]); }
  N = P.length;
  function T(i) { return t0 + i * DAY; }
  function day(i) { var d = new Date(T(i)); return d.getUTCDate() + " " + MON[d.getUTCMonth()] + " " + d.getUTCFullYear(); }
  function axis(v) { return v === 0 ? "$0" : v >= 1000 ? "$" + (v / 1000).toLocaleString("en-US", { maximumFractionDigits: 1 }) + "k" : money(v); }
  function money(v) { return v >= 1e5 ? "$" + Math.round(v / 1000) + "k" : v >= 1000 ? "$" + Math.round(v).toLocaleString("en-US") : v >= 1 ? "$" + v.toFixed(2) : "$" + v.toFixed(v >= 0.1 ? 2 : 3); }
  function moneyFull(v) { return v >= 1000 ? "$" + Math.round(v).toLocaleString("en-US") : money(v); }
  function idxOf(iso) { return Math.max(0, Math.min(N - 1, Math.round((Date.parse(iso) - t0) / DAY))); }
  var HV = D.halvings.map(idxOf);
  // the running record and the falls
  var REC = [], DD = [], pk = 0, falls = [], tr = 0, inF = false;
  for (var i = 0; i < N; i++) {
    if (P[i] >= P[pk]) { if (inF && P[tr] / P[pk] - 1 < -0.7) falls.push({ p: pk, t: tr, f: P[tr] / P[pk] - 1 }); inF = false; pk = i; tr = i; }
    else { inF = true; if (P[i] < P[tr]) tr = i; }
    REC.push(pk); DD.push((P[i] / P[pk] - 1) * 100);
  }
  if (inF && P[tr] / P[pk] - 1 < -0.3) falls.push({ p: pk, t: tr, f: P[tr] / P[pk] - 1, open: true });
  // the records that came before each great fall, for a label on the price chart
  var peaks = falls.map(function (f) { return f.p; });
  var state = { range: "Max", scale: "lin" }, RANGES = { "1M": 30, "3M": 91, "1Y": 365, "4Y": 1461, "Max": N };
  var charts = [].slice.call(document.querySelectorAll(".btc__plot")).map(function (el) {
    var cv = document.createElement("canvas"); cv.tabIndex = 0; cv.setAttribute("role", "img"); el.appendChild(cv);
    var read = el.parentNode.querySelector(".btc__read");
    return { el: el, cv: cv, read: read, kind: el.getAttribute("data-chart"), at: null };
  });
  var LABEL = {
    price: "Bitcoin's closing price every day since July 2010, with the four halvings. The great falls are listed in the table below.",
    dd: "How far below its record close Bitcoin stood each day since 2010.",
    cycles: "Bitcoin's price over the four years after each of its four halvings, as a multiple of its price on the halving day."
  };
  charts.forEach(function (ch) { ch.cv.setAttribute("aria-label", LABEL[ch.kind]); });

  function niceStep(span, n) { var raw = span / n, p = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / p; return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * p; }
  function setup(ch, h) {
    var dpr = Math.min(window.devicePixelRatio || 1, 2), w = ch.el.clientWidth; ch.cv.style.width = "100%"; ch.cv.style.height = h + "px";
    ch.cv.width = Math.round(w * dpr); ch.cv.height = Math.round(h * dpr); var c = ch.cv.getContext("2d"); c.setTransform(dpr, 0, 0, dpr, 0, 0);
    c.font = "400 12px Inter, 'Helvetica Neue', Arial, sans-serif"; c.textBaseline = "middle"; return { c: c, w: w, h: h, narrow: w < 560 };
  }
  function yearTicks(i0, i1, narrow) {
    var y0 = new Date(T(i0)).getUTCFullYear(), y1 = new Date(T(i1)).getUTCFullYear(), span = y1 - y0, step = span > 10 ? (narrow ? 4 : 2) : span > 4 ? (narrow ? 2 : 1) : 1, out = [];
    if (i1 - i0 < 800) { var d = new Date(T(i0)); d.setUTCDate(1); var stepM = (i1 - i0) > 400 ? (narrow ? 6 : 3) : (i1 - i0) > 200 ? (narrow ? 3 : 2) : 1; for (var k = 0; k < 30; k++) { d.setUTCMonth(d.getUTCMonth() + (k ? stepM : 1)); var ii = Math.round((d.getTime() - t0) / DAY); if (ii > i1) break; if (ii >= i0) out.push([ii, MON[d.getUTCMonth()] + (d.getUTCMonth() === 0 ? " " + d.getUTCFullYear() : "")]); } return out; }
    for (var y = y0 + 1; y <= y1; y++) if ((y - y0) % step === 0 || y === y1) out.push([Math.round((Date.UTC(y, 0, 1) - t0) / DAY), String(y)]);
    return out;
  }
  function frame(S, L, R, Tp, B) { return { L: L, R: R, T: Tp, B: B }; }

  function drawSeries(ch) {
    var price = ch.kind === "price", S = setup(ch, price ? (window.innerWidth < 700 ? 300 : 420) : (window.innerWidth < 700 ? 240 : 300)), c = S.c;
    var n = RANGES[state.range], i0 = Math.max(0, N - n), i1 = N - 1, log = price && state.scale === "log";
    var L = S.narrow ? 46 : 60, R = S.w - (S.narrow ? 14 : 92), Tp = 14, B = S.h - 30;
    var lo = Infinity, hi = -Infinity; for (var i = i0; i <= i1; i++) { var v = price ? P[i] : DD[i]; if (v < lo) lo = v; if (v > hi) hi = v; }
    var tf = log ? Math.log10 : function (v) { return v; }, y0, y1, ticks = [];
    if (price) {
      if (log) { y0 = Math.floor(Math.log10(lo)); y1 = Math.ceil(Math.log10(hi)); if (y1 - y0 < 2) { y0 = Math.log10(lo) - 0.05; y1 = Math.log10(hi) + 0.05; }
        for (var e = Math.floor(y0); e <= Math.ceil(y1); e++) [1, 2, 5].forEach(function (k) { var v = k * Math.pow(10, e), lv = Math.log10(v); if (lv >= y0 && lv <= y1 && (k === 1 || y1 - y0 < 3)) ticks.push([v, axis(v)]); }); }
      else { var span = hi - (state.range === "Max" || state.range === "4Y" ? 0 : lo), base = state.range === "Max" || state.range === "4Y" ? 0 : lo, st = niceStep(hi - base, S.narrow ? 3 : 5);
        y0 = Math.floor(base / st) * st; y1 = Math.ceil(hi * 1.04 / st) * st; for (var t = y0; t <= y1 + 1e-9; t += st) ticks.push([t, axis(t)]); }
    } else { y0 = Math.max(-100, Math.floor(lo / 25) * 25); y1 = 2; for (var t2 = 0; t2 >= y0; t2 -= 25) ticks.push([t2, t2 ? MIN + Math.abs(t2) + "%" : "0%"]); }
    function X(i) { return L + (i - i0) / Math.max(1, i1 - i0) * (R - L); }
    function Y(v) { return B - (tf(v) - y0) / (y1 - y0) * (B - Tp); }
    ch.X = X; ch.i0 = i0; ch.i1 = i1;
    ticks.forEach(function (tk) { var y = Y(tk[0]); c.strokeStyle = "rgba(255,255,255,.07)"; c.lineWidth = 1; c.beginPath(); c.moveTo(L, y); c.lineTo(R, y); c.stroke(); c.fillStyle = "#a3a8aa"; c.textAlign = "right"; c.fillText(tk[1], L - 8, y); });
    yearTicks(i0, i1, S.narrow).forEach(function (tk) { c.fillStyle = "#a3a8aa"; c.textAlign = "center"; c.fillText(tk[1], X(tk[0]), B + 18); });
    if (!price) { c.setLineDash([3, 4]); c.strokeStyle = "rgba(242,243,243,.35)"; c.beginPath(); c.moveTo(L, Y(0)); c.lineTo(R, Y(0)); c.stroke(); c.setLineDash([]); }
    var taken = [];
    HV.forEach(function (h, k) { if (h < i0 || h > i1) return; var x = X(h); c.setLineDash([3, 4]); c.strokeStyle = "rgba(242,243,243,.3)"; c.beginPath(); c.moveTo(x, Tp); c.lineTo(x, B); c.stroke(); c.setLineDash([]);
      if (price) { var hl = S.narrow ? "H" + (k + 1) : "Halving " + (k + 1); c.fillStyle = "#a3a8aa"; c.textAlign = "left"; c.fillText(hl, x + 5, B - 10); taken.push([x + 3, B - 18, x + 7 + c.measureText(hl).width, B - 2]); } });
    if (!price) { c.fillStyle = "rgba(255,255,255,.07)"; c.beginPath(); c.moveTo(X(i0), Y(0)); for (var q = i0; q <= i1; q++) c.lineTo(X(q), Y(DD[q])); c.lineTo(X(i1), Y(0)); c.closePath(); c.fill(); }
    var step = Math.max(1, Math.floor((i1 - i0) / ((R - L) * 2)));
    c.beginPath(); for (var k2 = i0; k2 <= i1; k2 += step) { var xx = X(k2), yy = Y(price ? P[k2] : DD[k2]); k2 === i0 ? c.moveTo(xx, yy) : c.lineTo(xx, yy); } c.lineTo(X(i1), Y(price ? P[i1] : DD[i1]));
    c.strokeStyle = "#f2f3f3"; c.lineWidth = price ? 1.5 : 1.2; c.stroke();
    // marks: the cycles' peaks on the price; the falls' lows below the record
    function mark(i, v, text, color, below) { if (i < i0 || i > i1) return; var x0 = X(i), y = Y(v), w = c.measureText(text).width, x = Math.min(Math.max(x0, L + w / 2 + 3), S.w - w / 2 - 6), ty = below ? y + 15 : y - 13, bx = [x - w / 2 - 3, ty - 8, x + w / 2 + 3, ty + 8];
      c.fillStyle = "#f2f3f3"; c.beginPath(); c.arc(x0, y, 2.6, 0, 7); c.fill(); if (bx[0] < L - 4 || bx[2] > S.w - 2 || taken.some(function (t) { return !(bx[2] < t[0] || bx[0] > t[2] || bx[3] < t[1] || bx[1] > t[3]); })) return;
      taken.push(bx); c.fillStyle = color; c.textAlign = "center"; c.fillText(text, x, ty); }
    if (price) peaks.forEach(function (m, k) { var d = new Date(T(m)), top = m === REC[N - 1] || P[m] >= P[REC[N - 1]]; if (P[m] < 10 && !log) return;
      mark(m, P[m], (top ? "Record " : "") + money(P[m]) + (S.narrow ? "" : ", " + MON[d.getUTCMonth()] + " " + d.getUTCFullYear()), top ? "#f2f3f3" : "#a3a8aa", false); });
    else falls.forEach(function (f) { mark(f.t, DD[f.t], MIN + Math.abs(f.f * 100).toFixed(0) + "%", "#ff4b52", true); });
    // the day under the pointer
    var at = ch.at != null ? Math.max(i0, Math.min(i1, ch.at)) : null;
    if (at != null) { var ax = X(at), ay = Y(price ? P[at] : DD[at]); c.strokeStyle = "rgba(242,243,243,.4)"; c.beginPath(); c.moveTo(ax, Tp); c.lineTo(ax, B); c.stroke(); c.fillStyle = "#f2f3f3"; c.beginPath(); c.arc(ax, ay, 3.5, 0, 7); c.fill(); }
    var lx = X(i1), ly = Y(price ? P[i1] : DD[i1]); c.fillStyle = "#f2f3f3"; c.beginPath(); c.arc(lx, ly, 3, 0, 7); c.fill();
    if (price && !S.narrow) { c.textAlign = "left"; c.fillText(moneyFull(P[i1]), lx + 8, ly); }
    var k3 = at != null ? at : i1, r = REC[k3], fromRec = (P[k3] / P[r] - 1) * 100;
    if (price) ch.read.innerHTML = (at != null ? day(k3) : "Latest: " + day(k3)) + ", " + moneyFull(P[k3]) + (r === k3 ? " · a record close" : " · its record then " + moneyFull(P[r]) + " on " + day(r) + ', <span class="down">' + MIN + Math.abs(fromRec).toFixed(0) + "%</span> below it");
    else ch.read.innerHTML = (at != null ? day(k3) : "Today") + ": " + (Math.round(fromRec * 10) / 10 < 0 ? '<span class="down">' + MIN + Math.abs(fromRec).toFixed(1) + "%</span> below the record of " + day(r) : "at a record close");
  }

  function drawCycles(ch) {
    var S = setup(ch, window.innerWidth < 700 ? 260 : 360), c = S.c, L = S.narrow ? 40 : 54, R = S.w - (S.narrow ? 14 : 110), Tp = 12, B = S.h - 30, DAYS = 1460;
    var styles = [[1.5, 3], [8, 3, 1.5, 3], [6, 4], []], cys = HV.map(function (h, k) { var pts = []; for (var j = h; j < N && j - h <= DAYS; j++) pts.push(P[j] / P[h]); return { pts: pts, k: k, year: new Date(T(h)).getUTCFullYear() }; });
    var lo = Infinity, hi = -Infinity; cys.forEach(function (cy) { cy.pts.forEach(function (v) { if (v < lo) lo = v; if (v > hi) hi = v; }); });
    var y0 = Math.log10(Math.min(lo, 0.8)), y1 = Math.log10(hi) + 0.05;
    function X(d) { return L + d / DAYS * (R - L); } function Y(v) { return B - (Math.log10(v) - y0) / (y1 - y0) * (B - Tp); }
    [0.5, 1, 2, 5, 10, 20, 50, 100, 200].forEach(function (v) { var lv = Math.log10(v); if (lv < y0 || lv > y1) return; var y = Y(v); c.strokeStyle = "rgba(255,255,255,.07)"; c.beginPath(); c.moveTo(L, y); c.lineTo(R, y); c.stroke(); c.fillStyle = "#a3a8aa"; c.textAlign = "right"; c.fillText("×" + v, L - 8, y); });
    [[0, S.narrow ? "Day 0" : "Halving day"], [365, "1 year"], [730, "2 years"], [1095, "3 years"], [1460, "4 years"]].forEach(function (t) { c.fillStyle = "#a3a8aa"; c.textAlign = t[0] ? "center" : "left"; c.fillText(t[1], X(t[0]), B + 18); });
    c.setLineDash([3, 4]); c.strokeStyle = "rgba(242,243,243,.35)"; c.beginPath(); c.moveTo(L, Y(1)); c.lineTo(R, Y(1)); c.stroke(); c.setLineDash([]);
    var cur = cys[cys.length - 1], at = ch.at != null ? Math.max(0, Math.min(DAYS, ch.at)) : null, taken = [];
    cys.forEach(function (cy) { c.beginPath(); cy.pts.forEach(function (v, d) { d ? c.lineTo(X(d), Y(v)) : c.moveTo(X(d), Y(v)); }); c.setLineDash(styles[cy.k] || []);
      c.strokeStyle = cy === cur ? "#f2f3f3" : "rgba(242,243,243,.72)"; c.lineWidth = cy === cur ? 2 : 1.2; c.stroke(); c.setLineDash([]);
      var lv = cy.pts[cy.pts.length - 1], lx = X(cy.pts.length - 1), ly = Y(lv), text = cy.year + " · ×" + (lv >= 10 ? lv.toFixed(0) : lv.toFixed(lv >= 2 ? 1 : 2));
      if (!S.narrow) { var bx = [lx + 6, ly - 8, lx + 6 + c.measureText(text).width, ly + 8]; while (taken.some(function (t) { return !(bx[2] < t[0] || bx[0] > t[2] || bx[3] < t[1] || bx[1] > t[3]); })) { bx[1] += 14; bx[3] += 14; }
        taken.push(bx); c.fillStyle = cy === cur ? "#f2f3f3" : "#a3a8aa"; c.textAlign = "left"; c.fillText(text, bx[0], (bx[1] + bx[3]) / 2); } });
    if (at != null) { var ax = X(at); c.strokeStyle = "rgba(242,243,243,.4)"; c.beginPath(); c.moveTo(ax, Tp); c.lineTo(ax, B); c.stroke(); }
    var dshow = at != null ? at : cur.pts.length - 1;
    ch.read.innerHTML = (at != null ? "Day " + dshow.toLocaleString("en-US") + " after each halving: " : "Day " + dshow.toLocaleString("en-US") + " of the fourth cycle: ") +
      cys.slice().reverse().filter(function (cy) { return cy.pts[dshow] != null; }).map(function (cy) { return cy.year + " ×" + (cy.pts[dshow] >= 10 ? cy.pts[dshow].toFixed(0) : cy.pts[dshow].toFixed(2)); }).join(" · ");
    ch.X = X; ch.i0 = 0; ch.i1 = DAYS; ch.days = true;
  }
  function draw(ch) { if (!ch.el.clientWidth) return; if (ch.kind === "cycles") drawCycles(ch); else drawSeries(ch); }
  function all() { charts.forEach(draw); }
  charts.forEach(function (ch) {
    function pick(e) { var b = ch.cv.getBoundingClientRect(), x = e.clientX - b.left, best = null; if (!ch.X) return;
      var L = ch.X(ch.i0), R = ch.X(ch.i1), f = Math.max(0, Math.min(1, (x - L) / Math.max(1, R - L))); best = Math.round(ch.i0 + f * (ch.i1 - ch.i0)); if (best !== ch.at) { ch.at = best; draw(ch); } }
    ch.cv.addEventListener("pointermove", pick); ch.cv.addEventListener("pointerdown", pick);
    ch.cv.addEventListener("pointerleave", function () { ch.at = null; draw(ch); });
    ch.cv.addEventListener("blur", function () { ch.at = null; draw(ch); });
    ch.cv.addEventListener("keydown", function (e) { var d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (!d) return; e.preventDefault();
      var span = ch.i1 - ch.i0, stepK = e.shiftKey ? Math.max(1, Math.round(span / 20)) : Math.max(1, Math.round(span / 200)); ch.at = Math.max(ch.i0, Math.min(ch.i1, (ch.at == null ? ch.i1 : ch.at) + d * stepK)); draw(ch); });
  });
  var ctl = document.querySelector(".btc .dd__ctl"); if (ctl) { ctl.hidden = false;
    ctl.addEventListener("click", function (e) { var bt = e.target.closest("button"); if (!bt) return; var r = bt.getAttribute("data-range"), s = bt.getAttribute("data-scale");
      if (r) state.range = r; if (s) state.scale = s;
      [].forEach.call(ctl.querySelectorAll("button"), function (x) { x.setAttribute("aria-pressed", String(x.getAttribute("data-range") === state.range || x.getAttribute("data-scale") === state.scale)); });
      charts.forEach(function (ch) { if (ch.kind !== "cycles") { ch.at = null; draw(ch); } }); }); }
  var once = function () { all(); };
  if (document.fonts && document.fonts.load) document.fonts.load("400 12px Inter").then(once, once); else once();
  if ("ResizeObserver" in window) new ResizeObserver(function () { all(); }).observe(document.querySelector(".btc")); else window.addEventListener("resize", all);
})();
