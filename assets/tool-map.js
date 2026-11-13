/* The Tools sections' pages: a section's tools as a map. Each tool is a knot of fine strands round
   a bright core; the tools are joined by bands of the same strands, with light travelling along
   them. The list of links is the page's own markup: this script lays its two, three or four links
   out over a canvas, and without it they stay a plain list. A knot can be dragged with a mouse or
   pen, and where it is left is kept in this browser (localStorage "andra-tool-map", by page); a
   double click puts them back. A press without a drag, or a tap, opens the tool. */
(function () {
  var map = document.querySelector(".tool-map"); if (!map) return;
  var items = map.querySelectorAll("li > a"), CNT = items.length; if (CNT < 2 || CNT > 4) return;
  var cv = document.createElement("canvas"), cx = cv.getContext("2d"); if (!cx) return;
  cv.setAttribute("aria-hidden", "true"); map.insertBefore(cv, map.firstChild); map.classList.add("is-live", "is-n" + CNT);
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  // where each tool sits (share of the map's width and height), wide and narrow, and which side its words go
  var N = CNT === 4 ? { pa: { w: [0.5, 0.2], n: [0.2, 0.1], r: 15 }, rc: { w: [0.17, 0.5], n: [0.2, 0.36], r: 11 }, ef: { w: [0.83, 0.5], n: [0.2, 0.61], r: 11 }, ps: { w: [0.5, 0.74], n: [0.2, 0.86], r: 11 } }
    : CNT === 3 ? { pa: { w: [0.5, 0.2], n: [0.2, 0.13], r: 12 }, rc: { w: [0.2, 0.64], n: [0.2, 0.47], r: 12 }, ef: { w: [0.8, 0.64], n: [0.2, 0.81], r: 12 } }
    : { pa: { w: [0.26, 0.46], n: [0.2, 0.2], r: 13 }, rc: { w: [0.74, 0.46], n: [0.2, 0.72], r: 13 } };
  for (var k0 in N) { N[k0].kn = []; N[k0].ph = k0.charCodeAt(0) * 1.7 + k0.charCodeAt(1); }
  // every tool is joined to every other
  var E = CNT === 4 ? [["rc", "pa"], ["ef", "pa"], ["ps", "pa"], ["rc", "ef"], ["rc", "ps"], ["ef", "ps"]] : CNT === 3 ? [["rc", "pa"], ["ef", "pa"], ["rc", "ef"]] : [["rc", "pa"], ["rc", "pa"]]; // two tools are joined twice, above and below
  var seed = 5; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
  var K = 120; E.forEach(function (e) { e.st = []; for (var i = 0; i < K; i++) e.st.push({ r: Math.sqrt(rnd()), tw: (rnd() - 0.5) * 1.4, ph: rnd() * 6.28, sp: 0.5 + rnd() * 0.7 }); });
  for (var k1 in N) for (var z0 = 0; z0 < 9; z0++) N[k1].kn.push({ tilt: rnd() * 3.14, sq: 0.25 + rnd() * 0.75, r: 0.55 + rnd() * 0.6, sp: (rnd() < 0.5 ? -1 : 1) * (0.2 + rnd() * 0.6), ph: rnd() * 6.28, len: 2.2 + rnd() * 3.4 });
  var DUST = []; for (var d0 = 0; d0 < 260; d0++) DUST.push({ x: rnd(), y: rnd(), s: 0.4 + rnd() * 1.3, a: 0.08 + rnd() * 0.3, v: 0.004 + rnd() * 0.012, ph: rnd() * 6.28 });
  var W = 0, H = 0, dpr = 1, narrow = false, pick = null, grab = null, px = -1, py = -1, t0 = 0, intro = still ? 1 : 0;
  var links = {}; ["pa", "rc", "ef", "ps"].slice(0, CNT).forEach(function (k, i) { links[k] = items[i]; }); if (CNT === 4) links.pa.classList.add("is-hub");
  var KEY = "andra-tool-map", PAGE = map.getAttribute("data-page") || "tools", saved = null;
  try { localStorage.removeItem("andra-risk-map"); saved = (JSON.parse(localStorage.getItem(KEY) || "{}") || {})[PAGE] || null; } catch (err) {}
  function size() {
    W = map.clientWidth; H = map.clientHeight; dpr = Math.min(window.devicePixelRatio || 1, 2); narrow = W < 720; cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
    var mode = narrow ? "n" : "w";
    for (var k in N) { var n = N[k], p = saved && saved[mode] && saved[mode][k] ? saved[mode][k] : n[mode]; n.fx = p[0]; n.fy = p[1]; n.rr = n.r * (narrow ? 0.85 : 1); }
    layout();
  }
  function layout() {
    var gx = 0, gy = 0, k; for (k in N) { var n = N[k]; n.x = n.fx * W; n.y = n.fy * H; gx += n.x / CNT; gy += n.y / CNT; }
    for (k in N) { var m = N[k], st = links[k].style; if (narrow) { st.left = (m.x + 34) + "px"; st.right = "16px"; st.top = (m.y - 12) + "px"; st.textAlign = "left"; } else { st.left = (m.x - 110) + "px"; st.right = "auto"; st.top = (m.y + 34) + "px"; st.textAlign = "center"; } }
    E.forEach(function (e, i) { var a = N[e[0]], b = N[e[1]], mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2, dx = b.x - a.x, dy = b.y - a.y, l = Math.hypot(dx, dy) || 1, ox = mx - gx, oy = my - gy, ol = Math.hypot(ox, oy);
      if (ol < l * 0.04) { ox = -dy / l * (i % 2 ? 1 : -1); oy = dx / l * (i % 2 ? 1 : -1); ol = 1; if (narrow && CNT === 2) { ox = i % 2 ? 0.25 : -1; oy = 0; ol = 1; } }
      e.c = [mx + ox / ol * l * 0.3, my + oy / ol * l * 0.3]; });
  }
  function qp(e, t) { var a = N[e[0]], b = N[e[1]], u = 1 - t; return [u * u * a.x + 2 * u * t * e.c[0] + t * t * b.x, u * u * a.y + 2 * u * t * e.c[1] + t * t * b.y]; }
  function cp(e, t) { var A = N[e[0]], B = N[e[1]], u = 1 - t, p1 = e.p1 || e.c, p2 = e.p2 || e.c; return [u * u * u * A.vx + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * B.vx, u * u * u * A.vy + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * B.vy]; }
  function glow(x, y, r, a) { var g = cx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, "rgba(255,255,255," + a + ")"); g.addColorStop(0.25, "rgba(215,230,255," + a * 0.45 + ")"); g.addColorStop(1, "rgba(180,210,255,0)"); cx.fillStyle = g; cx.fillRect(x - r, y - r, r * 2, r * 2); }
  function draw(time) {
    if (!t0) t0 = time; var t = (time - t0) / 1000; if (intro < 1) intro = Math.min(1, t / 1.8); var e0 = 1 - Math.pow(1 - intro, 3);
    cx.setTransform(dpr, 0, 0, dpr, 0, 0); cx.clearRect(0, 0, W, H); cx.globalCompositeOperation = "lighter";
    DUST.forEach(function (d) { var y = ((d.y - t * d.v) % 1 + 1) % 1; cx.fillStyle = "rgba(225,234,250," + (d.a * (0.6 + 0.4 * Math.sin(t + d.ph)) * e0).toFixed(3) + ")"; cx.fillRect(d.x * W, y * H, d.s, d.s); });
    // each knot drifts a little, and leans away from the pointer
    for (var k2 in N) { var m = N[k2], fl = still || k2 === grab ? 0 : 1; m.vx = m.x + Math.sin(t * 0.42 + m.ph) * 5 * fl + (px > -1 ? (m.x - px) * 0.012 * fl : 0); m.vy = m.y + Math.cos(t * 0.36 + m.ph * 1.7) * 5 * fl + (px > -1 ? (m.y - py) * 0.012 * fl : 0); }
    E.forEach(function (e, i) {
      var on = !pick || e[0] === pick || e[1] === pick, A = N[e[0]], B = N[e[1]], dx = B.vx - A.vx, dy = B.vy - A.vy, l = Math.hypot(dx, dy) || 1, nx = -dy / l, ny = dx / l, base = (on ? (pick ? 0.34 : 0.2) : 0.035) * e0;
      // the band as a cubic through its bend, so its strands can cross over between the two thirds: a twisted rope, turning
      var q1x = A.vx + (e.c[0] - A.x) * 2 / 3, q1y = A.vy + (e.c[1] - A.y) * 2 / 3, q2x = B.vx + (e.c[0] - B.x) * 2 / 3, q2y = B.vy + (e.c[1] - B.y) * 2 / 3, wide = Math.min(l * 0.1, narrow ? 34 : 64);
      function push(x, y) { if (px < 0) return [x, y]; var ddx = x - px, ddy = y - py, d = Math.hypot(ddx, ddy) || 1, f = Math.max(0, 1 - d / 190); f = f * f * 52; return [x + ddx / d * f, y + ddy / d * f]; }
      var p1 = push(q1x, q1y), p2 = push(q2x, q2y);
      cx.lineWidth = narrow ? 0.45 : 0.55;
      for (var q = 0; q < e.st.length * e0; q++) { var st = e.st[q], th = st.ph + (still ? 0 : t * st.sp * 0.5), o1 = wide * st.r * Math.sin(th), o2 = wide * st.r * Math.sin(th + 2.6 + st.tw), dep = 0.5 + 0.5 * Math.cos(th);
        cx.strokeStyle = "rgba(226,236,252," + (base * (0.3 + 0.7 * dep)).toFixed(3) + ")"; cx.beginPath(); cx.moveTo(A.vx, A.vy); cx.bezierCurveTo(p1[0] + nx * o1, p1[1] + ny * o1, p2[0] + nx * o2, p2[1] + ny * o2, B.vx, B.vy); cx.stroke(); }
      e.p1 = p1; e.p2 = p2;
      // light along the band, both ways, each a head with a long tail
      if (!still && on && intro >= 1) for (var u = 0; u < 4; u++) { var f = (t * (0.1 + u * 0.022) + i * 0.37 + u * 0.27) % 1, back = u % 2; cx.lineCap = "round";
        for (var s2 = 0; s2 < 14; s2++) { var f0 = f - s2 * 0.009, f1 = f - (s2 + 1) * 0.009; if (f1 < 0) break; var a0 = cp(e, back ? 1 - f0 : f0), a1 = cp(e, back ? 1 - f1 : f1); cx.strokeStyle = "rgba(240,246,255," + ((1 - s2 / 14) * 0.85 * (pick ? 1 : 0.8)).toFixed(3) + ")"; cx.lineWidth = 1.9 * (1 - s2 / 16); cx.beginPath(); cx.moveTo(a0[0], a0[1]); cx.lineTo(a1[0], a1[1]); cx.stroke(); }
        var hd = cp(e, back ? 1 - f : f); glow(hd[0], hd[1], narrow ? 9 : 15, 0.95); }
    });
    // each knot: a point of light with a flare, and a few fine orbits
    for (var k in N) { var n = N[k], on = !pick || k === pick || E.some(function (e) { return (e[0] === pick && e[1] === k) || (e[1] === pick && e[0] === k); }), a = (on ? 1 : 0.35) * e0, beat = still ? 0.5 : 0.5 + 0.5 * Math.sin(t * 1.3 + n.ph * 3);
      var hot = k === pick || k === grab ? 1.45 : 1, X = n.vx, Y = n.vy, R = n.rr;
      glow(X, Y, R * (4.2 + 0.6 * beat) * hot, 0.26 * a); glow(X, Y, R * 1.1, 0.9 * a); glow(X, Y, R * 0.42, a);
      var rot = still ? 0.3 : t * 0.07 + n.ph;
      for (var r0 = 0; r0 < 6; r0++) { var ang = rot + r0 * Math.PI / 3, len = R * (r0 % 3 === 0 ? 4.6 + 1.2 * beat : 2.1 + 0.5 * beat) * hot, ex = X + Math.cos(ang) * len, ey = Y + Math.sin(ang) * len, g = cx.createLinearGradient(X, Y, ex, ey);
        g.addColorStop(0, "rgba(255,255,255," + (0.85 * a).toFixed(3) + ")"); g.addColorStop(0.3, "rgba(215,230,255," + (0.3 * a).toFixed(3) + ")"); g.addColorStop(1, "rgba(200,220,255,0)"); cx.strokeStyle = g; cx.lineWidth = r0 % 3 === 0 ? 1.1 : 0.7; cx.beginPath(); cx.moveTo(X, Y); cx.lineTo(ex, ey); cx.stroke(); }
      cx.lineWidth = 0.5;
      n.kn.forEach(function (z) { var a0 = still ? z.ph : t * z.sp + z.ph, ct = Math.cos(z.tilt), sn = Math.sin(z.tilt), RR = R * (0.9 + z.r);
        cx.strokeStyle = "rgba(225,234,250," + (0.34 * a * hot * (0.4 + 0.6 * Math.abs(Math.sin(z.ph + t * 0.3)))).toFixed(3) + ")"; cx.beginPath();
        for (var w = 0; w <= 18; w++) { var qq = a0 + w / 18 * z.len, ox = Math.cos(qq) * RR, oy = Math.sin(qq) * RR * z.sq, x2 = X + ox * ct - oy * sn, y2 = Y + ox * sn + oy * ct; if (w) cx.lineTo(x2, y2); else cx.moveTo(x2, y2); } cx.stroke(); }); }
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
  cv.addEventListener("pointermove", function (e) { var b = cv.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top; if (e.pointerType !== "touch") { px = x; py = y; }
    if (grab) { moved = Math.max(moved, Math.hypot(e.clientX - sx, e.clientY - sy)); if (moved > 5) { var n = N[grab]; n.fx = Math.max(0.04, Math.min(0.96, x / W)); n.fy = Math.max(0.06, Math.min(0.9, y / H)); layout(); } once(); return; }
    var k = hit(x, y); cv.style.cursor = k ? "grab" : "default"; if (k !== pick) set(k); });
  cv.addEventListener("pointerup", function () { if (!grab) return; var k = grab; grab = null; cv.style.cursor = "grab";
    if (moved <= 5) { links[k].click(); return; } // a press without a drag opens the tool
    try { var all = JSON.parse(localStorage.getItem(KEY) || "{}") || {}, mine = all[PAGE] || {}, mode = narrow ? "n" : "w"; mine[mode] = mine[mode] || {}; for (var q in N) mine[mode][q] = [+N[q].fx.toFixed(4), +N[q].fy.toFixed(4)]; all[PAGE] = mine; localStorage.setItem(KEY, JSON.stringify(all)); saved = mine; } catch (err) {} once(); });
  cv.addEventListener("pointerleave", function () { px = py = -1; if (!grab) set(null); });
  cv.addEventListener("dblclick", function () { try { var all = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; delete all[PAGE]; localStorage.setItem(KEY, JSON.stringify(all)); } catch (err) {} saved = null; size(); once(); });
  window.addEventListener("resize", function () { size(); once(); });
  if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { visible = en[0].isIntersecting; if (visible) once(); }).observe(map);
  size(); once();
})();
