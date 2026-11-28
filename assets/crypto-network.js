/* Crypto: Network (owner-approved sketch, 28 Nov 2026). The Lightning nodes on the Earth are drawn by
   assets/crypto-globe.js, from its own data. This script draws, from the JSON in the page (mempool.space):
   the power, under the globe: the hashrate since 2010 as a line of amber light with a soft fall of light under it
   (the pulse of Derivatives), drawn from its first day to today in about six seconds, the four halvings dashed and
   the fall of 2021 named; the figure at the left follows the day while it draws or under the pointer; Replay;
   pointing or the arrow keys read out any day; drawn at once under reduced motion;
   and the fees: the middle transaction's rate and the dearest tenth's over a year, in the dashboard style.
   Amber is the group's light, not a rise; red and green only on signed figures. Without this script the page
   keeps its text, bars, tables and Latest panel. */
(function () {
  "use strict";
  var src = document.getElementById("nw-data"); if (!src) return;
  var J; try { J = JSON.parse(src.textContent); } catch (e) { return; }
  var MIN = "−", DAY = 864e5, MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches, dpr = Math.min(window.devicePixelRatio || 1, 2), FONT = " Inter, 'Helvetica Neue', Arial, sans-serif";
  function day(t) { var d = new Date(t); return d.getUTCDate() + " " + MON[d.getUTCMonth()] + " " + d.getUTCFullYear(); }
  function canvas(cv, w, h) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); var c = cv.getContext("2d"); c.setTransform(dpr, 0, 0, dpr, 0, 0); c.textBaseline = "middle"; return c; }
  function fonts(fn) { if (document.fonts && document.fonts.load) document.fonts.load("300 12px Inter").then(fn, fn); else fn(); }
  function power(v) { return v >= 1000 ? (v / 1000).toFixed(2) + " ZH/s" : v >= 10 ? Math.round(v).toLocaleString("en-US") + " EH/s" : v >= 0.01 ? v.toFixed(2) + " EH/s" : v.toPrecision(2) + " EH/s"; }
  document.querySelector("main").classList.add("has-race");

  var box = document.querySelector(".nwh"), HS = J.hash;
  if (box && HS && HS.v.length > 100) (function () {
    var cv = box.querySelector(".vr__c"), read = box.querySelector(".vr__read"), fig = box.querySelector(".dvh__fig b"), t0 = Date.parse(HS.start), V = HS.v, N = V.length, figNow = fig.textContent;
    function T(i) { return t0 + i * HS.step * DAY; } function at(t) { return Math.max(0, Math.min(N - 1, Math.round((t - t0) / (HS.step * DAY)))); }
    var f = still ? 1 : 0, raf = 0, sel = null, geo = {}, top = 0; V.forEach(function (v) { top = Math.max(top, v); });
    var st = top > 800 ? 200 : top > 300 ? 100 : 50, mx = Math.ceil(top * 1.06 / st) * st;
    function draw() {
      var w = box.clientWidth, h = box.clientHeight; if (!w) return; var c = canvas(cv, w, h), narrow = w < 700, pad = Math.max(narrow ? 16 : 24, (w - 1328) / 2);
      var X0 = pad + 64, X1 = w - pad - (narrow ? 14 : 120), Tp = narrow ? 180 : 160, B = h - 56, end = Math.round(f * (N - 1)), k = sel != null ? sel : end;
      function X(i) { return X0 + i / (N - 1) * (X1 - X0); } function Y(v) { return B - v / mx * (B - Tp); } geo = { X0: X0, X1: X1 };
      c.font = "300 12px" + FONT;
      for (var g = 0; g <= mx; g += narrow ? st * 2 : st) { c.strokeStyle = "rgba(255,255,255,.06)"; c.beginPath(); c.moveTo(X0, Y(g)); c.lineTo(X1, Y(g)); c.stroke(); c.fillStyle = "#74797c"; c.textAlign = "right"; c.fillText(g + " EH/s", X0 - 10, Y(g)); }
      var ya = new Date(T(0)).getUTCFullYear(), yb = new Date(T(N - 1)).getUTCFullYear(); for (var y = ya + 2; y <= yb; y += narrow ? 4 : 2) { c.fillStyle = "#a3a8aa"; c.textAlign = "center"; c.fillText(String(y), X(at(Date.UTC(y, 0, 1))), B + 18); }
      (HS.halvings || []).forEach(function (d, n) { var i = at(Date.parse(d)); if (i > end) return; var x = X(i); c.setLineDash([3, 4]); c.strokeStyle = "rgba(242,243,243,.28)"; c.lineWidth = 1; c.beginPath(); c.moveTo(x, Tp); c.lineTo(x, B); c.stroke(); c.setLineDash([]); c.fillStyle = "#a3a8aa"; c.textAlign = "left"; c.fillText(narrow ? "H" + (n + 1) : "Halving " + (n + 1), x + 6, Tp + 8); });
      var grd = c.createLinearGradient(0, Tp, 0, B); grd.addColorStop(0, "rgba(255,176,72,.22)"); grd.addColorStop(1, "rgba(255,176,72,0)");
      c.beginPath(); c.moveTo(X(0), B); for (var i = 0; i <= end; i++) c.lineTo(X(i), Y(V[i])); c.lineTo(X(end), B); c.closePath(); c.fillStyle = grd; c.fill();
      c.globalCompositeOperation = "lighter"; [[16, 0.05], [6, 0.12], [2.2, 0.95]].forEach(function (p) { c.beginPath(); for (var q = 0; q <= end; q++) q ? c.lineTo(X(q), Y(V[q])) : c.moveTo(X(q), Y(V[q])); c.strokeStyle = "rgba(255,176,72," + p[1] + ")"; c.lineWidth = p[0]; c.lineJoin = "round"; c.stroke(); });
      var hx = X(end), hy = Y(V[end]), gr = c.createRadialGradient(hx, hy, 0, hx, hy, 26); gr.addColorStop(0, "rgba(255,200,120,.95)"); gr.addColorStop(0.25, "rgba(255,176,72,.3)"); gr.addColorStop(1, "rgba(255,176,72,0)"); c.fillStyle = gr; c.beginPath(); c.arc(hx, hy, 26, 0, 7); c.fill(); c.globalCompositeOperation = "source-over";
      (HS.marks || []).forEach(function (m) { if (m.i > end || narrow) return; var x = X(m.i), y2 = Y(V[m.i]); c.fillStyle = "#ffd99a"; c.beginPath(); c.arc(x, y2, 3, 0, 7); c.fill(); c.textAlign = "center"; c.font = "400 13px" + FONT; c.fillStyle = "#ff4b52"; c.fillText(MIN + Math.abs(m.fall) + "%", x, y2 - 62); c.font = "300 12px" + FONT; c.fillStyle = "#a3a8aa"; c.fillText(m.text, x, y2 - 46); c.strokeStyle = "rgba(242,243,243,.3)"; c.beginPath(); c.moveTo(x, y2 - 36); c.lineTo(x, y2 - 8); c.stroke(); });
      if (sel != null) { c.strokeStyle = "rgba(242,243,243,.35)"; c.lineWidth = 1; c.beginPath(); c.moveTo(X(sel), Tp - 10); c.lineTo(X(sel), B); c.stroke(); c.fillStyle = "#ffd99a"; c.beginPath(); c.arc(X(sel), Y(V[sel]), 4, 0, 7); c.fill(); }
      if (!narrow) { c.textAlign = "left"; c.font = "500 14px" + FONT; c.fillStyle = "#ffd99a"; c.fillText(power(V[end]), hx + 16, hy); }
      fig.textContent = f < 1 || sel != null ? power(V[k]) : figNow;
      var ago = at(T(k) - 365 * DAY), chg = k > ago && V[ago] > 0 ? (V[k] / V[ago] - 1) * 100 : null;
      read.textContent = (sel != null ? "Week to " + day(T(k)) : f >= 1 ? "Now" : day(T(k))) + ": " + power(V[k]) + (chg != null ? " · " + (chg >= 0 ? "+" : MIN) + Math.abs(Math.round(chg)).toLocaleString("en-US") + "% on a year before" : "") + " · dashed, the halvings";
    }
    function play() { cancelAnimationFrame(raf); sel = null; if (still) { f = 1; draw(); return; } var s0 = performance.now(); f = 0; (function tick(n) { f = Math.max(0, Math.min(1, (n - s0) / 6000)); draw(); if (f < 1) raf = requestAnimationFrame(tick); })(s0); }
    function pick(e) { if (f < 1) return; var b = cv.getBoundingClientRect(), x = e.clientX - b.left; if (x < geo.X0 - 10 || x > geo.X1 + 10) { if (sel != null) { sel = null; draw(); } return; } var i = Math.round(Math.max(0, Math.min(1, (x - geo.X0) / (geo.X1 - geo.X0))) * (N - 1)); if (i !== sel) { sel = i; draw(); } }
    cv.addEventListener("pointermove", pick); cv.addEventListener("pointerdown", pick); cv.addEventListener("pointerleave", function () { if (sel != null) { sel = null; draw(); } });
    cv.tabIndex = 0; cv.addEventListener("keydown", function (e) { var dlt = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (!dlt || f < 1) return; e.preventDefault(); sel = Math.max(0, Math.min(N - 1, (sel == null ? N - 1 : sel) + dlt * (e.shiftKey ? 90 : 7))); draw(); });
    cv.addEventListener("blur", function () { if (sel != null) { sel = null; draw(); } });
    box.querySelector(".vr__replay").addEventListener("click", play);
    box.hidden = false; var started = false, go = function () { if (started) return; started = true; play(); };
    fonts(function () { if ("IntersectionObserver" in window) new IntersectionObserver(function (en, ob) { if (en[0].isIntersecting) { ob.disconnect(); go(); } }, { threshold: 0.25 }).observe(box); else go(); });
    if ("ResizeObserver" in window) new ResizeObserver(function () { if (started) draw(); }).observe(box);
  })();

  var fe = document.querySelector('.vm-plot[data-chart="fees"]'), F = J.fees;
  if (fe && F && F.t.length > 20) (function () {
    var cv = document.createElement("canvas"), n = F.t.length, CAP = 60, read = document.querySelector('[data-read="fees"]'), base = read.innerHTML, sel = null, geo = {};
    cv.setAttribute("role", "img"); cv.setAttribute("aria-label", "The fee rate of the middle transaction and of the dearest tenth, block by block over a year."); cv.tabIndex = 0; fe.appendChild(cv);
    function draw() { var w = fe.clientWidth; if (!w) return; var narrow = w < 560, h = narrow ? 230 : 280; cv.style.width = "100%"; cv.style.height = h + "px"; var c = canvas(cv, w, h), L = 44, R = w - (narrow ? 14 : 150), Tp = 14, B = h - 30;
      function X(i) { return L + i / (n - 1) * (R - L); } function Y(v) { return B - Math.min(v, CAP) / CAP * (B - Tp); } geo = { L: L, R: R };
      c.font = "400 12px" + FONT; [0, 20, 40, 60].forEach(function (g) { c.strokeStyle = "rgba(255,255,255,.07)"; c.beginPath(); c.moveTo(L, Y(g)); c.lineTo(R, Y(g)); c.stroke(); c.fillStyle = "#a3a8aa"; c.textAlign = "right"; c.fillText(g === CAP ? CAP + "+" : String(g), L - 8, Y(g)); });
      var lastM = -1, lastX = -1e9; for (var i = 0; i < n; i++) { var d = new Date(F.t[i] * 1000), m = d.getUTCMonth(); if (m !== lastM) { lastM = m; var x = X(i); if (i && x - lastX > (narrow ? 60 : 44)) { lastX = x; c.fillStyle = "#a3a8aa"; c.textAlign = "center"; c.fillText(MON[m] + (m === 0 ? " " + d.getUTCFullYear() : ""), x, B + 17); } } }
      c.beginPath(); for (i = 0; i < n; i++) i ? c.lineTo(X(i), Y(F.top[i])) : c.moveTo(X(i), Y(F.top[i])); c.setLineDash([5, 4]); c.strokeStyle = "rgba(242,243,243,.55)"; c.lineWidth = 1; c.stroke(); c.setLineDash([]);
      c.beginPath(); for (i = 0; i < n; i++) i ? c.lineTo(X(i), Y(F.mid[i])) : c.moveTo(X(i), Y(F.mid[i])); c.strokeStyle = "#f2f3f3"; c.lineWidth = 1.5; c.stroke();
      if (!narrow) { var ya = Y(F.top[n - 1]), yb = Y(F.mid[n - 1]); if (yb - ya < 15) ya = yb - 15; c.textAlign = "left"; c.fillStyle = "#a3a8aa"; c.fillText("Dearest tenth " + F.top[n - 1], R + 8, ya); c.fillStyle = "#f2f3f3"; c.fillText("Middle " + F.mid[n - 1] + " sat/vB", R + 8, yb); }
      if (sel != null) { c.strokeStyle = "rgba(242,243,243,.4)"; c.beginPath(); c.moveTo(X(sel), Tp); c.lineTo(X(sel), B); c.stroke(); read.textContent = day(F.t[sel] * 1000) + ": the middle transaction paid " + F.mid[sel] + " sat/vB · the dearest tenth " + F.top[sel]; } else read.innerHTML = base; }
    function pick(e) { var b = cv.getBoundingClientRect(); sel = Math.round(Math.max(0, Math.min(1, (e.clientX - b.left - geo.L) / (geo.R - geo.L))) * (n - 1)); draw(); }
    cv.addEventListener("pointermove", pick); cv.addEventListener("pointerdown", pick); cv.addEventListener("pointerleave", function () { sel = null; draw(); }); cv.addEventListener("blur", function () { sel = null; draw(); });
    cv.addEventListener("keydown", function (e) { var dlt = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (!dlt) return; e.preventDefault(); sel = Math.max(0, Math.min(n - 1, (sel == null ? n - 1 : sel) + dlt * (e.shiftKey ? 10 : 1))); draw(); });
    fonts(draw); if ("ResizeObserver" in window) new ResizeObserver(draw).observe(fe);
  })();
})();
