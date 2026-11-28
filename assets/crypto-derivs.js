/* Crypto: Derivatives (owner-approved sketch, 27 Nov 2026: "the pulse", after two charts of the options by strike
   were turned down). From the JSON in the page (Deribit).
   The pulse, under the page head: DVOL, the yearly swing options price in for the next 30 days, as a line of amber
   light with a soft fall of light under it, drawn from its first day to today in about six seconds; behind it, dim,
   the swing that actually happened. Its highest days, well apart, carry their date and level; today's figure
   stands large at the left with what it means for a day. Once drawn, pointing at it or the arrow keys read out
   any day; Replay draws it again; under reduced motion it is drawn at once.
   Then three plain charts in the dashboard style: the perpetual's funding day by day (with a read-out under the
   pointer), the futures curve and the volatility smile of the largest expiry.
   Amber is the group's light, not a rise; red and green appear only on signed figures. Without this script the
   page keeps its text, tables and Latest panel. */
(function () {
  "use strict";
  var src = document.getElementById("dv-data"); if (!src) return;
  var J; try { J = JSON.parse(src.textContent); } catch (e) { return; }
  var MIN = "−", DAY = 864e5, MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches, dpr = Math.min(window.devicePixelRatio || 1, 2), FONT = " Inter, 'Helvetica Neue', Arial, sans-serif";
  function day(t) { var d = new Date(t); return d.getUTCDate() + " " + MON[d.getUTCMonth()] + " " + d.getUTCFullYear(); }
  function sgn(v, d) { var r = Number(v.toFixed(d == null ? 1 : d)); return (r > 0 ? "+" : r < 0 ? MIN : "") + Math.abs(r).toFixed(d == null ? 1 : d); }
  function canvas(cv, w, h) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); var c = cv.getContext("2d"); c.setTransform(dpr, 0, 0, dpr, 0, 0); c.textBaseline = "middle"; return c; }
  function fonts(fn) { if (document.fonts && document.fonts.load) document.fonts.load("300 12px Inter").then(fn, fn); else fn(); }

  // ---- the pulse -------------------------------------------------------------------------------------------
  var box = document.querySelector(".dvh");
  if (box && J.dvol && J.dvol.length > 30) (function () {
    var cv = box.querySelector(".vr__c"), read = box.querySelector(".vr__read"), fig = box.querySelector(".dvh__fig b"), t0 = Date.parse(J.start), T = J.d.map(function (k) { return t0 + k * DAY; }), V = J.dvol, RV = J.real, N = V.length;
    var f = still ? 1 : 0, raf = 0, at = null, geo = {}, figNow = fig.textContent;
    var hiAll = 0, loAll = 1e9; V.forEach(function (v) { hiAll = Math.max(hiAll, v); loAll = Math.min(loAll, v); }); RV.forEach(function (v) { if (v != null) { hiAll = Math.max(hiAll, v); loAll = Math.min(loAll, v); } });
    var mx = Math.ceil(hiAll / 10) * 10 + 5, mn = Math.max(0, Math.floor(loAll / 10) * 10 - 5);
    // its highest days, a few, well apart
    var peaks = [], gap = Math.round(N / 9); V.map(function (v, i) { return i; }).sort(function (a, b) { return V[b] - V[a]; }).forEach(function (i) { if (peaks.length < 4 && peaks.every(function (u) { return Math.abs(u - i) > gap; })) peaks.push(i); });
    function draw() {
      var w = box.clientWidth, h = box.clientHeight; if (!w) return; var c = canvas(cv, w, h), narrow = w < 700, pad = Math.max(narrow ? 16 : 24, (w - 1328) / 2);
      var X0 = pad + 40, X1 = w - pad - (narrow ? 14 : 130), Tp = narrow ? 170 : 150, B = h - 56, end = Math.round(f * (N - 1)), sel = at != null ? at : end;
      function X(i) { return X0 + (T[i] - T[0]) / (T[N - 1] - T[0]) * (X1 - X0); } function Y(v) { return B - (v - mn) / (mx - mn) * (B - Tp); } geo = { X0: X0, X1: X1 };
      c.font = "300 12px" + FONT;
      for (var g = Math.ceil(mn / 10) * 10; g <= mx; g += narrow ? 20 : 10) { c.strokeStyle = "rgba(255,255,255,.06)"; c.beginPath(); c.moveTo(X0, Y(g)); c.lineTo(X1, Y(g)); c.stroke(); c.fillStyle = "#74797c"; c.textAlign = "right"; c.fillText(g + "%", X0 - 10, Y(g)); }
      var ya = new Date(T[0]).getUTCFullYear(), yb = new Date(T[N - 1]).getUTCFullYear();
      for (var y = ya; y <= yb; y++) [0, 6].forEach(function (m) { var t = Date.UTC(y, m, 1); if (t < T[0] || t > T[N - 1] || (narrow && m)) return; var x = X0 + (t - T[0]) / (T[N - 1] - T[0]) * (X1 - X0); c.fillStyle = "#a3a8aa"; c.textAlign = "center"; c.fillText(m ? "Jul" : String(y), x, B + 18); });
      // what actually happened, behind and dim
      c.beginPath(); var on = false; for (var i = 0; i <= end; i++) { if (RV[i] == null) { on = false; continue; } on ? c.lineTo(X(i), Y(RV[i])) : c.moveTo(X(i), Y(RV[i])); on = true; } c.strokeStyle = "rgba(242,243,243,.3)"; c.lineWidth = 1; c.stroke();
      // the pulse and the light that falls from it
      var grd = c.createLinearGradient(0, Tp, 0, B); grd.addColorStop(0, "rgba(255,176,72,.20)"); grd.addColorStop(1, "rgba(255,176,72,0)");
      c.beginPath(); c.moveTo(X(0), B); for (i = 0; i <= end; i++) c.lineTo(X(i), Y(V[i])); c.lineTo(X(end), B); c.closePath(); c.fillStyle = grd; c.fill();
      c.globalCompositeOperation = "lighter"; [[16, 0.05], [6, 0.12], [2.2, 0.95]].forEach(function (p) { c.beginPath(); for (var k = 0; k <= end; k++) k ? c.lineTo(X(k), Y(V[k])) : c.moveTo(X(k), Y(V[k])); c.strokeStyle = "rgba(255,176,72," + p[1] + ")"; c.lineWidth = p[0]; c.lineJoin = "round"; c.stroke(); });
      var hx = X(end), hy = Y(V[end]), gr = c.createRadialGradient(hx, hy, 0, hx, hy, 26); gr.addColorStop(0, "rgba(255,200,120,.95)"); gr.addColorStop(0.25, "rgba(255,176,72,.3)"); gr.addColorStop(1, "rgba(255,176,72,0)"); c.fillStyle = gr; c.beginPath(); c.arc(hx, hy, 26, 0, 7); c.fill(); c.globalCompositeOperation = "source-over";
      peaks.slice(0, narrow ? 2 : 4).forEach(function (p) { if (p > end) return; var x = X(p), y2 = Y(V[p]); c.fillStyle = "#ffd99a"; c.beginPath(); c.arc(x, y2, 3, 0, 7); c.fill(); var tx = Math.max(X0 + 34, Math.min(X1 - 34, x)); c.textAlign = "center"; c.font = "400 13px" + FONT; c.fillStyle = "#f2f3f3"; c.fillText(V[p].toFixed(0) + "%", tx, y2 - 30); c.font = "300 12px" + FONT; c.fillStyle = "#a3a8aa"; c.fillText(day(T[p]), tx, y2 - 14); });
      if (at != null) { c.strokeStyle = "rgba(242,243,243,.35)"; c.lineWidth = 1; c.beginPath(); c.moveTo(X(at), Tp - 10); c.lineTo(X(at), B); c.stroke(); c.fillStyle = "#ffd99a"; c.beginPath(); c.arc(X(at), Y(V[at]), 4, 0, 7); c.fill(); }
      var lr = null; for (i = sel; i >= 0 && lr == null; i--) lr = RV[i];
      if (!narrow) { c.textAlign = "left"; c.font = "500 14px" + FONT; c.fillStyle = "#ffd99a"; c.fillText("Expected  " + V[end].toFixed(0) + "%", hx + 16, hy - 4); if (lr != null && f >= 1) { c.font = "300 13px" + FONT; c.fillStyle = "#a3a8aa"; c.fillText("Actual  " + RV[N - 1 - (RV[N - 1] == null ? 1 : 0)].toFixed(0) + "%", hx + 16, hy + 16); } }
      fig.textContent = f < 1 || at != null ? V[sel].toFixed(1) + "%" : figNow;
      read.textContent = (at != null ? day(T[sel]) : f >= 1 ? "Today" : day(T[end])) + ": expected " + V[sel].toFixed(1) + "% a year" + (lr != null ? " · actual, the 30 days before, " + lr.toFixed(1) + "%" : "") + " · the grey line is what the price did";
    }
    function play() { cancelAnimationFrame(raf); at = null; if (still) { f = 1; draw(); return; } var s0 = performance.now(); f = 0; (function tick(n) { f = Math.max(0, Math.min(1, (n - s0) / 6000)); draw(); if (f < 1) raf = requestAnimationFrame(tick); })(s0); }
    function pick(e) { if (f < 1) return; var b = cv.getBoundingClientRect(), x = e.clientX - b.left; if (x < geo.X0 - 10 || x > geo.X1 + 10) { if (at != null) { at = null; draw(); } return; }
      var t = T[0] + Math.max(0, Math.min(1, (x - geo.X0) / (geo.X1 - geo.X0))) * (T[N - 1] - T[0]), best = 0; for (var i = 1; i < N; i++) if (Math.abs(T[i] - t) < Math.abs(T[best] - t)) best = i; if (best !== at) { at = best; draw(); } }
    cv.addEventListener("pointermove", pick); cv.addEventListener("pointerdown", pick); cv.addEventListener("pointerleave", function () { if (at != null) { at = null; draw(); } });
    cv.tabIndex = 0; cv.addEventListener("keydown", function (e) { var dlt = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (!dlt || f < 1) return; e.preventDefault(); at = Math.max(0, Math.min(N - 1, (at == null ? N - 1 : at) + dlt * (e.shiftKey ? 30 : 3))); draw(); });
    cv.addEventListener("blur", function () { if (at != null) { at = null; draw(); } });
    box.querySelector(".vr__replay").addEventListener("click", play);
    box.hidden = false; document.querySelector("main").classList.add("has-race");
    var started = false, go = function () { if (started) return; started = true; play(); };
    fonts(function () { if ("IntersectionObserver" in window) new IntersectionObserver(function (en, ob) { if (en[0].isIntersecting) { ob.disconnect(); go(); } }).observe(box); else go(); });
    if ("ResizeObserver" in window) new ResizeObserver(function () { if (started) draw(); }).observe(box);
  })();

  // ---- the plain charts ----------------------------------------------------------------------------------------
  function plot(el, o) {
    var cv = el.querySelector("canvas"); if (!cv) { cv = document.createElement("canvas"); cv.setAttribute("role", "img"); cv.setAttribute("aria-label", o.label); el.appendChild(cv); }
    var w = el.clientWidth; if (!w) return null; var narrow = w < 560, h = narrow ? o.hn || 220 : o.h; cv.style.width = "100%"; cv.style.height = h + "px"; var c = canvas(cv, w, h), L = 52, R = w - (narrow ? 14 : o.right || 40), Tp = 16, B = h - 30;
    function X(v) { return L + (v - o.x0) / (o.x1 - o.x0) * (R - L); } function Y(v) { return B - (v - o.y0) / (o.y1 - o.y0) * (B - Tp); }
    c.font = "400 12px" + FONT;
    o.yticks.forEach(function (t) { c.strokeStyle = "rgba(255,255,255,.07)"; c.beginPath(); c.moveTo(L, Y(t[0])); c.lineTo(R, Y(t[0])); c.stroke(); c.fillStyle = "#a3a8aa"; c.textAlign = "right"; c.fillText(t[1], L - 8, Y(t[0])); });
    var lastX = -1e9; o.xticks.forEach(function (t) { var x = X(t[0]), tw = c.measureText(t[1]).width; if (x - tw / 2 < lastX + 10) return; lastX = x + tw / 2; c.fillStyle = "#a3a8aa"; c.textAlign = "center"; c.fillText(t[1], x, B + 17); });
    if (o.zero) { c.setLineDash([3, 4]); c.strokeStyle = "rgba(242,243,243,.35)"; c.beginPath(); c.moveTo(L, Y(0)); c.lineTo(R, Y(0)); c.stroke(); c.setLineDash([]); }
    if (o.vline) { var vx = X(o.vline[0]); c.setLineDash([3, 4]); c.strokeStyle = "rgba(242,243,243,.35)"; c.beginPath(); c.moveTo(vx, Tp); c.lineTo(vx, B); c.stroke(); c.setLineDash([]); c.fillStyle = "#a3a8aa"; c.textAlign = "left"; c.fillText(o.vline[1], vx + 6, Tp + 8); }
    if (o.fill) { c.fillStyle = "rgba(255,255,255,.07)"; c.beginPath(); c.moveTo(X(o.pts[0][0]), Y(0)); o.pts.forEach(function (p) { c.lineTo(X(p[0]), Y(p[1])); }); c.lineTo(X(o.pts[o.pts.length - 1][0]), Y(0)); c.closePath(); c.fill(); }
    c.beginPath(); o.pts.forEach(function (p, i) { i ? c.lineTo(X(p[0]), Y(p[1])) : c.moveTo(X(p[0]), Y(p[1])); }); c.strokeStyle = "#f2f3f3"; c.lineWidth = 1.5; c.lineJoin = "round"; c.stroke();
    if (o.dots) { var lastL = -1e9; o.pts.forEach(function (p) { var x = X(p[0]), y = Y(p[1]); c.fillStyle = "#f2f3f3"; c.beginPath(); c.arc(x, y, 2.6, 0, 7); c.fill(); var t = sgn(p[1]) + "%", tw = c.measureText(t).width; if (x - tw / 2 < lastL + 8) return; lastL = x + tw / 2; c.textAlign = "center"; c.fillText(t, Math.min(R - tw / 2, x), y - 14); }); }
    if (o.end) { var lp = o.pts[o.pts.length - 1]; c.fillStyle = "#f2f3f3"; c.beginPath(); c.arc(X(lp[0]), Y(lp[1]), 3, 0, 7); c.fill(); if (!narrow) { c.textAlign = "left"; c.fillText(o.end, X(lp[0]) + 8, Y(lp[1])); } }
    if (o.at != null) { var ap = o.pts[o.at]; c.strokeStyle = "rgba(242,243,243,.4)"; c.beginPath(); c.moveTo(X(ap[0]), Tp); c.lineTo(X(ap[0]), B); c.stroke(); c.fillStyle = "#f2f3f3"; c.beginPath(); c.arc(X(ap[0]), Y(ap[1]), 3.5, 0, 7); c.fill(); }
    return { cv: cv, L: L, R: R };
  }
  function nice(lo, hi, n) { var raw = (hi - lo) / n, p = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / p; return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * p; }

  var fe = document.querySelector('.vm-plot[data-chart="fund"]');
  if (fe && J.fund && J.fund.v.length > 10) (function () {
    var f0 = Date.parse(J.fund.start), pts = J.fund.d.map(function (k, i) { return [f0 + k * DAY, J.fund.v[i]]; }), n = pts.length, read = document.querySelector('[data-read="fund"]'), base = read.innerHTML, at = null, geo = null;
    var m = 0; pts.forEach(function (p) { m = Math.max(m, Math.abs(p[1])); }); var top = Math.max(10, Math.ceil(m / 10) * 10), xt = [], d = new Date(pts[0][0]); d.setUTCDate(1);
    for (var k = 0; k < 40; k++) { d.setUTCMonth(d.getUTCMonth() + 1); if (d.getTime() > pts[n - 1][0]) break; xt.push([d.getTime(), MON[d.getUTCMonth()] + (d.getUTCMonth() === 0 ? " " + d.getUTCFullYear() : "")]); }
    function draw() { geo = plot(fe, { label: "The perpetual's funding rate each day, as a yearly rate.", h: 260, right: 104, x0: pts[0][0], x1: pts[n - 1][0], y0: -top, y1: top, pts: pts, fill: true, zero: true, at: at, end: sgn(pts[n - 1][1]) + "% a year",
        yticks: [[-top, MIN + top + "%"], [0, "0%"], [top, "+" + top + "%"]], xticks: xt });
      if (at != null) { var v = pts[at][1], r = Math.round(v * 10) / 10; read.innerHTML = day(pts[at][0]) + ': <span class="' + (r > 0 ? "up" : r < 0 ? "down" : "") + '">' + sgn(v) + "%</span> a year · " + (r > 0 ? "longs paid shorts" : r < 0 ? "shorts paid longs" : "no one paid"); } else read.innerHTML = base; }
    fonts(function () { draw(); if (!geo) return; var cv = geo.cv; cv.tabIndex = 0;
      function pick(e) { var b = cv.getBoundingClientRect(); at = Math.round(Math.max(0, Math.min(1, (e.clientX - b.left - geo.L) / (geo.R - geo.L))) * (n - 1)); draw(); }
      cv.addEventListener("pointermove", pick); cv.addEventListener("pointerdown", pick); cv.addEventListener("pointerleave", function () { at = null; draw(); }); cv.addEventListener("blur", function () { at = null; draw(); });
      cv.addEventListener("keydown", function (e) { var dlt = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (!dlt) return; e.preventDefault(); at = Math.max(0, Math.min(n - 1, (at == null ? n - 1 : at) + dlt * (e.shiftKey ? 7 : 1))); draw(); }); });
    if ("ResizeObserver" in window) new ResizeObserver(draw).observe(fe);
  })();

  var ce = document.querySelector('.vm-plot[data-chart="curve"]');
  if (ce && J.curve && J.curve.length > 1) (function () {
    var pts = J.curve.map(function (r) { return [r[0], r[1]]; }), lo = Math.min(0, Math.min.apply(0, pts.map(function (p) { return p[1]; }))), hi = Math.max(0, Math.max.apply(0, pts.map(function (p) { return p[1]; }))), st = nice(lo, hi, 4), y0 = Math.floor(lo / st) * st, y1 = Math.ceil(hi / st) * st + st * 0.6, yt = [];
    for (var v = y0; v <= y1 + 1e-9; v += st) yt.push([v, sgn(v, st < 1 ? 1 : 0) + "%"]);
    function draw() { plot(ce, { label: "Each future's premium over Bitcoin's price, as a yearly rate, by expiry.", h: 240, x0: 0, x1: pts[pts.length - 1][0] * 1.03, y0: y0, y1: y1, pts: pts, zero: true, dots: true, yticks: yt,
        xticks: J.curve.map(function (r) { var d = new Date(r[2]); return [r[0], d.getUTCDate() + " " + MON[d.getUTCMonth()] + " " + String(d.getUTCFullYear()).slice(2)]; }) }); }
    fonts(draw); if ("ResizeObserver" in window) new ResizeObserver(draw).observe(ce);
  })();

  var se = document.querySelector('.vm-plot[data-chart="smile"]');
  if (se && J.smile && J.smile.length > 3) (function () {
    var pts = J.smile, lo = Math.floor(Math.min.apply(0, pts.map(function (p) { return p[1]; })) / 10) * 10, hi = Math.ceil(Math.max.apply(0, pts.map(function (p) { return p[1]; })) / 10) * 10, yt = [], xt = [], st = hi - lo > 60 ? 20 : 10;
    for (var v = lo; v <= hi; v += st) yt.push([v, v + "%"]); var x0 = pts[0][0], x1 = pts[pts.length - 1][0], xs = nice(x0, x1, 7);
    for (var k = Math.ceil(x0 / xs) * xs; k <= x1; k += xs) xt.push([k, "$" + (k / 1000) + "k"]);
    function draw() { plot(se, { label: "The volatility options price in at each strike for the largest expiry.", h: 280, x0: x0, x1: x1, y0: lo, y1: hi, pts: pts, yticks: yt, xticks: xt, vline: [J.und, "Bitcoin now"] }); }
    fonts(draw); if ("ResizeObserver" in window) new ResizeObserver(draw).observe(se);
  })();
})();
