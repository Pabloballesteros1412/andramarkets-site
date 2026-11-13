/* Tools: every section and its tools on one map. A section is a knot of light; the six are joined
   in a ring by ropes of fine strands, and each section's tools hang off it as smaller knots on
   shorter ropes, with light travelling along all of them. The nested list of links is the page's
   own markup: this script lays it out over a canvas, and without it the list stays a list. A
   section can be dragged with a mouse or pen, its tools with it; where it is left is kept in this
   browser (localStorage "andra-tool-map", under "all"); a double click puts them back. A press on
   a tool's knot, or its name, opens the tool. On a narrow screen the same map is drawn whole, small,
   and two fingers enlarge it; once enlarged, one finger moves it. */
(function () {
  var map = document.querySelector(".tools-map"); if (!map) return;
  var groups = [].slice.call(map.querySelectorAll(":scope > ol > li")); if (groups.length < 2) return;
  var cv = document.createElement("canvas"), cx = cv.getContext("2d"); if (!cx) return;
  cv.setAttribute("aria-hidden", "true"); map.insertBefore(cv, map.firstChild); map.classList.add("is-live");
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var seed = 9; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
  function strands(n) { var a = []; for (var i = 0; i < n; i++) a.push({ r: Math.sqrt(rnd()), tw: (rnd() - 0.5) * 1.4, ph: rnd() * 6.28, sp: 0.5 + rnd() * 0.7 }); return a; }
  function orbits(n) { var a = []; for (var i = 0; i < n; i++) a.push({ tilt: rnd() * 3.14, sq: 0.25 + rnd() * 0.75, r: 0.55 + rnd() * 0.6, sp: (rnd() < 0.5 ? -1 : 1) * (0.2 + rnd() * 0.6), ph: rnd() * 6.28, len: 2.2 + rnd() * 3.4 }); return a; }
  // the knots: sections, and each section's tools
  var G = groups.map(function (li, i) {
    var g = { i: i, el: li.querySelector(":scope > .tools-map__name"), r: 13, ph: rnd() * 6.28, kn: orbits(8), tools: [] };
    [].forEach.call(li.querySelectorAll("ol > li > a"), function (a, j) { g.tools.push({ g: g, j: j, el: a, r: 6.5, ph: rnd() * 6.28, kn: orbits(4), st: strands(26) }); });
    return g;
  });
  var NG = G.length, RING = G.map(function (g, i) { return { a: g, b: G[(i + 1) % NG], st: strands(84) }; });
  var ALL = []; G.forEach(function (g) { ALL.push(g); g.tools.forEach(function (t) { ALL.push(t); }); });
  var DUST = []; for (var d0 = 0; d0 < 280; d0++) DUST.push({ x: rnd(), y: rnd(), s: 0.4 + rnd() * 1.3, a: 0.08 + rnd() * 0.3, v: 0.004 + rnd() * 0.012, ph: rnd() * 6.28 });
  var W = 0, H = 0, CW = 0, CH = 0, Z = 1, Z0 = 1, OX = 0, OY = 0, VW = 1040, VH = 1100, list = map.querySelector(":scope > ol"), dpr = 1, narrow = false, pick = null, grab = null, px = -1, py = -1, t0 = 0, intro = still ? 1 : 0;
  var KEY = "andra-tool-map", saved = null; try { saved = (JSON.parse(localStorage.getItem(KEY) || "{}") || {}).all || null; } catch (err) {}
  function view() { // the list of names is moved and scaled with the picture
    if (narrow) { Z = Math.max(Z0, Math.min(Z0 * 4.5, Z)); OX = Math.min(0, Math.max(CW - VW * Z, OX)); OY = Math.min(0, Math.max(CH - VH * Z, OY)); }
    list.style.width = W + "px"; list.style.height = H + "px"; list.style.transform = narrow ? "translate(" + OX + "px," + OY + "px) scale(" + Z + ")" : "none";
    map.classList.toggle("is-zoom", narrow && Z > Z0 * 1.03);
  }
  function size() {
    narrow = map.clientWidth < 900;
    if (narrow) { Z0 = map.clientWidth / VW; map.style.height = Math.round(VH * Z0) + "px"; } else map.style.height = "";
    CW = map.clientWidth; CH = map.clientHeight; dpr = Math.min(window.devicePixelRatio || 1, 2); cv.width = Math.round(CW * dpr); cv.height = Math.round(CH * dpr);
    if (narrow) { W = VW; H = VH; Z = Z0; OX = OY = 0; } else { W = CW; H = CH; Z = 1; OX = OY = 0; }
    var mode = narrow ? "n" : "w";
    G.forEach(function (g, i) {
      var a = -Math.PI / 2 + i / NG * 6.2832, p = [0.5 + Math.cos(a) * (narrow ? 0.2 : 0.25 * Math.min(1, 1240 / W + 0.1)), 0.5 + Math.sin(a) * 0.25];
      if (saved && saved[mode] && saved[mode][i]) p = saved[mode][i];
      g.fx = p[0]; g.fy = p[1]; g.r = narrow ? 19 : 13; g.tools.forEach(function (t) { t.r = narrow ? 10 : 6.5; });
    });
    layout(); view();
  }
  function layout() {
    var gx = 0, gy = 0; G.forEach(function (g) { g.x = g.fx * W; g.y = g.fy * H; gx += g.x / NG; gy += g.y / NG; });
    G.forEach(function (g) {
      var a = Math.atan2(g.y - gy, g.x - gx), n = g.tools.length, s = g.el.style;
      s.left = (g.x - Math.cos(a) * (narrow ? 62 : 84)) + "px"; s.top = (g.y - Math.sin(a) * (narrow ? 50 : 44)) + "px"; s.transform = "translate(-50%,-50%)"; s.textAlign = "center";
      g.tools.forEach(function (t, j) {
        var ta = a + (j - (n - 1) / 2) * (n > 3 ? 0.46 : 0.54), d = 150 + (n > 2 && j % 2 ? 26 : 0), ts = t.el.style;
        t.x = g.x + Math.cos(ta) * d; t.y = g.y + Math.sin(ta) * d; var c = Math.cos(ta), sn = Math.sin(ta), side = c > 0.12 ? 1 : c < -0.12 ? -1 : 0;
        ts.left = (t.x + (side ? side * 18 : 0)) + "px"; ts.top = (t.y + (side ? 0 : sn > 0 ? 24 : -24)) + "px"; ts.transform = "translate(" + (side > 0 ? "0" : side < 0 ? "-100%" : "-50%") + ",-50%)"; ts.textAlign = side > 0 ? "left" : side < 0 ? "right" : "center";
        t.c = [(g.x + t.x) / 2 - (t.y - g.y) * 0.12, (g.y + t.y) / 2 + (t.x - g.x) * 0.12];
      });
    });
    RING.forEach(function (e) { var mx = (e.a.x + e.b.x) / 2, my = (e.a.y + e.b.y) / 2, ox = mx - gx, oy = my - gy, ol = Math.hypot(ox, oy) || 1, l = Math.hypot(e.b.x - e.a.x, e.b.y - e.a.y);
      e.c = [mx - ox / ol * l * 0.16, my - oy / ol * l * 0.16]; });
  }
  var LW = 1;
  function glow(x, y, r, a) { var g = cx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, "rgba(255,255,255," + a + ")"); g.addColorStop(0.25, "rgba(215,230,255," + a * 0.45 + ")"); g.addColorStop(1, "rgba(180,210,255,0)"); cx.fillStyle = g; cx.fillRect(x - r, y - r, r * 2, r * 2); }
  function push(x, y) { if (px < 0) return [x, y]; var dx = x - px, dy = y - py, d = Math.hypot(dx, dy) || 1, f = Math.max(0, 1 - d / 170); f = f * f * 40; return [x + dx / d * f, y + dy / d * f]; }
  function lit(n) { return !pick || n === pick || n.g === pick || (pick.g && pick.g === n) ; }
  // a rope from A to B bending through c: strands that cross over between its thirds, turning, with light along it
  function rope(A, B, c, st, wide, base, t, e0, pulses, key) {
    var dx = B.vx - A.vx, dy = B.vy - A.vy, l = Math.hypot(dx, dy) || 1, nx = -dy / l, ny = dx / l;
    var p1 = push(A.vx + (c[0] - A.x) * 2 / 3, A.vy + (c[1] - A.y) * 2 / 3), p2 = push(B.vx + (c[0] - B.x) * 2 / 3, B.vy + (c[1] - B.y) * 2 / 3);
    cx.lineWidth = 0.55 * LW;
    for (var q = 0; q < st.length * e0; q++) { var s = st[q], th = s.ph + (still ? 0 : t * s.sp * 0.5), o1 = wide * s.r * Math.sin(th), o2 = wide * s.r * Math.sin(th + 2.6 + s.tw);
      cx.strokeStyle = "rgba(226,236,252," + (base * (0.3 + 0.7 * (0.5 + 0.5 * Math.cos(th)))).toFixed(3) + ")"; cx.beginPath(); cx.moveTo(A.vx, A.vy); cx.bezierCurveTo(p1[0] + nx * o1, p1[1] + ny * o1, p2[0] + nx * o2, p2[1] + ny * o2, B.vx, B.vy); cx.stroke(); }
    if (still || intro < 1 || !pulses) return;
    function at(f) { var u = 1 - f; return [u * u * u * A.vx + 3 * u * u * f * p1[0] + 3 * u * f * f * p2[0] + f * f * f * B.vx, u * u * u * A.vy + 3 * u * u * f * p1[1] + 3 * u * f * f * p2[1] + f * f * f * B.vy]; }
    cx.lineCap = "round";
    for (var u = 0; u < pulses; u++) { var f = (t * (0.1 + u * 0.03) + key * 0.37 + u * 0.41) % 1, back = u % 2;
      for (var k = 0; k < 12; k++) { var f0 = f - k * 0.011, f1 = f - (k + 1) * 0.011; if (f1 < 0) break; var a0 = at(back ? 1 - f0 : f0), a1 = at(back ? 1 - f1 : f1); cx.strokeStyle = "rgba(240,246,255," + ((1 - k / 12) * 0.8 * Math.min(1, base * 5)).toFixed(3) + ")"; cx.lineWidth = (wide > 30 ? 1.8 : 1.2) * LW * (1 - k / 14); cx.beginPath(); cx.moveTo(a0[0], a0[1]); cx.lineTo(a1[0], a1[1]); cx.stroke(); }
      var hd = at(back ? 1 - f : f); glow(hd[0], hd[1], wide > 30 ? 13 : 8, Math.min(0.95, base * 5)); }
  }
  function knot(n, t, a) {
    var beat = still ? 0.5 : 0.5 + 0.5 * Math.sin(t * 1.3 + n.ph * 3), hot = n === pick || n === grab ? 1.45 : 1, X = n.vx, Y = n.vy, R = n.r, big = !n.g;
    glow(X, Y, R * (4.2 + 0.6 * beat) * hot, (big ? 0.26 : 0.2) * a); glow(X, Y, R * 1.1, 0.9 * a); glow(X, Y, R * 0.42, a);
    var rot = still ? 0.3 : t * 0.07 + n.ph, rays = big ? 6 : 4;
    for (var r0 = 0; r0 < rays; r0++) { var ang = rot + r0 * 6.2832 / rays, len = R * ((big ? r0 % 3 === 0 : r0 % 2 === 0) ? 4.4 + 1.2 * beat : 2.1 + 0.5 * beat) * hot, ex = X + Math.cos(ang) * len, ey = Y + Math.sin(ang) * len, g = cx.createLinearGradient(X, Y, ex, ey);
      g.addColorStop(0, "rgba(255,255,255," + (0.85 * a).toFixed(3) + ")"); g.addColorStop(0.3, "rgba(215,230,255," + (0.3 * a).toFixed(3) + ")"); g.addColorStop(1, "rgba(200,220,255,0)"); cx.strokeStyle = g; cx.lineWidth = (big ? 1 : 0.7) * LW; cx.beginPath(); cx.moveTo(X, Y); cx.lineTo(ex, ey); cx.stroke(); }
    cx.lineWidth = 0.5 * LW;
    n.kn.forEach(function (z) { var a0 = still ? z.ph : t * z.sp + z.ph, ct = Math.cos(z.tilt), sn = Math.sin(z.tilt), RR = R * (0.9 + z.r);
      cx.strokeStyle = "rgba(225,234,250," + (0.34 * a * hot * (0.4 + 0.6 * Math.abs(Math.sin(z.ph + t * 0.3)))).toFixed(3) + ")"; cx.beginPath();
      for (var w = 0; w <= 16; w++) { var qq = a0 + w / 16 * z.len, ox = Math.cos(qq) * RR, oy = Math.sin(qq) * RR * z.sq, x2 = X + ox * ct - oy * sn, y2 = Y + ox * sn + oy * ct; if (w) cx.lineTo(x2, y2); else cx.moveTo(x2, y2); } cx.stroke(); });
  }
  function draw(time) {
    if (!t0) t0 = time; var t = (time - t0) / 1000; if (intro < 1) intro = Math.min(1, t / 2); var e0 = 1 - Math.pow(1 - intro, 3);
    cx.setTransform(1, 0, 0, 1, 0, 0); cx.clearRect(0, 0, cv.width, cv.height); cx.setTransform(dpr * Z, 0, 0, dpr * Z, OX * dpr, OY * dpr); LW = Math.min(2.4, 1 / Z); cx.globalCompositeOperation = "lighter";
    DUST.forEach(function (d) { var y = ((d.y - t * d.v) % 1 + 1) % 1; cx.fillStyle = "rgba(225,234,250," + (d.a * (0.6 + 0.4 * Math.sin(t + d.ph)) * e0).toFixed(3) + ")"; cx.fillRect(d.x * W, y * H, d.s, d.s); });
    ALL.forEach(function (n) { var fl = still || n === grab || (n.g && n.g === grab) ? 0 : 1, k = n.g ? 3 : 5; n.vx = n.x + Math.sin(t * 0.42 + n.ph) * k * fl; n.vy = n.y + Math.cos(t * 0.36 + n.ph * 1.7) * k * fl; });
    RING.forEach(function (e, i) { var on = !pick || e.a === pick || e.b === pick || (pick.g && (pick.g === e.a || pick.g === e.b)); rope(e.a, e.b, e.c, e.st, Math.min(46, Math.hypot(e.b.x - e.a.x, e.b.y - e.a.y) * 0.1), (on ? (pick ? 0.3 : 0.19) : 0.04) * e0, t, e0, on ? 3 : 0, i); });
    G.forEach(function (g) { g.tools.forEach(function (tl, j) { var on = !pick || pick === g || pick === tl; rope(g, tl, tl.c, tl.st, 13, (on ? (pick ? 0.42 : 0.24) : 0.05) * e0, t, e0, on ? 1 : 0, g.i * 4 + j + 7); }); });
    ALL.forEach(function (n) { knot(n, t, (lit(n) ? 1 : 0.35) * e0); });
    cx.globalCompositeOperation = "source-over";
  }
  var run = 0, visible = true;
  function frame(time) { run = 0; draw(time); if (!still && visible) run = requestAnimationFrame(frame); }
  function once() { if (!run) run = requestAnimationFrame(frame); }
  function set(n) { if (n === pick) return; pick = n; map.classList.toggle("has-pick", !!n); ALL.forEach(function (m) { m.el.classList.toggle("is-on", !n || lit(m)); }); once(); }
  ALL.forEach(function (n) { n.el.addEventListener("pointerenter", function () { set(n); }); n.el.addEventListener("pointerleave", function () { set(null); }); n.el.addEventListener("focus", function () { set(n); }); n.el.addEventListener("blur", function () { set(null); }); });
  function hit(x, y) { var b = null, bd = 1e9, k = narrow ? Math.max(1, 0.7 / Z) : 1; ALL.forEach(function (n) { var d = Math.hypot(n.x - x, n.y - y); if (d < (n.g ? 20 : 30) * k && d < bd) { bd = d; b = n; } }); return b; }
  function at(e) { var b = map.getBoundingClientRect(); return [(e.clientX - b.left - OX) / Z, (e.clientY - b.top - OY) / Z, e.clientX - b.left, e.clientY - b.top]; }
  var moved = 0, sx = 0, sy = 0, TP = {}, pin = null;
  function fingers() { var a = []; for (var k in TP) a.push(TP[k]); return a; }
  map.addEventListener("pointerdown", function (e) { var p = at(e);
    if (e.pointerType === "touch") { TP[e.pointerId] = { x: p[2], y: p[3], x0: p[2], y0: p[3], t: e.target }; var f = fingers(); moved = 0;
      pin = f.length === 2 ? { d: Math.hypot(f[0].x - f[1].x, f[0].y - f[1].y) || 1, z: Z, wx: ((f[0].x + f[1].x) / 2 - OX) / Z, wy: ((f[0].y + f[1].y) / 2 - OY) / Z } : null; return; }
    if (e.target !== cv) return; var n = hit(p[0], p[1]); if (!n) return;
    grab = n; moved = 0; sx = e.clientX; sy = e.clientY; cv.setPointerCapture(e.pointerId); cv.style.cursor = n.g ? "pointer" : "grabbing"; e.preventDefault(); });
  map.addEventListener("pointermove", function (e) { var p = at(e);
    if (e.pointerType === "touch") { var me = TP[e.pointerId]; if (!me) return; var dx = p[2] - me.x, dy = p[3] - me.y; me.x = p[2]; me.y = p[3]; moved = Math.max(moved, Math.hypot(p[2] - me.x0, p[3] - me.y0)); var f = fingers();
      if (pin && f.length === 2) { var mx = (f[0].x + f[1].x) / 2, my = (f[0].y + f[1].y) / 2; Z = pin.z * Math.hypot(f[0].x - f[1].x, f[0].y - f[1].y) / pin.d; Z = Math.max(Z0, Math.min(Z0 * 4.5, Z)); OX = mx - pin.wx * Z; OY = my - pin.wy * Z; view(); once(); e.preventDefault(); }
      else if (f.length === 1 && Z > Z0 * 1.03) { OX += dx; OY += dy; view(); once(); e.preventDefault(); }
      return; }
    px = p[0]; py = p[1];
    if (grab) { moved = Math.max(moved, Math.hypot(e.clientX - sx, e.clientY - sy)); if (moved > 5 && !grab.g) { grab.fx = Math.max(0.06, Math.min(0.94, p[0] / W)); grab.fy = Math.max(0.08, Math.min(0.92, p[1] / H)); layout(); } once(); return; }
    if (e.target !== cv) return; var n = hit(p[0], p[1]); cv.style.cursor = n ? (n.g ? "pointer" : "grab") : "default"; set(n); });
  function lift(e) {
    if (e.pointerType === "touch") { var me = TP[e.pointerId], was = fingers().length; delete TP[e.pointerId]; pin = null;
      if (me && was === 1 && moved < 8 && me.t === cv && e.type === "pointerup") { var p = at(e), n = hit(p[0], p[1]); if (n && n.g) n.el.click(); }
      fingers().forEach(function (o) { o.x0 = o.x; o.y0 = o.y; }); return; }
    if (!grab) return; var g0 = grab; grab = null; cv.style.cursor = "default";
    if (moved <= 5) { if (g0.g) g0.el.click(); return; }
    if (g0.g) return;
    try { var all = JSON.parse(localStorage.getItem(KEY) || "{}") || {}, mine = all.all || {}, mode = narrow ? "n" : "w"; mine[mode] = G.map(function (g) { return [+g.fx.toFixed(4), +g.fy.toFixed(4)]; }); all.all = mine; localStorage.setItem(KEY, JSON.stringify(all)); saved = mine; } catch (err) {} once(); }
  map.addEventListener("pointerup", lift); map.addEventListener("pointercancel", lift);
  map.addEventListener("click", function (e) { if (moved >= 8 && e.target !== cv) e.preventDefault(); }, true); // a finger that moved the map does not open a tool
  cv.addEventListener("pointerleave", function () { px = py = -1; if (!grab) set(null); });
  cv.addEventListener("dblclick", function () { try { var all = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; delete all.all; localStorage.setItem(KEY, JSON.stringify(all)); } catch (err) {} saved = null; size(); once(); });
  window.addEventListener("resize", function () { size(); once(); });
  if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { visible = en[0].isIntersecting; if (visible) once(); }).observe(map);
  size(); once();
})();
