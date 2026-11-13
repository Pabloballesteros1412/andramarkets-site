/* Risk & portfolio: the four tools as a map. Each tool is a knot of fine strands round a bright
   core; every pair is joined by a band of the same strands, with light travelling along it. The
   list of links is the page's own markup: this script lays its four links out over a canvas, and
   without it they stay a plain list. A knot can be dragged with a mouse or pen, and where it is
   left is kept in this browser (localStorage "andra-risk-map"); a double click puts them back.
   A press without a drag, or a tap, opens the tool. */
(function () {
  var map = document.querySelector(".tool-map"); if (!map) return;
  var items = map.querySelectorAll("li > a"); if (items.length !== 4) return;
  var cv = document.createElement("canvas"), cx = cv.getContext("2d"); if (!cx) return;
  cv.setAttribute("aria-hidden", "true"); map.insertBefore(cv, map.firstChild); map.classList.add("is-live");
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  // where each tool sits (share of the map's width and height), wide and narrow, and which side its words go
  var N = { pa: { w: [0.5, 0.2], n: [0.2, 0.1], r: 46 }, rc: { w: [0.17, 0.5], n: [0.2, 0.36], r: 32 }, ef: { w: [0.83, 0.5], n: [0.2, 0.61], r: 32 }, ps: { w: [0.5, 0.74], n: [0.2, 0.86], r: 32 } };
  for (var k0 in N) { N[k0].kn = []; }
  // every tool is joined to every other
  var E = [["rc", "pa"], ["ef", "pa"], ["ps", "pa"], ["rc", "ef"], ["rc", "ps"], ["ef", "ps"]];
  var seed = 5; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
  var K = 54; E.forEach(function (e) { e.st = []; for (var i = 0; i < K; i++) e.st.push({ a: rnd() - 0.5, b: rnd() - 0.5, c: (rnd() - 0.5) * (0.3 + rnd() * 0.9), ph: rnd() * 6.28, sp: 0.3 + rnd() * 0.6 }); });
  for (var k1 in N) for (var z0 = 0; z0 < 26; z0++) N[k1].kn.push({ tilt: rnd() * 3.14, sq: 0.25 + rnd() * 0.75, r: 0.55 + rnd() * 0.6, sp: (rnd() < 0.5 ? -1 : 1) * (0.2 + rnd() * 0.6), ph: rnd() * 6.28, len: 2.2 + rnd() * 3.4 });
  var DUST = []; for (var d0 = 0; d0 < 260; d0++) DUST.push({ x: rnd(), y: rnd(), s: 0.4 + rnd() * 1.3, a: 0.08 + rnd() * 0.3, v: 0.004 + rnd() * 0.012, ph: rnd() * 6.28 });
  var W = 0, H = 0, dpr = 1, narrow = false, pick = null, grab = null, t0 = 0, intro = still ? 1 : 0;
  var links = {}; ["pa", "rc", "ef", "ps"].forEach(function (k, i) { links[k] = items[i]; }); links.pa.classList.add("is-hub");
  var KEY = "andra-risk-map", saved = null; try { saved = JSON.parse(localStorage.getItem(KEY) || "null"); } catch (err) {}
  function size() {
    W = map.clientWidth; H = map.clientHeight; dpr = Math.min(window.devicePixelRatio || 1, 2); narrow = W < 720; cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
    var mode = narrow ? "n" : "w";
    for (var k in N) { var n = N[k], p = saved && saved[mode] && saved[mode][k] ? saved[mode][k] : n[mode]; n.fx = p[0]; n.fy = p[1]; n.rr = n.r * (narrow ? 0.8 : 1); }
    layout();
  }
  function layout() {
    var gx = 0, gy = 0, k; for (k in N) { var n = N[k]; n.x = n.fx * W; n.y = n.fy * H; gx += n.x / 4; gy += n.y / 4; }
    for (k in N) { var m = N[k], st = links[k].style; if (narrow) { st.left = (m.x + m.rr + 22) + "px"; st.right = "16px"; st.top = (m.y - 16) + "px"; st.textAlign = "left"; } else { st.left = (m.x - 110) + "px"; st.right = "auto"; st.top = (m.y + m.rr + 18) + "px"; st.textAlign = "center"; } }
    E.forEach(function (e, i) { var a = N[e[0]], b = N[e[1]], mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2, dx = b.x - a.x, dy = b.y - a.y, l = Math.hypot(dx, dy) || 1, ox = mx - gx, oy = my - gy, ol = Math.hypot(ox, oy);
      if (ol < l * 0.12) { ox = -dy / l * (i % 2 ? 1 : -1); oy = dx / l * (i % 2 ? 1 : -1); ol = 1; }
      e.c = [mx + ox / ol * l * 0.3, my + oy / ol * l * 0.3]; });
  }
  function qp(e, t) { var a = N[e[0]], b = N[e[1]], u = 1 - t; return [u * u * a.x + 2 * u * t * e.c[0] + t * t * b.x, u * u * a.y + 2 * u * t * e.c[1] + t * t * b.y]; }
  function glow(x, y, r, a) { var g = cx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, "rgba(255,255,255," + a + ")"); g.addColorStop(0.25, "rgba(215,230,255," + a * 0.45 + ")"); g.addColorStop(1, "rgba(180,210,255,0)"); cx.fillStyle = g; cx.fillRect(x - r, y - r, r * 2, r * 2); }
  function draw(time) {
    if (!t0) t0 = time; var t = (time - t0) / 1000; if (intro < 1) intro = Math.min(1, t / 1.8); var e0 = 1 - Math.pow(1 - intro, 3);
    cx.setTransform(dpr, 0, 0, dpr, 0, 0); cx.clearRect(0, 0, W, H); cx.globalCompositeOperation = "lighter";
    DUST.forEach(function (d) { var y = ((d.y - t * d.v) % 1 + 1) % 1; cx.fillStyle = "rgba(225,234,250," + (d.a * (0.6 + 0.4 * Math.sin(t + d.ph)) * e0).toFixed(3) + ")"; cx.fillRect(d.x * W, y * H, d.s, d.s); });
    E.forEach(function (e, i) {
      var on = !pick || e[0] === pick || e[1] === pick, A = N[e[0]], B = N[e[1]], dx = B.x - A.x, dy = B.y - A.y, l = Math.hypot(dx, dy) || 1, nx = -dy / l, ny = dx / l, base = (on ? (pick ? 0.3 : 0.17) : 0.03) * e0;
      cx.lineWidth = narrow ? 0.6 : 0.8;
      for (var q = 0; q < e.st.length * e0; q++) { var st = e.st[q], wob = still ? 0 : Math.sin(t * st.sp + st.ph) * 0.05, ax = A.x + nx * st.a * A.rr * 0.9, ay = A.y + ny * st.a * A.rr * 0.9, bx = B.x + nx * st.b * B.rr * 0.9, by = B.y + ny * st.b * B.rr * 0.9, c0 = e.c[0] + nx * (st.c + wob) * l * 0.42, c1 = e.c[1] + ny * (st.c + wob) * l * 0.42;
        cx.strokeStyle = "rgba(225,234,250," + (base * (0.5 + 0.5 * Math.abs(Math.sin(st.ph + t * 0.2)))).toFixed(3) + ")"; cx.beginPath(); cx.moveTo(ax, ay); cx.quadraticCurveTo(c0, c1, bx, by); cx.stroke(); }
      if (!still && on && intro >= 1) for (var u = 0; u < 3; u++) for (var s2 = 0; s2 < 12; s2++) { var f = ((t * (0.13 + u * 0.03) + i * 0.37 + u * 0.33) % 1) - s2 * 0.011; if (f < 0) continue; var p = qp(e, f); glow(p[0], p[1], (s2 ? 8 : 22) * (narrow ? 0.6 : 1), (1 - s2 / 12) * (s2 ? 0.5 : 1) * (pick ? 1 : 0.8)); }
    });
    for (var k in N) { var n = N[k], on = !pick || k === pick || E.some(function (e) { return (e[0] === pick && e[1] === k) || (e[1] === pick && e[0] === k); }), a = (on ? 1 : 0.35) * e0, beat = still ? 0.5 : 0.5 + 0.5 * Math.sin(t * 1.4 + n.x);
      var hot = k === pick || k === grab ? 1.5 : 1;
      glow(n.x, n.y, n.rr * (3.6 + 0.4 * beat), 0.34 * a * hot); glow(n.x, n.y, n.rr * 0.9, 0.85 * a);
      cx.lineWidth = 0.8; cx.lineCap = "round";
      n.kn.forEach(function (z) { var a0 = still ? z.ph : t * z.sp + z.ph, ct = Math.cos(z.tilt), sn = Math.sin(z.tilt), R = n.rr * z.r;
        cx.strokeStyle = "rgba(225,234,250," + (0.3 * a * hot * (0.5 + 0.5 * Math.abs(Math.sin(z.ph + t * 0.3)))).toFixed(3) + ")"; cx.beginPath();
        for (var w = 0; w <= 14; w++) { var q = a0 + w / 14 * z.len, ex = Math.cos(q) * R, ey = Math.sin(q) * R * z.sq, X = n.x + ex * ct - ey * sn, Y = n.y + ex * sn + ey * ct; if (w) cx.lineTo(X, Y); else cx.moveTo(X, Y); } cx.stroke(); }); }
    cx.globalCompositeOperation = "source-over";
  }
  var run = 0;
  var visible = true;
  function frame(time) { run = 0; draw(time); if (!still && visible) run = requestAnimationFrame(frame); }
  function once() { if (!run) run = requestAnimationFrame(frame); }
  function set(k) { pick = k; map.classList.toggle("has-pick", !!k); for (var q in links) links[q].classList.toggle("is-on", !k || q === k || E.some(function (e) { return (e[0] === k && e[1] === q) || (e[1] === k && e[0] === q); })); once(); }
  for (var k in links) (function (k) { var a = links[k]; a.addEventListener("pointerenter", function () { set(k); }); a.addEventListener("pointerleave", function () { set(null); }); a.addEventListener("focus", function () { set(k); }); a.addEventListener("blur", function () { set(null); }); })(k);
  function hit(x, y) { var b = null, bd = 1e9; for (var k in N) { var d = Math.hypot(N[k].x - x, N[k].y - y); if (d < Math.max(34, N[k].rr * 1.5) && d < bd) { bd = d; b = k; } } return b; }
  var moved = 0, sx = 0, sy = 0;
  cv.addEventListener("pointerdown", function (e) { var b = cv.getBoundingClientRect(), k = hit(e.clientX - b.left, e.clientY - b.top); if (!k) return; if (e.pointerType === "touch") { links[k].click(); return; } grab = k; moved = 0; sx = e.clientX; sy = e.clientY; cv.setPointerCapture(e.pointerId); cv.style.cursor = "grabbing"; e.preventDefault(); });
  cv.addEventListener("pointermove", function (e) { var b = cv.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top;
    if (grab) { moved = Math.max(moved, Math.hypot(e.clientX - sx, e.clientY - sy)); if (moved > 5) { var n = N[grab]; n.fx = Math.max(0.04, Math.min(0.96, x / W)); n.fy = Math.max(0.06, Math.min(0.9, y / H)); layout(); } once(); return; }
    var k = hit(x, y); cv.style.cursor = k ? "grab" : "default"; if (k !== pick) set(k); });
  cv.addEventListener("pointerup", function () { if (!grab) return; var k = grab; grab = null; cv.style.cursor = "grab";
    if (moved <= 5) { links[k].click(); return; } // a press without a drag opens the tool
    try { var all = JSON.parse(localStorage.getItem(KEY) || "{}") || {}, mode = narrow ? "n" : "w"; all[mode] = all[mode] || {}; for (var q in N) all[mode][q] = [N[q].fx, N[q].fy]; localStorage.setItem(KEY, JSON.stringify(all)); saved = all; } catch (err) {} once(); });
  cv.addEventListener("pointerleave", function () { if (!grab) set(null); });
  cv.addEventListener("dblclick", function () { try { localStorage.removeItem(KEY); } catch (err) {} saved = null; size(); once(); });
  window.addEventListener("resize", function () { size(); once(); });
  if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { visible = en[0].isIntersecting; if (visible) once(); }).observe(map);
  size(); once();
})();
