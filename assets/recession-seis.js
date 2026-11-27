/* Recession watch: the five indicators as a seismograph of light (owner, 24 Nov 2026). Each indicator is one
   line across the screen, its own history since 1970 (or its first observation), drawn in the maps' stroke;
   the NBER recessions are bands that cross all five; at the right, today: a point of light on each line and
   its latest reading. The page's own figures are the source: the series come from #rw-data (the same the
   charts below draw) and the readings from the table. Pointing shows the date and each line's value there;
   a press on a line goes to its chart. It makes no call: every line is scaled to its own range, nothing more. */
(function () {
  "use strict";
  var box = document.querySelector(".rw-seis"), el = document.getElementById("rw-data"); if (!box || !el) return;
  var D; try { D = JSON.parse(el.textContent); } catch (err) { return; }
  var cv = box.querySelector("canvas"), cx = cv && cv.getContext("2d"), names = box.querySelector(".rw-seis__names"); if (!cx || !names) return;
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var KEYS = ["curve", "sahm", "claims", "baa", "nfci"], MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  function day(s) { return Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10)) / 864e5; }
  function minus(s) { return s.replace("-", "−"); }
  var FMT = { curve: function (v) { return minus(v.toFixed(0)) + " bp"; }, sahm: function (v) { return minus(v.toFixed(2)) + " pp"; }, claims: function (v) { return Math.round(v).toLocaleString("en-US") + "k"; },
    baa: function (v) { return minus(v.toFixed(0)) + " bp"; }, nfci: function (v) { return minus(v.toFixed(2)); } };
  // the lines, from the page's own data; the names and latest readings, from its table
  var T = []; KEYS.forEach(function (k) { var b = D[k]; if (!b || !b.dates || !b.dates.length) return; var vals = b.values || (b.series && b.series[0] && b.series[0].values); if (!vals) return;
    var a = document.querySelector('.rw-tab a.rw-name[href="#rw-' + k + '"]'), row = a && a.closest("tr"), fig = row && row.querySelector(".cb-fig");
    var t = { k: k, name: a ? a.textContent : k, now: fig ? fig.textContent : FMT[k](vals[vals.length - 1]), d: b.dates.map(day), v: vals, log: k === "claims", ref: k === "sahm" ? (b.trigger || 0.5) : k === "curve" || k === "nfci" ? 0 : null };
    var lo = Infinity, hi = -Infinity; vals.forEach(function (x) { var y = t.log ? Math.log(x) : x; if (y < lo) lo = y; if (y > hi) hi = y; }); if (t.ref != null) { lo = Math.min(lo, t.ref); hi = Math.max(hi, t.ref); } t.lo = lo; t.hi = hi;
    t.elName = document.createElement("span"); t.elName.className = "rw-seis__name"; t.elName.textContent = t.name; names.appendChild(t.elName);
    t.elNow = document.createElement("span"); t.elNow.className = "rw-seis__now"; t.elNow.textContent = t.now; names.appendChild(t.elNow); T.push(t); });
  if (T.length < 2) return;
  var REC = (D.rec || []).map(function (p) { return [day(p[0]), day(p[1]), p[0].slice(2, 4) === p[1].slice(2, 4) ? p[0].slice(0, 4) : p[0].slice(0, 4) + "–" + p[1].slice(2, 4)]; });
  var D0 = day("1970-01-01"), D1 = D0; T.forEach(function (t) { D1 = Math.max(D1, t.d[t.d.length - 1]); });
  box.hidden = false; var page = box.closest(".rw"); if (page) page.classList.add("has-seis");
  var W, H, dpr, narrow, X0, X1, Y0, Y1, TH, px = -1, py = -1, run = 0, visible = true, t0 = performance.now();
  function xOf(d) { return X0 + (d - D0) / (D1 - D0) * (X1 - X0); }
  function size() {
    narrow = box.clientWidth < 900; box.style.height = narrow ? (T.length * 92 + 86) + "px" : "";
    W = box.clientWidth; H = box.clientHeight; dpr = Math.min(window.devicePixelRatio || 1, 2); cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
    var head = page && page.querySelector(".page__title"), top = 24; if (!narrow && head) top = Math.max(24, head.getBoundingClientRect().bottom - box.getBoundingClientRect().top + 44);
    var side = Math.max(0, (W - 1328) / 2) + (W > 1440 ? 0 : 56); if (narrow) side = 16;
    X0 = side + (narrow ? 0 : 150); X1 = W - side - (narrow ? 0 : 118); Y0 = top; Y1 = H - (narrow ? 44 : 86); TH = (Y1 - Y0) / T.length;
    T.forEach(function (t, i) { var a = Y0 + TH * i, pad = narrow ? 26 : TH * 0.16; t.y0 = a + pad; t.y1 = a + TH - (narrow ? 8 : TH * 0.12);
      // one point for each pixel across, keeping the highest and lowest reading in it so no spike is lost
      var n = Math.max(2, Math.round(X1 - X0)), mn = new Float32Array(n + 1), mx = new Float32Array(n + 1), has = new Uint8Array(n + 1), j, k;
      for (j = 0; j < t.d.length; j++) { k = Math.round((t.d[j] - D0) / (D1 - D0) * n); if (k < 0 || k > n) continue; var y = yOf(t, t.v[j]); if (!has[k]) { has[k] = 1; mn[k] = mx[k] = y; } else { if (y < mn[k]) mn[k] = y; if (y > mx[k]) mx[k] = y; } }
      t.n = n; t.mn = mn; t.mx = mx; t.has = has; t.first = 0; while (t.first < n && !has[t.first]) t.first++; var lastY = mn[t.first]; for (k = t.first; k <= n; k++) { if (!has[k]) { mn[k] = mx[k] = lastY; } else lastY = (mn[k] + mx[k]) / 2; }
      t.xl = xOf(t.d[t.d.length - 1]); t.yl = yOf(t, t.v[t.v.length - 1]);
      var s = t.elName.style, s2 = t.elNow.style; if (narrow) { s.left = X0 + "px"; s.top = (a + 4) + "px"; s.transform = "none"; s2.left = "auto"; s2.right = (W - X1) + "px"; s2.top = (a + 4) + "px"; s2.transform = "none"; }
      else { s.left = (X0 - 150) + "px"; s.top = ((t.y0 + t.y1) / 2) + "px"; s.transform = "translateY(-50%)"; s2.right = "auto"; s2.left = (X1 + 22) + "px"; s2.top = t.yl + "px"; s2.transform = "translateY(-50%)"; } });
  }
  function yOf(t, v) { var y = t.log ? Math.log(v) : v; return t.y1 - (y - t.lo) / ((t.hi - t.lo) || 1) * (t.y1 - t.y0); }
  function glow(x, y, r, a) { var g = cx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, "rgba(255,255,255," + a + ")"); g.addColorStop(0.25, "rgba(215,230,255," + a * 0.45 + ")"); g.addColorStop(1, "rgba(190,215,255,0)"); cx.fillStyle = g; cx.fillRect(x - r, y - r, r * 2, r * 2); }
  function path(t, off, upto) { cx.beginPath(); var k, n = Math.min(t.n, upto == null ? t.n : upto), up = true; cx.moveTo(X0 + t.first, t.mn[t.first] + off);
    for (k = t.first; k <= n; k++) { var x = X0 + k; if (t.mx[k] - t.mn[k] > 1.2) { if (up) { cx.lineTo(x, t.mx[k] + off); cx.lineTo(x, t.mn[k] + off); } else { cx.lineTo(x, t.mn[k] + off); cx.lineTo(x, t.mx[k] + off); } up = !up; } else cx.lineTo(x, (t.mn[k] + t.mx[k]) / 2 + off); } }
  function text(s, x, y, a, al, size) { cx.font = "300 " + ((size || 11) + 1) + "px Geist,'Helvetica Neue',Arial,sans-serif"; cx.textAlign = al || "left"; cx.textBaseline = "middle"; cx.fillStyle = "rgba(226,236,252," + a + ")"; cx.fillText(s, x, y); }
  function draw(now) {
    var t = still ? 6 : (now - t0) / 1000, e0 = still ? 1 : Math.min(1, t / 2.2), ease = 1 - Math.pow(1 - e0, 3);
    cx.setTransform(dpr, 0, 0, dpr, 0, 0); cx.clearRect(0, 0, W, H); cx.globalCompositeOperation = "lighter";
    var lastR = -99; REC.forEach(function (r) { var a = Math.max(X0, xOf(r[0])), b = Math.min(X1, xOf(r[1])); if (b <= a) return; var g = cx.createLinearGradient(0, Y0, 0, Y1 + 10); g.addColorStop(0, "rgba(190,215,255,0)"); g.addColorStop(0.12, "rgba(200,220,255,0.14)"); g.addColorStop(0.9, "rgba(200,220,255,0.14)"); g.addColorStop(1, "rgba(190,215,255,0)");
      cx.fillStyle = g; cx.fillRect(a, Y0 - 6, Math.max(1.5, b - a), Y1 - Y0 + 16); var mid = (a + b) / 2, low = mid - lastR < (narrow ? 34 : 52); if (!narrow || !low) { text(r[2], mid, Y1 + (low ? 36 : 22), 0.5, "center", 10); } lastR = low ? lastR : mid; }); // two close together: the second a line lower
    text(String(new Date(D1 * 864e5).getUTCFullYear()), X1, Y1 + 22, 0.5, narrow ? "right" : "center", 10);
    T.forEach(function (tr, i) {
      if (tr.ref != null) { var yr2 = yOf(tr, tr.ref); cx.setLineDash([2, 5]); cx.strokeStyle = "rgba(226,236,252,0.26)"; cx.lineWidth = 1; cx.beginPath(); cx.moveTo(X0, yr2); cx.lineTo(X1, yr2); cx.stroke(); cx.setLineDash([]); if (!narrow) text(tr.k === "sahm" ? "0.50" : "0", X0 - 8, yr2, 0.38, "right", 10); }
      var upto = Math.round(tr.first + (tr.n - tr.first) * ease); cx.lineJoin = "round";
      cx.strokeStyle = "rgba(200,220,255,0.05)"; cx.lineWidth = 7; path(tr, 0, upto); cx.stroke();
      cx.strokeStyle = "rgba(226,236,252,0.16)"; cx.lineWidth = 0.6; path(tr, -1.6, upto); cx.stroke(); path(tr, 1.6, upto); cx.stroke();
      cx.strokeStyle = "rgba(240,246,255,0.88)"; cx.lineWidth = 1.05; path(tr, 0, upto); cx.stroke();
      if (!still && e0 >= 1) { var f = (t * 0.045 + i * 0.21) % 1, k = Math.round(tr.first + (tr.n - tr.first) * f); glow(X0 + k, (tr.mn[k] + tr.mx[k]) / 2, 11, 0.7); }
      if (e0 >= 1) { var beat = still ? 0.5 : 0.5 + 0.5 * Math.sin(t * 1.3 + i); glow(tr.xl, tr.yl, 22 + 4 * beat, 0.3); glow(tr.xl, tr.yl, 6, 0.95);
        for (var r0 = 0; r0 < 4; r0++) { var ang = 0.3 + r0 * 1.5708 + (still ? 0 : t * 0.07), len = (r0 % 2 ? 9 : 17) + 3 * beat, g2 = cx.createLinearGradient(tr.xl, tr.yl, tr.xl + Math.cos(ang) * len, tr.yl + Math.sin(ang) * len); g2.addColorStop(0, "rgba(255,255,255,0.85)"); g2.addColorStop(1, "rgba(190,215,255,0)"); cx.strokeStyle = g2; cx.lineWidth = 0.8; cx.beginPath(); cx.moveTo(tr.xl, tr.yl); cx.lineTo(tr.xl + Math.cos(ang) * len, tr.yl + Math.sin(ang) * len); cx.stroke(); } } });
    if (px >= X0 && px <= X1 && py >= Y0 - 10 && py <= Y1 + 10) { // the reading under the pointer, on every line
      var d = D0 + (px - X0) / (X1 - X0) * (D1 - D0), dt = new Date(d * 864e5), flip = px > X1 - 150; cx.strokeStyle = "rgba(226,236,252,0.4)"; cx.lineWidth = 1; cx.beginPath(); cx.moveTo(px, Y0 - 6); cx.lineTo(px, Y1 + 10); cx.stroke();
      text(dt.getUTCDate() + " " + MON[dt.getUTCMonth()] + " " + dt.getUTCFullYear(), px + (flip ? -8 : 8), Y0 - 14, 0.9, flip ? "right" : "left", 11);
      T.forEach(function (tr) { var lo = 0, hi = tr.d.length - 1; if (d < tr.d[0] - 20 || d > tr.d[hi] + 20) return; while (lo < hi) { var m = (lo + hi) >> 1; if (tr.d[m] < d) lo = m + 1; else hi = m; } if (lo > 0 && d - tr.d[lo - 1] < tr.d[lo] - d) lo--;
        var y = yOf(tr, tr.v[lo]); glow(px, y, 9, 0.9); cx.globalCompositeOperation = "source-over"; var s = FMT[tr.k](tr.v[lo]); cx.font = "300 12px Geist,'Helvetica Neue',Arial,sans-serif"; var w = cx.measureText(s).width + 10; cx.fillStyle = "rgba(0,0,0,0.72)"; cx.fillRect(flip ? px - 10 - w : px + 10, y - 20, w, 16); cx.globalCompositeOperation = "lighter"; text(s, px + (flip ? -15 : 15), y - 12, 0.95, flip ? "right" : "left", 11); }); }
    return e0 < 1;
  }
  function frame(now) { run = 0; var more = draw(now); if ((more || !still) && visible) run = requestAnimationFrame(frame); }
  function once() { if (!run) run = requestAnimationFrame(frame); }
  function at(e) { var b = box.getBoundingClientRect(); px = e.clientX - b.left; py = e.clientY - b.top; }
  function track() { if (px < X0 - 150 || px > X1 + 118 || py < Y0 || py > Y1) return null; return T[Math.min(T.length - 1, Math.floor((py - Y0) / TH))]; }
  cv.addEventListener("pointermove", function (e) { at(e); cv.style.cursor = track() ? "pointer" : ""; once(); });
  cv.addEventListener("pointerleave", function () { px = py = -1; once(); });
  cv.addEventListener("click", function (e) { at(e); var tr = track(), to = tr && document.getElementById("rw-" + tr.k); if (to) to.scrollIntoView({ behavior: still ? "auto" : "smooth", block: "start" }); });
  window.addEventListener("resize", function () { size(); once(); });
  if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { visible = en[0].isIntersecting; if (visible) once(); }).observe(box);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { size(); once(); });
  size(); once();
})();
