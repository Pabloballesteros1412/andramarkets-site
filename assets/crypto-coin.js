/* Crypto: a coin's page (owner, 27 Nov 2026: "analyse each coin, as in Companies"; the Ethereum sketch approved).
   assets/crypto-bitcoin.js draws its price and how far below its record; this script draws the rest from the JSON
   in the page: the coin against the other 99 on five measures (strips of hollow dots, the coin filled, the middle
   coin a dashed tick; pointing at a dot names it), its price in bitcoin, how closely it moves with Bitcoin, its
   volatility beside Bitcoin's, its network's activity where there is any, and how often each size of daily move has
   happened. Tables and figures are in the page without it. Red and green only on a signed move. */
(function () {
  "use strict";
  var src = document.getElementById("btc-data"); if (!src) return;
  var D; try { D = JSON.parse(src.textContent); } catch (e) { return; }
  var MIN = "−", DAY = 864e5, MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], dpr = Math.min(window.devicePixelRatio || 1, 2);
  function setup(el, h) { var cv = el.querySelector("canvas"); if (!cv) { cv = document.createElement("canvas"); cv.setAttribute("role", "img"); el.appendChild(cv); }
    var w = el.clientWidth; cv.style.width = "100%"; cv.style.height = h + "px"; cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
    var c = cv.getContext("2d"); c.setTransform(dpr, 0, 0, dpr, 0, 0); c.font = "400 12px Inter, 'Helvetica Neue', Arial, sans-serif"; c.textBaseline = "middle"; return { c: c, w: w, h: h, cv: cv, narrow: w < 520 }; }
  function sgn(v, d) { var r = Number(v.toFixed(d)); return (r > 0 ? "+" : r < 0 ? MIN : "") + Math.abs(r).toFixed(d); }
  function cls(v) { var r = Math.round(v * 10) / 10; return r > 0 ? "up" : r < 0 ? "down" : ""; }
  function kfmt(v) { return v >= 1e9 ? (v / 1e9).toFixed(v >= 1e10 ? 0 : 1) + "bn" : v >= 1e6 ? (v / 1e6).toFixed(v >= 1e7 ? 0 : 1) + "m" : v >= 1000 ? Math.round(v / 1000) + "k" : String(Math.round(v)); }
  function fmt(kind, v) { return kind === "btc" ? (v >= 1 ? v.toFixed(2) : v >= 0.01 ? v.toFixed(4) : v.toPrecision(2)) + " BTC" : kind === "ratio" ? v.toFixed(2) : kind === "pct" ? Math.round(v) + "%" : kfmt(v); }
  function tickFmt(kind, v) { return kind === "btc" ? (v >= 1 ? v.toFixed(1) : v >= 0.01 ? v.toFixed(3) : v.toPrecision(1)) : kind === "ratio" ? v.toFixed(1) : kind === "pct" ? Math.round(v) + "%" : kfmt(v); }
  function niceStep(span, n) { var raw = span / n, p = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / p; return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * p; }
  function day(t) { var d = new Date(t); return d.getUTCDate() + " " + MON[d.getUTCMonth()] + " " + d.getUTCFullYear(); }

  function line(el, ch, at) {
    var S = setup(el, el.getAttribute("data-chart") === "corr" ? 180 : 220), c = S.c, t0 = Date.parse(ch.t0), st = ch.step * DAY, L = S.narrow ? 46 : 58, R = S.w - (S.narrow ? 12 : 96), T = 10, B = S.h - 28;
    var n = 0, lo = Infinity, hi = -Infinity; ch.s.forEach(function (s) { n = Math.max(n, s.v.length); s.v.forEach(function (v) { if (v == null) return; if (v < lo) lo = v; if (v > hi) hi = v; }); });
    if (!isFinite(lo)) return; var y0 = ch.y0 != null ? ch.y0 : lo - (hi - lo) * 0.08, y1 = ch.y1 != null ? ch.y1 : hi + (hi - lo) * 0.08; if (y1 === y0) y1 = y0 + 1;
    function X(i) { return L + i / Math.max(1, n - 1) * (R - L); } function Y(v) { return B - (v - y0) / (y1 - y0) * (B - T); }
    var stp = niceStep(y1 - y0, 4); for (var t = Math.ceil(y0 / stp) * stp; t <= y1 + 1e-12; t += stp) { var y = Y(t); c.strokeStyle = "rgba(255,255,255,.07)"; c.beginPath(); c.moveTo(L, y); c.lineTo(R, y); c.stroke(); c.fillStyle = "#a3a8aa"; c.textAlign = "right"; c.fillText(tickFmt(ch.fmt, t), L - 8, y); }
    var ya = new Date(t0).getUTCFullYear(), yb = new Date(t0 + (n - 1) * st).getUTCFullYear(), every = yb - ya > 8 ? (S.narrow ? 4 : 2) : (S.narrow ? 2 : 1);
    for (var yr = ya + 1; yr <= yb; yr++) if ((yr - ya) % every === 0) { var xi = (Date.UTC(yr, 0, 1) - t0) / st; c.fillStyle = "#a3a8aa"; c.textAlign = "center"; c.fillText(String(yr), X(xi), B + 17); }
    if (yb === ya) { c.fillStyle = "#a3a8aa"; c.textAlign = "left"; c.fillText(day(t0), L, B + 17); }
    (ch.hl || []).forEach(function (h) { c.setLineDash([3, 4]); c.strokeStyle = "rgba(242,243,243,.35)"; c.beginPath(); c.moveTo(L, Y(h)); c.lineTo(R, Y(h)); c.stroke(); c.setLineDash([]); });
    var taken = [];
    ch.s.forEach(function (s, k) { c.beginPath(); var on = false; s.v.forEach(function (v, i) { if (v == null) { on = false; return; } var x = X(i), y = Y(v); on ? c.lineTo(x, y) : c.moveTo(x, y); on = true; });
      c.setLineDash(s.style === "dash" ? [5, 4] : []); c.strokeStyle = "rgba(242,243,243," + (s.alpha || 1) + ")"; c.lineWidth = s.style ? 1 : 1.3; c.stroke(); c.setLineDash([]);
      for (var j = s.v.length - 1; j >= 0; j--) if (s.v[j] != null) break; if (j < 0) return; var lx = X(j), ly = Y(s.v[j]);
      if (!s.style) { c.fillStyle = "#f2f3f3"; c.beginPath(); c.arc(lx, ly, 3, 0, 7); c.fill(); }
      if (!S.narrow) { var txt = (s.label === "now" ? "" : s.label + " ") + fmt(ch.fmt, s.v[j]); var by = ly; while (taken.some(function (q) { return Math.abs(q - by) < 14; })) by += 14; taken.push(by); c.fillStyle = s.style ? "#a3a8aa" : "#f2f3f3"; c.textAlign = "left"; c.fillText(txt, lx + 8, by); } });
    if (at != null) { var ax = X(at); c.strokeStyle = "rgba(242,243,243,.4)"; c.beginPath(); c.moveTo(ax, T); c.lineTo(ax, B); c.stroke(); }
    var i2 = at != null ? at : n - 1, words = ch.s.map(function (s) { var v = s.v[Math.min(i2, s.v.length - 1)]; return v == null ? null : (s.label === "now" ? "" : s.label + " ") + fmt(ch.fmt, v); }).filter(Boolean).join(" · ");
    var read = document.querySelector('[data-read="' + el.getAttribute("data-chart") + '"]'); if (read) read.textContent = (at != null ? day(t0 + i2 * st) : "Latest") + ": " + (el.getAttribute("data-name") ? el.getAttribute("data-name") + " " : "") + words;
    el._X = X; el._n = n; el._L = L; el._R = R;
  }
  function hist(el) {
    var S = setup(el, 200), c = S.c, b = D.bins || [], mx = Math.max.apply(0, b.concat([1])), L = 8, R = S.w - 8, T = 8, Bt = S.h - 26, w = (R - L) / 31;
    b.forEach(function (n, k) { var h = n / mx * (Bt - T), x = L + k * w; c.fillStyle = k < 15 ? "rgba(255,75,82,.75)" : "rgba(31,210,122,.75)"; c.fillRect(x + 1, Bt - h, Math.max(1, w - 2), h); });
    c.fillStyle = "#a3a8aa"; c.textAlign = "center"; [-15, -10, -5, 0, 5, 10, 15].forEach(function (v) { if (S.narrow && Math.abs(v) === 5) return; c.fillText((v > 0 ? "+" : v < 0 ? MIN : "") + Math.abs(v) + "%" + (Math.abs(v) === 15 ? "+" : ""), L + (v + 15.5) * w, Bt + 16); });
    S.cv.setAttribute("aria-label", "How often each size of daily move has happened, from 15% down to 15% up.");
  }
  // the coin against the other 99
  function peers() {
    var box = document.querySelector(".cc-peers"), P = D.peers; if (!box || !P) return;
    var read = document.querySelector(".cc-peers-read");
    box.innerHTML = P.m.map(function (m) { var v = m.v[P.me]; return '<div class="pe-row"><span>' + m.label + '</span><canvas data-k="' + m.k + '" aria-hidden="true"></canvas><span>' +
      (v == null ? '<span class="cs-none">' + (m.k === "issued" ? "No maximum" : "n/a") + "</span>" : m.move ? '<span class="' + cls(v) + '">' + sgn(v, 1) + "%</span>" : v.toFixed(1) + "%") + "</span></div>"; }).join("");
    [].forEach.call(box.querySelectorAll("canvas"), function (cv) {
      var m = P.m.filter(function (x) { return x.k === cv.getAttribute("data-k"); })[0], vals = m.v.filter(function (v) { return v != null; }).sort(function (a, b) { return a - b; }); if (vals.length < 5) return;
      var lo = vals[Math.floor(vals.length * 0.05)], hi = vals[Math.floor(vals.length * 0.95)], med = vals[Math.floor(vals.length / 2)], pts = [];
      function draw(hot) { var w = cv.clientWidth, h = 34; cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); var c = cv.getContext("2d"); c.setTransform(dpr, 0, 0, dpr, 0, 0); pts = [];
        function X(v) { return 6 + (Math.max(lo, Math.min(hi, v)) - lo) / ((hi - lo) || 1) * (w - 12); }
        c.strokeStyle = "rgba(255,255,255,.14)"; c.beginPath(); c.moveTo(6, 17); c.lineTo(w - 6, 17); c.stroke();
        m.v.forEach(function (v, i) { if (v == null || i === P.me) return; var x = X(v); pts.push([x, i]); c.strokeStyle = i === hot ? "#f2f3f3" : "rgba(116,121,124,.9)"; c.lineWidth = 1; c.beginPath(); c.arc(x, 17, i === hot ? 4.5 : 3.2, 0, 7); c.stroke(); });
        c.setLineDash([2, 3]); c.strokeStyle = "rgba(242,243,243,.6)"; c.beginPath(); c.moveTo(X(med), 6); c.lineTo(X(med), 28); c.stroke(); c.setLineDash([]);
        var mv = m.v[P.me]; if (mv != null) { c.fillStyle = "#f2f3f3"; c.beginPath(); c.arc(X(mv), 17, 5, 0, 7); c.fill(); } }
      draw(null); cv._draw = draw;
      cv.addEventListener("pointermove", function (e) { var b = cv.getBoundingClientRect(), x = e.clientX - b.left, best = null, bd = 8; pts.forEach(function (p) { var d = Math.abs(p[0] - x); if (d < bd) { bd = d; best = p[1]; } });
        draw(best); if (best != null && read) { var v = m.v[best]; read.innerHTML = P.names[best] + ", " + m.label.toLowerCase() + ": " + (m.move ? '<span class="' + cls(v) + '">' + sgn(v, 1) + "%</span>" : v.toFixed(1) + "%"); } });
      cv.addEventListener("pointerleave", function () { draw(null); if (read) read.textContent = ""; });
    });
  }
  var plots = [].slice.call(document.querySelectorAll(".cc-plot"));
  function all() { plots.forEach(function (el) { var k = el.getAttribute("data-chart"); if (k === "hist") hist(el); else if (D.charts && D.charts[k]) line(el, D.charts[k], el._at); });
    [].forEach.call(document.querySelectorAll(".cc-peers canvas"), function (cv) { if (cv._draw) cv._draw(null); }); }
  plots.forEach(function (el) { var k = el.getAttribute("data-chart"); if (k === "hist" || !D.charts || !D.charts[k]) return;
    el.addEventListener("pointermove", function (e) { var cv = el.querySelector("canvas"), b = cv.getBoundingClientRect(), x = e.clientX - b.left; if (!el._X) return;
      el._at = Math.round(Math.max(0, Math.min(1, (x - el._L) / (el._R - el._L))) * (el._n - 1)); line(el, D.charts[k], el._at); });
    el.addEventListener("pointerleave", function () { el._at = null; line(el, D.charts[k], null); }); });
  var go = function () { peers(); all(); };
  if (document.fonts && document.fonts.load) document.fonts.load("400 12px Inter").then(go, go); else go();
  if ("ResizeObserver" in window && plots[0]) new ResizeObserver(all).observe(plots[0].parentNode);
})();
