/* Crypto: Bitcoin vs markets (owner-approved sketches, 27 Nov 2026: "the race" and "the portfolio's control").
   From the JSON in the page (daily closes on the S&P 500's trading days since September 2014).
   The race, under the page head: Bitcoin (amber, with a glow) and five markets, each at 100 on the same day, drawn
   from that day to today in about seven seconds, the month counting at the left and each line's name and level at
   its head. The chips choose the start; Replay runs it again; once it has run, pointing at it (or the arrow keys)
   reads out any day. Under reduced motion it is drawn at once.
   Moving together: Bitcoin's 90-day correlation with four markets, with a read-out under the pointer.
   The portfolio's control: a slider from 0 to 20% of Bitcoin in a 60/40 portfolio rebalanced monthly; three figures
   and the portfolio's line (amber) against the plain one follow it.
   Amber is the group's light, not a rise: red and green appear only on signed falls and rises. Without this script
   the page keeps its tables and Latest panel. */
(function () {
  "use strict";
  var src = document.getElementById("vm-data"); if (!src) return;
  var J; try { J = JSON.parse(src.textContent); } catch (e) { return; }
  var MIN = "−", DAY = 864e5, MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var t0 = Date.parse(J.start), T = J.d.map(function (k) { return t0 + k * DAY; }), S = J.s, N = T.length;
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches, dpr = Math.min(window.devicePixelRatio || 1, 2), FONT = " Inter, 'Helvetica Neue', Arial, sans-serif";
  function day(t) { var d = new Date(t); return d.getUTCDate() + " " + MON[d.getUTCMonth()] + " " + d.getUTCFullYear(); }
  function yearStart(y) { var t = Date.UTC(y, 0, 1); for (var i = 0; i < N; i++) if (T[i] >= t) return i; return -1; }
  function canvas(cv, w, h) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); var c = cv.getContext("2d"); c.setTransform(dpr, 0, 0, dpr, 0, 0); c.textBaseline = "middle"; return c; }
  function glow(c, rgb, width, k, path) { c.globalCompositeOperation = "lighter"; [[width * 7, 0.05], [width * 3, 0.12], [width, 0.95]].forEach(function (p) { c.beginPath(); path(); c.strokeStyle = "rgba(" + rgb + "," + p[1] * k + ")"; c.lineWidth = p[0]; c.lineJoin = "round"; c.stroke(); }); c.globalCompositeOperation = "source-over"; }

  // ---- the race --------------------------------------------------------------------------------------------
  var LINES = [["BTC", "Bitcoin", "255,176,72", 2.4], ["GOLD", "Gold", "242,243,243", 1.2], ["SPX", "S&P 500", "242,243,243", 1.2, "S&P"], ["NDX", "Nasdaq", "200,206,214", 1.1], ["DXY", "Dollar", "150,156,164", 1], ["BOND", "Treasuries", "150,156,164", 1, "Bonds"]];
  var box = document.querySelector(".vr");
  if (box) (function () {
    var cv = box.querySelector(".vr__c"), dateEl = box.querySelector(".vr__date"), read = box.querySelector(".vr__read"), chips = [].slice.call(box.querySelectorAll("[data-back]"));
    var back = 1260, i0 = 0, mx = 1, f = still ? 1 : 0, raf = 0, at = null, geo = null;
    chips.forEach(function (b) { if (b.getAttribute("aria-pressed") === "true") back = +b.getAttribute("data-back"); });
    function scale() { i0 = Math.max(0, N - 1 - back); mx = 0; LINES.forEach(function (l) { for (var i = i0; i < N; i++) mx = Math.max(mx, S[l[0]][i] / S[l[0]][i0] * 100); });
      var st = mx > 4000 ? 2000 : mx > 1500 ? 500 : mx > 600 ? 200 : mx > 300 ? 100 : 50; mx = Math.ceil(mx * 1.04 / st) * st; geo = { st: st }; }
    function draw() {
      var w = box.clientWidth, h = box.clientHeight; if (!w) return; var c = canvas(cv, w, h), narrow = w < 700, pad = Math.max(narrow ? 16 : 24, (w - 1328) / 2);
      var X0 = pad + 36, X1 = w - pad - (narrow ? 96 : 150), Tp = narrow ? 104 : 96, B = h - 58, end = at != null ? at : i0 + Math.round(f * (N - 1 - i0));
      function X(i) { return X0 + (i - i0) / Math.max(1, N - 1 - i0) * (X1 - X0); } function Y(v) { return B - v / mx * (B - Tp); }
      geo.X0 = X0; geo.X1 = X1;
      c.font = "300 12px" + FONT;
      for (var g = 0; g <= mx; g += geo.st) { c.strokeStyle = "rgba(255,255,255,.06)"; c.beginPath(); c.moveTo(X0, Y(g)); c.lineTo(X1, Y(g)); c.stroke(); c.fillStyle = "#74797c"; c.textAlign = "right"; c.fillText(g >= 1000 ? (g / 1000) + "k" : String(g), X0 - 10, Y(g)); }
      c.setLineDash([3, 5]); c.strokeStyle = "rgba(255,255,255,.24)"; c.beginPath(); c.moveTo(X0, Y(100)); c.lineTo(X1, Y(100)); c.stroke(); c.setLineDash([]);
      var ya = new Date(T[i0]).getUTCFullYear(), yb = new Date(T[N - 1]).getUTCFullYear(), every = (yb - ya > 7 ? 2 : 1) * (narrow && yb - ya > 3 ? 2 : 1);
      for (var y = ya + 1; y <= yb; y++) { if ((y - ya) % every) continue; var k = yearStart(y); if (k < 0) continue; c.fillStyle = k <= end ? "#a3a8aa" : "#3c4043"; c.textAlign = "center"; c.fillText(String(y), X(k), B + 18); }
      var labels = [], stp = Math.max(1, Math.floor((N - i0) / ((X1 - X0) * 1.5)));
      LINES.slice().reverse().forEach(function (l) { var s = S[l[0]], base = s[i0], last = at != null ? N - 1 : end;
        glow(c, l[2], l[3], l[0] === "BTC" ? 1 : 0.75, function () { for (var i = i0; i <= last; i += stp) { var x = X(i), yy = Y(s[i] / base * 100); i === i0 ? c.moveTo(x, yy) : c.lineTo(x, yy); } c.lineTo(X(last), Y(s[last] / base * 100)); });
        var v = s[end] / base * 100, hx = X(end), hy = Y(v), r = l[0] === "BTC" ? 24 : 11, gr = c.createRadialGradient(hx, hy, 0, hx, hy, r); c.globalCompositeOperation = "lighter";
        gr.addColorStop(0, "rgba(" + l[2] + ",.95)"); gr.addColorStop(0.25, "rgba(" + l[2] + ",.3)"); gr.addColorStop(1, "rgba(" + l[2] + ",0)"); c.fillStyle = gr; c.beginPath(); c.arc(hx, hy, r, 0, 7); c.fill(); c.globalCompositeOperation = "source-over";
        labels.push({ n: narrow && l[4] ? l[4] : l[1], v: v, y: hy, btc: l[0] === "BTC" }); });
      if (at != null) { c.strokeStyle = "rgba(242,243,243,.3)"; c.beginPath(); c.moveTo(X(end), Tp); c.lineTo(X(end), B); c.stroke(); }
      labels.sort(function (a, b) { return a.y - b.y; }); for (var j = 1; j < labels.length; j++) if (labels[j].y - labels[j - 1].y < 17) labels[j].y = labels[j - 1].y + 17;
      var over = labels[labels.length - 1].y - (B - 2); if (over > 0) labels.forEach(function (l) { l.y -= over; });
      var lx = at != null ? X1 + 12 : Math.min(X(end) + 14, X1 + 12);
      labels.forEach(function (l) { c.textAlign = "left"; c.font = (l.btc ? "500 " + (narrow ? 13 : 15) + "px" : "300 " + (narrow ? 11 : 13) + "px") + FONT; c.fillStyle = l.btc ? "#ffd99a" : "#c3cad6"; c.fillText(l.n + "  " + Math.round(l.v).toLocaleString("en-US"), lx, l.y); });
      var d = new Date(T[end]); dateEl.textContent = (at != null ? d.getUTCDate() + " " : "") + MON[d.getUTCMonth()] + " " + d.getUTCFullYear();
      if (f >= 1 || at != null) read.textContent = "100 on " + day(T[i0]) + " · " + (at != null ? day(T[end]) : "today") + ": " + LINES.map(function (l) { return l[1] + " " + Math.round(S[l[0]][end] / S[l[0]][i0] * 100).toLocaleString("en-US"); }).join(" · ");
      else read.textContent = "Each line starts at 100 on " + day(T[i0]) + " · Bitcoin in amber";
    }
    function play() { cancelAnimationFrame(raf); at = null; if (still) { f = 1; draw(); return; } var s0 = performance.now(); f = 0; (function tick(n) { f = Math.max(0, Math.min(1, (n - s0) / 7000)); draw(); if (f < 1) raf = requestAnimationFrame(tick); })(s0); }
    chips.forEach(function (b) { b.addEventListener("click", function () { back = +b.getAttribute("data-back"); chips.forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); }); scale(); play(); }); });
    box.querySelector(".vr__replay").addEventListener("click", play);
    function pick(e) { if (f < 1 || !geo.X1) return; var b = cv.getBoundingClientRect(), x = e.clientX - b.left; if (x < geo.X0 - 10 || x > geo.X1 + 10) { if (at != null) { at = null; draw(); } return; }
      at = i0 + Math.round(Math.max(0, Math.min(1, (x - geo.X0) / (geo.X1 - geo.X0))) * (N - 1 - i0)); draw(); }
    cv.addEventListener("pointermove", pick); cv.addEventListener("pointerdown", pick); cv.addEventListener("pointerleave", function () { if (at != null) { at = null; draw(); } });
    cv.tabIndex = 0; cv.addEventListener("keydown", function (e) { var dlt = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (!dlt || f < 1) return; e.preventDefault(); var stepK = Math.max(1, Math.round((N - i0) / (e.shiftKey ? 20 : 200))); at = Math.max(i0, Math.min(N - 1, (at == null ? N - 1 : at) + dlt * stepK)); draw(); });
    cv.addEventListener("blur", function () { if (at != null) { at = null; draw(); } });
    box.hidden = false; document.querySelector("main").classList.add("has-race"); scale();
    var started = false, go = function () { if (started) { draw(); return; } started = true; play(); };
    var ready = function () { if ("IntersectionObserver" in window) new IntersectionObserver(function (en, ob) { if (en[0].isIntersecting) { ob.disconnect(); go(); } }).observe(box); else go(); };
    if (document.fonts && document.fonts.load) document.fonts.load("300 12px Inter").then(ready, ready); else ready();
    if ("ResizeObserver" in window) new ResizeObserver(function () { if (started) draw(); }).observe(box);
  })();

  // ---- daily moves, for the correlation and the portfolio ----------------------------------------------------------
  var R = {}; Object.keys(S).forEach(function (k) { R[k] = [0]; for (var i = 1; i < N; i++) R[k].push(S[k][i] / S[k][i - 1] - 1); });

  // ---- moving together ----------------------------------------------------------------------------------------
  var cp = document.querySelector('.vm-plot[data-chart="corr"]');
  if (cp) (function () {
    var CK = [["SPX", "S&P 500", [], 1.6, 1], ["NDX", "Nasdaq", [6, 4], 1.1, 0.75], ["GOLD", "Gold", [8, 3, 1.5, 3], 1.1, 0.75], ["DXY", "Dollar", [1.5, 3], 1.1, 0.75]], W = 90, STEP = 3, idx = [], cv = document.createElement("canvas"), read = document.querySelector('[data-read="corr"]'), at = null, geo = {};
    cv.setAttribute("role", "img"); cv.setAttribute("aria-label", "Bitcoin's 90-day correlation with the S&P 500, the Nasdaq, gold and the dollar index since 2015."); cv.tabIndex = 0; cp.appendChild(cv);
    function corr(a, b, e) { var ma = 0, mb = 0, i; for (i = e - W; i < e; i++) { ma += a[i]; mb += b[i]; } ma /= W; mb /= W; var s = 0, sa = 0, sb = 0; for (i = e - W; i < e; i++) { s += (a[i] - ma) * (b[i] - mb); sa += (a[i] - ma) * (a[i] - ma); sb += (b[i] - mb) * (b[i] - mb); } return sa && sb ? s / Math.sqrt(sa * sb) : 0; }
    for (var e = W + 1; e <= N; e += STEP) idx.push(e - 1); if (idx[idx.length - 1] !== N - 1) idx.push(N - 1);
    var V = CK.map(function (k) { return idx.map(function (i) { return corr(R.BTC, R[k[0]], i + 1); }); });
    function fmt(v) { return (v < 0 ? MIN : "") + Math.abs(v).toFixed(2); }
    function draw() { var w = cp.clientWidth, narrow = w < 560, h = narrow ? 240 : 320; if (!w) return; cv.style.width = "100%"; cv.style.height = h + "px"; var c = canvas(cv, w, h), L = 44, Rr = w - (narrow ? 12 : 128), Tp = 10, B = h - 28, n = idx.length;
      function X(j) { return L + j / (n - 1) * (Rr - L); } function Y(v) { return B - (v + 0.6) / 1.6 * (B - Tp); } geo = { L: L, R: Rr, n: n };
      c.font = "400 12px" + FONT; [-0.5, 0, 0.5, 1].forEach(function (g) { c.strokeStyle = "rgba(255,255,255,.07)"; c.beginPath(); c.moveTo(L, Y(g)); c.lineTo(Rr, Y(g)); c.stroke(); c.fillStyle = "#a3a8aa"; c.textAlign = "right"; c.fillText(fmt(g).replace(".00", "").replace("0.5", "0.5"), L - 8, Y(g)); });
      c.setLineDash([3, 4]); c.strokeStyle = "rgba(242,243,243,.35)"; c.beginPath(); c.moveTo(L, Y(0)); c.lineTo(Rr, Y(0)); c.stroke(); c.setLineDash([]);
      var ya = new Date(T[idx[0]]).getUTCFullYear(), yb = new Date(T[N - 1]).getUTCFullYear(); for (var y = ya + 1; y <= yb; y++) { if ((y - ya) % (narrow ? 4 : 2)) continue; var t = Date.UTC(y, 0, 1), j = 0; while (j < n - 1 && T[idx[j]] < t) j++; c.fillStyle = "#a3a8aa"; c.textAlign = "center"; c.fillText(String(y), X(j), B + 17); }
      var labels = []; CK.forEach(function (k, q) { c.beginPath(); V[q].forEach(function (v, j) { j ? c.lineTo(X(j), Y(v)) : c.moveTo(X(j), Y(v)); }); c.setLineDash(k[2]); c.strokeStyle = "rgba(242,243,243," + k[4] + ")"; c.lineWidth = k[3]; c.stroke(); c.setLineDash([]); labels.push({ t: k[1] + " " + fmt(V[q][n - 1]), y: Y(V[q][n - 1]), main: !q }); });
      if (!narrow) { labels.sort(function (a, b) { return a.y - b.y; }); for (var q2 = 1; q2 < labels.length; q2++) if (labels[q2].y - labels[q2 - 1].y < 15) labels[q2].y = labels[q2 - 1].y + 15; labels.forEach(function (l) { c.fillStyle = l.main ? "#f2f3f3" : "#a3a8aa"; c.textAlign = "left"; c.fillText(l.t, Rr + 8, l.y); }); }
      if (at != null) { c.strokeStyle = "rgba(242,243,243,.4)"; c.beginPath(); c.moveTo(X(at), Tp); c.lineTo(X(at), B); c.stroke(); }
      var j2 = at != null ? at : n - 1; read.textContent = (at != null ? "90 days to " + day(T[idx[j2]]) : "Today") + ": " + CK.map(function (k, q) { return k[1] + " " + fmt(V[q][j2]); }).join(" · "); }
    function pick(e) { var b = cv.getBoundingClientRect(); at = Math.round(Math.max(0, Math.min(1, (e.clientX - b.left - geo.L) / (geo.R - geo.L))) * (geo.n - 1)); draw(); }
    cv.addEventListener("pointermove", pick); cv.addEventListener("pointerdown", pick); cv.addEventListener("pointerleave", function () { at = null; draw(); }); cv.addEventListener("blur", function () { at = null; draw(); });
    cv.addEventListener("keydown", function (e) { var dlt = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (!dlt) return; e.preventDefault(); at = Math.max(0, Math.min(geo.n - 1, (at == null ? geo.n - 1 : at) + dlt * (e.shiftKey ? 20 : 2))); draw(); });
    var go = function () { draw(); }; if (document.fonts && document.fonts.load) document.fonts.load("400 12px Inter").then(go, go); else go();
    if ("ResizeObserver" in window) new ResizeObserver(draw).observe(cp);
  })();

  // ---- the portfolio's control ----------------------------------------------------------------------------------
  var pm = document.querySelector(".pm");
  if (pm) (function () {
    var inp = pm.querySelector("input"), out = pm.querySelector("output"), pc = pm.querySelector(".pm__c"), KS = ["SPX", "BOND", "BTC"];
    function port(w) { var v = [100], hold = { SPX: 0.6 * (1 - w), BOND: 0.4 * (1 - w), BTC: w }, cur = { SPX: hold.SPX * 100, BOND: hold.BOND * 100, BTC: hold.BTC * 100 }, m = new Date(T[0]).getUTCMonth();
      for (var i = 1; i < N; i++) { var tot = 0; KS.forEach(function (k) { cur[k] *= 1 + R[k][i]; tot += cur[k]; }); v.push(tot); var m2 = new Date(T[i]).getUTCMonth(); if (m2 !== m) { m = m2; KS.forEach(function (k) { cur[k] = tot * hold[k]; }); } } return v; }
    function vol(p) { var r = [], m = 0; for (var i = 1; i < p.length; i++) { r.push(p[i] / p[i - 1] - 1); m += r[i - 1]; } m /= r.length; var s = 0; r.forEach(function (x) { s += (x - m) * (x - m); }); return Math.sqrt(s / (r.length - 1)) * Math.sqrt(252) * 100; }
    function deep(p) { var pk = p[0], w = 0; p.forEach(function (v) { if (v > pk) pk = v; w = Math.min(w, v / pk - 1); }); return w * 100; }
    function usd(v) { return "$" + Math.round(v * 100).toLocaleString("en-US"); }
    var base = port(0), bv = vol(base), bd = deep(base), $ = function (id) { return document.getElementById(id); };
    function mix() { var w = +inp.value / 100, p = w ? port(w) : base; inp.style.setProperty("--f", (w / 0.2 * 100) + "%"); out.textContent = inp.value + "%";
      $("pm-v").textContent = usd(p[N - 1]); $("pm-v2").textContent = "against " + usd(base[N - 1]) + " with none"; $("pm-s").textContent = vol(p).toFixed(1) + "%"; $("pm-s2").textContent = "against " + bv.toFixed(1) + "% with none";
      $("pm-d").innerHTML = '<span class="down">' + MIN + Math.abs(deep(p)).toFixed(0) + "%</span>"; $("pm-d2").textContent = "against " + MIN + Math.abs(bd).toFixed(0) + "% with none";
      var W = pm.clientWidth, narrow = W < 560, H = narrow ? 230 : 300; if (!W) return; pc.style.height = H + "px"; var c = canvas(pc, W, H), X0 = 44, X1 = W - (narrow ? 12 : 124), Tp = 12, B = H - 30, top = Math.max.apply(0, p) * 1.08, st = top > 1200 ? 500 : top > 600 ? 200 : 100, mx = Math.ceil(top / st) * st;
      function X(i) { return X0 + i / (N - 1) * (X1 - X0); } function Y(v) { return B - v / mx * (B - Tp); } c.font = "300 12px" + FONT;
      for (var g = 0; g <= mx; g += st) { c.strokeStyle = "rgba(255,255,255,.06)"; c.beginPath(); c.moveTo(X0, Y(g)); c.lineTo(X1, Y(g)); c.stroke(); c.fillStyle = "#74797c"; c.textAlign = "right"; c.fillText(String(g), X0 - 8, Y(g)); }
      var ya = new Date(T[0]).getUTCFullYear(), yb = new Date(T[N - 1]).getUTCFullYear(); for (var y = ya + 1; y <= yb; y++) { if ((y - ya + 1) % (narrow ? 4 : 2)) continue; var k = yearStart(y); c.fillStyle = "#a3a8aa"; c.textAlign = "center"; c.fillText(String(y), X(k), B + 18); }
      c.beginPath(); for (var i = 0; i < N; i += 2) i ? c.lineTo(X(i), Y(base[i])) : c.moveTo(X(i), Y(base[i])); c.strokeStyle = "rgba(242,243,243,.55)"; c.lineWidth = 1.1; c.stroke();
      if (w) glow(c, "255,176,72", 2, 1, function () { for (var i = 0; i < N; i += 2) i ? c.lineTo(X(i), Y(p[i])) : c.moveTo(X(i), Y(p[i])); c.lineTo(X(N - 1), Y(p[N - 1])); });
      if (!narrow) { var a = Y(p[N - 1]), b = Y(base[N - 1]); if (w && Math.abs(a - b) < 16) b = a + 16; c.textAlign = "left"; if (w) { c.font = "500 14px" + FONT; c.fillStyle = "#ffd99a"; c.fillText("With " + inp.value + "%  " + Math.round(p[N - 1]), X1 + 10, a); } c.font = "300 13px" + FONT; c.fillStyle = "#a3a8aa"; c.fillText("60/40  " + Math.round(base[N - 1]), X1 + 10, b); } }
    pm.hidden = false; inp.addEventListener("input", mix);
    var go = function () { mix(); }; if (document.fonts && document.fonts.load) document.fonts.load("300 12px Inter").then(go, go); else go();
    if ("ResizeObserver" in window) new ResizeObserver(mix).observe(pm);
  })();
})();
