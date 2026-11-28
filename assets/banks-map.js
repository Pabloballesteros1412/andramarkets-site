/* Central banks: every bank the page lists, on one map of light. Four regions are knots in the
   middle, joined by ropes of fine strands; each central bank is a smaller knot on the rim, tied to
   its region, with its economy, its policy rate and its last move written beside it. A bank that
   moved lately burns brighter. The page's own tables are the source: this script reads their rows
   and draws them, and the tables stay below. Pointing at a bank shows its count of rises and cuts
   and its date; a press goes to its row. Pointing at a region lights its banks. On a narrow screen
   the map is drawn whole, two fingers enlarge it and one finger moves it once enlarged. */
(function () {
  var map = document.querySelector(".cb-map"); if (!map) return;
  var rows = [].slice.call(document.querySelectorAll("tr[data-cb]")); if (rows.length < 8) return;
  var cv = map.querySelector("canvas"), cx = cv.getContext("2d"), layer = map.querySelector(".cb-map__names"), card = map.querySelector(".cb-map__card"); if (!cx) return;
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var seed = 8; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
  function strands(n) { var a = []; for (var i = 0; i < n; i++) a.push({ r: Math.sqrt(rnd()), tw: (rnd() - 0.5) * 1.6, ph: rnd() * 6.28, sp: 0.5 + rnd() * 0.7 }); return a; }
  function orbits(n) { var a = []; for (var i = 0; i < n; i++) a.push({ tilt: rnd() * 3.14, sq: 0.25 + rnd() * 0.75, r: 0.6 + rnd() * 0.7, sp: (rnd() < 0.5 ? -1 : 1) * (0.2 + rnd() * 0.5), ph: rnd() * 6.28, len: 2.2 + rnd() * 3.2 }); return a; }
  // the four sides of the map: which region sits on which, the arc its banks take, and its knot
  var SIDES = [["americas", "Americas", -90, 25], ["europe", "Europe", 0, 55], ["mea", "Middle East and Africa", 90, 24], ["asia", "Asia and Pacific", 180, 50]];
  var G = [], byK = {};
  SIDES.forEach(function (s) { var el = document.createElement("span"); el.className = "cb-map__region"; el.textContent = s[1]; layer.appendChild(el);
    var g = { k: s[0], el: el, mid: s[2] * Math.PI / 180, half: s[3] * Math.PI / 180, r: 13, ph: rnd() * 6.28, kn: orbits(8), banks: [] }; G.push(g); byK[s[0]] = g; });
  var NOW = Date.now();
  var B = rows.map(function (tr) { var g = byK[tr.getAttribute("data-region")]; if (!g) return null;
    var bp = parseFloat(tr.getAttribute("data-bp")), when = tr.getAttribute("data-when"), age = when ? (NOW - Date.parse(when)) / 864e5 : 999;
    var el = document.createElement("span"); el.className = "cb-map__bank";
    el.innerHTML = "<b></b><i></i>"; el.firstChild.textContent = tr.getAttribute("data-name") + " " + tr.getAttribute("data-level");
    if (!isNaN(bp)) { var m = document.createElement("em"); m.className = "mv mv--" + (bp >= 0 ? "up" : "down"); m.textContent = (bp >= 0 ? "+" : "−") + Math.abs(bp) + " bp"; el.lastChild.appendChild(m); var mo = document.createElement("u"); mo.textContent = " " + tr.getAttribute("data-month"); el.lastChild.appendChild(mo); }
    layer.appendChild(el);
    var b = { g: g, tr: tr, el: el, name: tr.getAttribute("data-name"), hot: Math.max(0, 1 - age / 240), r: 5, ph: rnd() * 6.28, kn: orbits(3), st: strands(22) }; g.banks.push(b); return b; }).filter(Boolean);
  G = G.filter(function (g) { return g.banks.length; }); var NG = G.length; if (NG < 2) return;
  var RING = G.map(function (g, i) { return { a: g, b: G[(i + 1) % NG], st: strands(70) }; });
  var ALL = G.concat(B);
  var W = 0, H = 0, CW = 0, CH = 0, Z = 1, Z0 = 1, OX = 0, OY = 0, VW = 1100, VH = 1150, dpr = 1, narrow = false, LW = 1;
  var pick = null, px = -1, py = -1, t0 = 0, intro = still ? 1 : 0;
  function view() {
    if (narrow) { Z = Math.max(Z0, Math.min(Z0 * 5, Z)); OX = Math.min(0, Math.max(CW - VW * Z, OX)); OY = Math.min(0, Math.max(CH - VH * Z, OY)); }
    layer.style.width = W + "px"; layer.style.height = H + "px"; layer.style.transform = narrow ? "translate(" + OX + "px," + OY + "px) scale(" + Z + ")" : "none";
    map.classList.toggle("is-zoom", narrow && Z > Z0 * 1.03); place();
  }
  function size() {
    narrow = map.clientWidth < 900; if (narrow) { Z0 = map.clientWidth / VW; map.style.height = Math.round(VH * Z0) + "px"; } else map.style.height = "";
    CW = map.clientWidth; CH = map.clientHeight; fit();
    if (narrow) { W = VW; H = VH; Z = Z0; } else { W = CW; H = CH; Z = 1; } OX = OY = 0;
    var x0 = W / 2, y0 = narrow ? H / 2 : H * 0.6, a = narrow ? 330 : Math.min(W * 0.33, 500), b = narrow ? 400 : Math.min(H * 0.27, 300);
    G.forEach(function (g) {
      var c = Math.cos(g.mid), s = Math.sin(g.mid), n = g.banks.length; g.x = x0 + c * a * 0.43; g.y = y0 + s * b * 0.45; g.r = narrow ? 17 : 13;
      var gs = g.el.style; gs.left = (g.x - c * 30) + "px"; gs.top = (g.y - s * 34 - (s ? 0 : 30)) + "px"; gs.transform = "translate(-50%,-50%)";
      g.banks.forEach(function (k, j) {
        var th = g.mid + (n > 1 ? (j / (n - 1) - 0.5) * 2 : 0) * g.half * (Math.abs(s) > 0.5 ? 1 : 1), kc = Math.cos(th), ks = Math.sin(th);
        k.x = x0 + kc * a; k.y = y0 + ks * b; k.r = narrow ? 7 : 5;
        var st = k.el.style, side = Math.abs(c) > 0.5, up = s < -0.5, off = side || n < 5 ? 0 : (j % 2 ? 34 : 0); k.el.classList.toggle("is-side", side);
        if (side) { st.left = (k.x + c * 16) + "px"; st.top = k.y + "px"; st.transform = "translate(" + (c > 0 ? "0" : "-100%") + ",-50%)"; st.textAlign = c > 0 ? "left" : "right"; }
        else { st.left = k.x + "px"; st.top = (k.y + (up ? -1 : 1) * (26 + off)) + "px"; st.transform = "translate(-50%,-50%)"; st.textAlign = "center"; }
        k.c = [(g.x + k.x) / 2 + (k.y - g.y) * 0.1 * (j % 2 ? 1 : -1), (g.y + k.y) / 2 - (k.x - g.x) * 0.1 * (j % 2 ? 1 : -1)];
      });
    });
    RING.forEach(function (e) { var mx = (e.a.x + e.b.x) / 2, my = (e.a.y + e.b.y) / 2; e.c = [mx + (x0 - mx) * 0.35, my + (y0 - my) * 0.35]; });
    view();
  }
  // A machine that cannot keep up gets a coarser picture, not a slower one: first the canvas below the screen's density
  // (res), then fewer strands in each rope, each a little brighter (SF), as on the homepage and the Tools map.
  var res = 1, SF = 1, slow = 0, nfr = 0, last = 0;
  function fit() { dpr = Math.min(window.devicePixelRatio || 1, 2) * res; cv.width = Math.round(CW * dpr); cv.height = Math.round(CH * dpr); }
  function glow(x, y, r, a) { var g = cx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, "rgba(255,255,255," + a + ")"); g.addColorStop(0.25, "rgba(215,230,255," + a * 0.45 + ")"); g.addColorStop(1, "rgba(180,210,255,0)"); cx.fillStyle = g; cx.fillRect(x - r, y - r, r * 2, r * 2); }
  function push(x, y) { if (px < 0) return [x, y]; var dx = x - px, dy = y - py, d = Math.hypot(dx, dy) || 1, f = Math.max(0, 1 - d / 160); f = f * f * 34; return [x + dx / d * f, y + dy / d * f]; }
  function lit(n) { return !pick || n === pick || n.g === pick || (!!pick.g && pick.g === n); }
  function rope(A, Bq, c, st, wide, base, t, e0, pulses, key) {
    var dx = Bq.vx - A.vx, dy = Bq.vy - A.vy, l = Math.hypot(dx, dy) || 1, nx = -dy / l, ny = dx / l;
    var p1 = push(A.vx + (c[0] - A.x) * 2 / 3, A.vy + (c[1] - A.y) * 2 / 3), p2 = push(Bq.vx + (c[0] - Bq.x) * 2 / 3, Bq.vy + (c[1] - Bq.y) * 2 / 3);
    cx.lineWidth = 0.55 * LW;
    for (var q = 0; q < st.length * e0 * SF; q++) { var s = st[q], th = s.ph + (still ? 0 : t * s.sp * 0.5), o1 = wide * s.r * Math.sin(th), o2 = wide * s.r * Math.sin(th + 2.6 + s.tw);
      cx.strokeStyle = "rgba(226,236,252," + (Math.min(1, base / SF) * (0.3 + 0.7 * (0.5 + 0.5 * Math.cos(th)))).toFixed(3) + ")"; cx.beginPath(); cx.moveTo(A.vx, A.vy); cx.bezierCurveTo(p1[0] + nx * o1, p1[1] + ny * o1, p2[0] + nx * o2, p2[1] + ny * o2, Bq.vx, Bq.vy); cx.stroke(); }
    if (still || intro < 1 || !pulses) return;
    function at(f) { var u = 1 - f; return [u * u * u * A.vx + 3 * u * u * f * p1[0] + 3 * u * f * f * p2[0] + f * f * f * Bq.vx, u * u * u * A.vy + 3 * u * u * f * p1[1] + 3 * u * f * f * p2[1] + f * f * f * Bq.vy]; }
    cx.lineCap = "round";
    for (var u = 0; u < pulses; u++) { var f = (t * (0.1 + u * 0.03) + key * 0.37 + u * 0.41) % 1, back = u % 2;
      for (var k = 0; k < 12; k++) { var f0 = f - k * 0.011, f1 = f - (k + 1) * 0.011; if (f1 < 0) break; var a0 = at(back ? 1 - f0 : f0), a1 = at(back ? 1 - f1 : f1); cx.strokeStyle = "rgba(240,246,255," + ((1 - k / 12) * 0.8 * Math.min(1, base * 5)).toFixed(3) + ")"; cx.lineWidth = (wide > 30 ? 1.8 : 1.2) * LW * (1 - k / 14); cx.beginPath(); cx.moveTo(a0[0], a0[1]); cx.lineTo(a1[0], a1[1]); cx.stroke(); }
      var hd = at(back ? 1 - f : f); glow(hd[0], hd[1], wide > 30 ? 13 : 7, Math.min(0.95, base * 5)); }
  }
  function knot(n, t, a) {
    var beat = still ? 0.5 : 0.5 + 0.5 * Math.sin(t * 1.3 + n.ph * 3), hot = n === pick ? 1.45 : 1, X = n.vx, Y = n.vy, R = n.r, big = !n.g;
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
    if (!t0) t0 = time; var t = (time - t0) / 1000; if (intro < 1) intro = Math.min(1, t / 2.4); var e0 = 1 - Math.pow(1 - intro, 3);
    cx.setTransform(1, 0, 0, 1, 0, 0); cx.clearRect(0, 0, cv.width, cv.height); cx.setTransform(dpr * Z, 0, 0, dpr * Z, OX * dpr, OY * dpr); LW = Math.min(2.4, 1 / Z); cx.globalCompositeOperation = "lighter";
    ALL.forEach(function (n) { var fl = still ? 0 : 1, k = n.g ? 2.5 : 5; n.vx = n.x + Math.sin(t * 0.42 + n.ph) * k * fl; n.vy = n.y + Math.cos(t * 0.36 + n.ph * 1.7) * k * fl; });
    RING.forEach(function (e, i) { var on = !pick || e.a === pick || e.b === pick || (pick.g && (pick.g === e.a || pick.g === e.b)); rope(e.a, e.b, e.c, e.st, 34, (on ? (pick ? 0.28 : 0.18) : 0.04) * e0, t, e0, on ? 2 : 0, i); });
    B.forEach(function (k, j) { var on = lit(k); rope(k.g, k, k.c, k.st, 9, (on ? (pick === k ? 0.5 : 0.1 + 0.16 * k.hot) : 0.03) * e0, t, e0, on && (pick === k || k.hot > 0.6) ? 1 : 0, j + 5); });
    G.forEach(function (g) { knot(g, t, (lit(g) ? 1 : 0.35) * e0); });
    B.forEach(function (k) { knot(k, t, (lit(k) ? 0.45 + 0.55 * k.hot : 0.2) * e0 * (pick === k ? 2 : 1)); });
    cx.globalCompositeOperation = "source-over";
    if (pick && pick.g) place();
  }
  function fill() { var k = pick && pick.g ? pick : null; card.classList.toggle("is-on", !!k); if (!k) return; var tr = k.tr; card.textContent = tr.getAttribute("data-note"); place(); }
  function place() { var k = pick && pick.g ? pick : null; if (!k) return; var r = k.el.getBoundingClientRect(), m = map.getBoundingClientRect(); card.style.left = Math.max(8, Math.min(CW - card.offsetWidth - 8, r.left - m.left + (k.el.style.textAlign === "right" ? r.width - card.offsetWidth : 0))) + "px"; card.style.top = (r.bottom - m.top + 4) + "px"; }
  var run = 0, visible = true;
  function frame(tm) { run = 0;
    if (last) { slow += Math.min(tm - last, 500); if (++nfr === 30 || (nfr >= 6 && slow > 1000)) { if (slow / nfr > 26) { if (res > 0.5) { res *= 0.78; fit(); } else if (SF > 0.35) SF *= 0.75; } slow = 0; nfr = 0; } } last = tm;
    draw(tm); if (!still && visible) run = requestAnimationFrame(frame); else last = 0; }
  function once() { if (!run) { last = 0; run = requestAnimationFrame(frame); } }
  function set(n) { if (n === pick) return; pick = n; map.classList.toggle("has-pick", !!n); ALL.forEach(function (m) { m.el.classList.toggle("is-on", !n || lit(m)); }); fill(); once(); }
  function near(x, y) { var b = null, k = narrow ? Math.max(1, 0.7 / Z) : 1, bd = 22 * k; B.forEach(function (q) { var d = Math.hypot(q.x - x, q.y - y); if (d < bd) { bd = d; b = q; } }); if (b) return b; G.forEach(function (q) { if (Math.hypot(q.x - x, q.y - y) < 36 * k) b = q; }); return b; }
  function at(e) { var b = map.getBoundingClientRect(); return [(e.clientX - b.left - OX) / Z, (e.clientY - b.top - OY) / Z, e.clientX - b.left, e.clientY - b.top]; }
  function go(k) { var tr = k.tr; tr.scrollIntoView({ behavior: still ? "auto" : "smooth", block: "center" }); tr.classList.add("is-found"); window.setTimeout(function () { tr.classList.remove("is-found"); }, 3600); }
  var TP = {}, pin = null, moved = 0;
  function fingers() { var a = []; for (var k in TP) a.push(TP[k]); return a; }
  map.addEventListener("pointerdown", function (e) { if (e.pointerType !== "touch") return; var p = at(e); TP[e.pointerId] = { x: p[2], y: p[3], x0: p[2], y0: p[3] }; var f = fingers(); moved = 0;
    pin = f.length === 2 ? { d: Math.hypot(f[0].x - f[1].x, f[0].y - f[1].y) || 1, z: Z, wx: ((f[0].x + f[1].x) / 2 - OX) / Z, wy: ((f[0].y + f[1].y) / 2 - OY) / Z } : null; });
  map.addEventListener("pointermove", function (e) { var p = at(e);
    if (e.pointerType === "touch") { var me = TP[e.pointerId]; if (!me) return; var dx = p[2] - me.x, dy = p[3] - me.y; me.x = p[2]; me.y = p[3]; moved = Math.max(moved, Math.hypot(p[2] - me.x0, p[3] - me.y0)); var f = fingers();
      if (pin && f.length === 2) { var mx = (f[0].x + f[1].x) / 2, my = (f[0].y + f[1].y) / 2; Z = Math.max(Z0, Math.min(Z0 * 5, pin.z * Math.hypot(f[0].x - f[1].x, f[0].y - f[1].y) / pin.d)); OX = mx - pin.wx * Z; OY = my - pin.wy * Z; view(); once(); e.preventDefault(); }
      else if (f.length === 1 && Z > Z0 * 1.03) { OX += dx; OY += dy; view(); once(); e.preventDefault(); }
      return; }
    px = p[0]; py = p[1]; var n = near(p[0], p[1]); cv.style.cursor = n && n.g ? "pointer" : "default"; set(n); });
  function lift(e) { if (e.pointerType !== "touch") return; var me = TP[e.pointerId], was = fingers().length; delete TP[e.pointerId]; pin = null;
    if (me && was === 1 && moved < 8 && e.type === "pointerup") { var p = at(e), n = near(p[0], p[1]); if (n && n.g && n === pick) go(n); else set(n); }
    fingers().forEach(function (o) { o.x0 = o.x; o.y0 = o.y; }); }
  map.addEventListener("pointerup", lift); map.addEventListener("pointercancel", lift);
  cv.addEventListener("click", function (e) { if (e.pointerType === "touch") return; var p = at(e), n = near(p[0], p[1]); if (n && n.g) go(n); });
  cv.addEventListener("pointerleave", function (e) { if (e.pointerType === "touch") return; px = py = -1; set(null); });
  window.addEventListener("resize", function () { size(); once(); });
  if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { visible = en[0].isIntersecting; if (visible) once(); }).observe(map);
  map.hidden = false; size(); once();
})();
