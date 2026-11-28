/* Crypto: Stablecoins & DeFi (owner, 28 Nov 2026: the plain data page, after a line of light and a river of strands
   were turned down). Two charts in the dashboard style, from the JSON in the page (DefiLlama): every stablecoin in
   circulation and the value locked in DeFi, in billions of dollars since 2019. One ink line each, a hairline grid,
   the latest at its end; pointing at a chart, or the arrow keys on it, reads out that day under it. Without this
   script the page keeps its text, bars, tables and Latest panel. */
(function () {
  "use strict";
  var src = document.getElementById("sd-data"); if (!src) return;
  var J; try { J = JSON.parse(src.textContent); } catch (e) { return; }
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], dpr = Math.min(window.devicePixelRatio || 1, 2), FONT = " Inter, 'Helvetica Neue', Arial, sans-serif";
  function day(t) { var d = new Date(t * 1000); return d.getUTCDate() + " " + MON[d.getUTCMonth()] + " " + d.getUTCFullYear(); }
  function bn(v) { return "$" + (v >= 100 ? v.toFixed(0) : v.toFixed(1)) + "bn"; }
  [].forEach.call(document.querySelectorAll(".sdp .vm-plot"), function (el) {
    var S = J[el.getAttribute("data-chart")]; if (!S || S.v.length < 10) return;
    var unit = el.getAttribute("data-unit") || "", read = document.querySelector('[data-read="' + el.getAttribute("data-chart") + '"]'), base = read ? read.innerHTML : "", n = S.v.length, at = null, geo = {};
    var cv = document.createElement("canvas"); cv.setAttribute("role", "img"); cv.tabIndex = 0; cv.setAttribute("aria-label", (el.getAttribute("data-chart") === "tvl" ? "The value locked in DeFi" : "Stablecoins in circulation") + ", in billions of dollars, since 2019. Now " + bn(S.v[n - 1]) + "."); el.appendChild(cv);
    var top = Math.max.apply(0, S.v), st = top > 250 ? 100 : top > 120 ? 50 : 25, mx = Math.ceil(top * 1.05 / st) * st;
    function draw() { var w = el.clientWidth; if (!w) return; var narrow = w < 560, h = narrow ? 230 : 300; cv.style.width = "100%"; cv.style.height = h + "px"; cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
      var c = cv.getContext("2d"); c.setTransform(dpr, 0, 0, dpr, 0, 0); c.textBaseline = "middle"; c.font = "400 12px" + FONT; var L = 60, R = w - (narrow ? 14 : 90), Tp = 14, B = h - 30;
      function X(i) { return L + (S.t[i] - S.t[0]) / (S.t[n - 1] - S.t[0]) * (R - L); } function Y(v) { return B - v / mx * (B - Tp); } geo = { L: L, R: R };
      for (var g = 0; g <= mx; g += st) { c.strokeStyle = "rgba(255,255,255,.07)"; c.beginPath(); c.moveTo(L, Y(g)); c.lineTo(R, Y(g)); c.stroke(); c.fillStyle = "#a3a8aa"; c.textAlign = "right"; c.fillText(g ? "$" + g + "bn" : "$0", L - 8, Y(g)); }
      var ya = new Date(S.t[0] * 1000).getUTCFullYear(), yb = new Date(S.t[n - 1] * 1000).getUTCFullYear(); for (var y = ya + 1; y <= yb; y += narrow ? 2 : 1) { var ts = Date.UTC(y, 0, 1) / 1000, x = L + (ts - S.t[0]) / (S.t[n - 1] - S.t[0]) * (R - L); c.fillStyle = "#a3a8aa"; c.textAlign = "center"; c.fillText(String(y), x, B + 17); }
      c.beginPath(); for (var i = 0; i < n; i++) i ? c.lineTo(X(i), Y(S.v[i])) : c.moveTo(X(i), Y(S.v[i])); c.strokeStyle = "#f2f3f3"; c.lineWidth = 1.5; c.lineJoin = "round"; c.stroke();
      c.fillStyle = "#f2f3f3"; c.beginPath(); c.arc(X(n - 1), Y(S.v[n - 1]), 3, 0, 7); c.fill(); if (!narrow) { c.textAlign = "left"; c.fillText(bn(S.v[n - 1]), X(n - 1) + 8, Y(S.v[n - 1])); }
      if (at != null) { c.strokeStyle = "rgba(242,243,243,.4)"; c.lineWidth = 1; c.beginPath(); c.moveTo(X(at), Tp); c.lineTo(X(at), B); c.stroke(); c.fillStyle = "#f2f3f3"; c.beginPath(); c.arc(X(at), Y(S.v[at]), 3.5, 0, 7); c.fill(); if (read) read.textContent = day(S.t[at]) + ": " + bn(S.v[at]) + " " + unit; } else if (read) read.innerHTML = base; }
    function pick(e) { var b = cv.getBoundingClientRect(), ts = S.t[0] + Math.max(0, Math.min(1, (e.clientX - b.left - geo.L) / (geo.R - geo.L))) * (S.t[n - 1] - S.t[0]), best = 0; for (var i = 1; i < n; i++) if (Math.abs(S.t[i] - ts) < Math.abs(S.t[best] - ts)) best = i; if (best !== at) { at = best; draw(); } }
    cv.addEventListener("pointermove", pick); cv.addEventListener("pointerdown", pick); cv.addEventListener("pointerleave", function () { at = null; draw(); }); cv.addEventListener("blur", function () { at = null; draw(); });
    cv.addEventListener("keydown", function (e) { var d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (!d) return; e.preventDefault(); at = Math.max(0, Math.min(n - 1, (at == null ? n - 1 : at) + d * (e.shiftKey ? 30 : 3))); draw(); });
    if (document.fonts && document.fonts.load) document.fonts.load("400 12px Inter").then(draw, draw); else draw();
    if ("ResizeObserver" in window) new ResizeObserver(draw).observe(el);
  });
})();
