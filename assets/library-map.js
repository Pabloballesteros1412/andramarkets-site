/* Research Library: the reports as a map of light. The six topics are stars in a ring; each report
   is a smaller star, brighter the newer it is, tied by a rope of fine strands to every topic it
   is about, so a report on two topics sits between them. The page's own list is the source: this
   script reads its rows (title, date, topics, link) and draws them, and the list stays below for
   search and for readers without the picture. Pointing at a report shows what it is; a press opens
   its PDF. Pointing at a topic lights its reports; a press filters the list to it. On a narrow
   screen the map is drawn whole, two fingers enlarge it, one finger moves it once enlarged, a tap
   on a report shows it and a tap on its card opens it. */
(function () {
  var map = document.querySelector(".lib-map"); if (!map) return;
  var rows = [].slice.call(document.querySelectorAll("[data-lib-item]")), chips = [].slice.call(document.querySelectorAll(".chip[data-lib-tag]"));
  if (rows.length < 3 || chips.length < 3) return;
  var cv = map.querySelector("canvas"), cx = cv.getContext("2d"), names = map.querySelector(".lib-map__names"), card = map.querySelector(".lib-map__card"); if (!cx) return;
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var seed = 3; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
  function strands(n) { var a = []; for (var i = 0; i < n; i++) a.push({ r: Math.sqrt(rnd()), tw: (rnd() - 0.5) * 1.6, ph: rnd() * 6.28, sp: 0.5 + rnd() * 0.7 }); return a; }
  function orbits(n) { var a = []; for (var i = 0; i < n; i++) a.push({ tilt: rnd() * 3.14, sq: 0.25 + rnd() * 0.75, r: 0.6 + rnd() * 0.7, sp: (rnd() < 0.5 ? -1 : 1) * (0.2 + rnd() * 0.5), ph: rnd() * 6.28, len: 2.2 + rnd() * 3.2 }); return a; }
  // topics, from the filter's own chips
  var T = [], byK = {};
  chips.forEach(function (c) { var k = c.getAttribute("data-lib-tag"); if (k === "all") return; var el = document.createElement("span"); el.className = "lib-map__name"; el.textContent = c.firstChild.textContent.trim(); var n = document.createElement("i"); el.appendChild(n); names.appendChild(el);
    var t = { k: k, chip: c, el: el, cnt: n, ph: rnd() * 6.28, n: 0, kn: orbits(7), singles: [] }; T.push(t); byK[k] = t; });
  T.forEach(function (t, i) { t.a = -Math.PI / 2 + i / T.length * 6.2832; });
  // reports, from the list's rows (newest first)
  var R = rows.map(function (li, i) {
    var a = li.querySelector("a"), ti = li.querySelector(".lib-res__t, .lib-issue__t"), tm = li.querySelector("time"), meta = li.querySelector(".lib-res__m, .lib-issue__f");
    var tg = (li.getAttribute("data-tags") || "").split(" ").map(function (k) { return byK[k]; }).filter(Boolean); tg.forEach(function (t) { t.n++; });
    var pages = meta && /(\d+) pages?/.exec(meta.textContent);
    var r = { li: li, a: a, title: ti ? ti.textContent : "", date: tm ? tm.textContent : "", pages: pages ? pages[0] : "", tg: tg, age: i / rows.length, ph: rnd() * 6.28, j: [rnd() - 0.5, rnd() - 0.5], st: tg.map(function () { return strands(8); }) };
    if (tg.length === 1) tg[0].singles.push(r); return r;
  }).filter(function (r) { return r.tg.length && r.a; });
  T.forEach(function (t) { t.cnt.textContent = t.n; });
  var DUST = []; for (var d0 = 0; d0 < 220; d0++) DUST.push({ x: rnd(), y: rnd(), s: 0.4 + rnd() * 1.2, a: 0.07 + rnd() * 0.26, v: 0.004 + rnd() * 0.01, ph: rnd() * 6.28 });
  var W = 0, H = 0, CW = 0, CH = 0, Z = 1, Z0 = 1, OX = 0, OY = 0, VW = 1000, VH = 1000, dpr = 1, narrow = false, LW = 1;
  var pick = null, hot = null, held = null, px = -1, py = -1, t0 = 0, intro = still ? 1 : 0;
  function view() {
    if (narrow) { Z = Math.max(Z0, Math.min(Z0 * 5, Z)); OX = Math.min(0, Math.max(CW - VW * Z, OX)); OY = Math.min(0, Math.max(CH - VH * Z, OY)); }
    names.style.width = W + "px"; names.style.height = H + "px"; names.style.transform = narrow ? "translate(" + OX + "px," + OY + "px) scale(" + Z + ")" : "none";
    map.classList.toggle("is-zoom", narrow && Z > Z0 * 1.03); place();
  }
  function size() {
    narrow = map.clientWidth < 900; if (narrow) { Z0 = map.clientWidth / VW; map.style.height = Math.round(VH * Z0) + "px"; } else map.style.height = "";
    CW = map.clientWidth; CH = map.clientHeight; dpr = Math.min(window.devicePixelRatio || 1, 2); cv.width = Math.round(CW * dpr); cv.height = Math.round(CH * dpr);
    if (narrow) { W = VW; H = VH; Z = Z0; } else { W = CW; H = CH; Z = 1; } OX = OY = 0;
    var rx = Math.min(W * 0.37, 520), ry = H * 0.36, cx0 = W / 2, cy0 = H / 2;
    T.forEach(function (t) { t.x = cx0 + Math.cos(t.a) * rx; t.y = cy0 + Math.sin(t.a) * ry; t.r = (narrow ? 15 : 11) + Math.sqrt(t.n) * 0.9;
      var s = t.el.style, c = Math.cos(t.a), sn = Math.sin(t.a); s.left = (t.x + c * 56) + "px"; s.top = (t.y + sn * 40) + "px"; s.transform = "translate(" + (c > 0.3 ? "0" : c < -0.3 ? "-100%" : "-50%") + ",-50%)";
      // a topic's own reports: a spiral round it, leaning toward the middle of the map
      t.singles.forEach(function (r, k) { var d = 54 + 25 * Math.sqrt(k + 0.4), a = k * 2.39996 + t.ph; r.x = t.x - c * 46 + Math.cos(a) * d * 1.15; r.y = t.y - sn * 46 + Math.sin(a) * d * 0.9; }); });
    // a report on several topics sits between them
    R.forEach(function (r) { if (r.tg.length < 2) return; var x = 0, y = 0; r.tg.forEach(function (t) { x += t.x / r.tg.length; y += t.y / r.tg.length; }); r.x = x + (cx0 - x) * 0.12 + r.j[0] * 90; r.y = y + (cy0 - y) * 0.12 + r.j[1] * 90; });
    for (var it = 0; it < 80; it++) { for (var i = 0; i < R.length; i++) { for (var j = i + 1; j < R.length; j++) { var a = R[i], b = R[j], dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1, m = 32; if (d < m) { var f = (m - d) / 2 / d; a.x -= dx * f; a.y -= dy * f; b.x += dx * f; b.y += dy * f; } }
      T.forEach(function (t) { var q = R[i], dx = q.x - t.x, dy = q.y - t.y, d = Math.hypot(dx, dy) || 1; if (d < 46) { q.x = t.x + dx / d * 46; q.y = t.y + dy / d * 46; } }); } }
    R.forEach(function (r) { r.x = Math.max(24, Math.min(W - 24, r.x)); r.y = Math.max(24, Math.min(H - 24, r.y)); r.r = (narrow ? 3.6 : 2.6) + 2.4 * (1 - r.age) * (1 - r.age); });
    view();
  }
  function glow(x, y, r, a) { var g = cx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, "rgba(255,255,255," + a + ")"); g.addColorStop(0.25, "rgba(215,230,255," + a * 0.45 + ")"); g.addColorStop(1, "rgba(180,210,255,0)"); cx.fillStyle = g; cx.fillRect(x - r, y - r, r * 2, r * 2); }
  function push(x, y) { if (px < 0) return [x, y]; var dx = x - px, dy = y - py, d = Math.hypot(dx, dy) || 1, f = Math.max(0, 1 - d / 150); f = f * f * 30; return [x + dx / d * f, y + dy / d * f]; }
  function flare(x, y, R0, a, rays, rot, w) { for (var i = 0; i < rays; i++) { var an = rot + i * 6.2832 / rays, l = R0 * (i % 2 ? 2.2 : 4.6), ex = x + Math.cos(an) * l, ey = y + Math.sin(an) * l, g = cx.createLinearGradient(x, y, ex, ey);
    g.addColorStop(0, "rgba(255,255,255," + (0.85 * a).toFixed(3) + ")"); g.addColorStop(0.3, "rgba(215,230,255," + (0.3 * a).toFixed(3) + ")"); g.addColorStop(1, "rgba(200,220,255,0)"); cx.strokeStyle = g; cx.lineWidth = w * LW; cx.beginPath(); cx.moveTo(x, y); cx.lineTo(ex, ey); cx.stroke(); } }
  function shown(r) { return !r.li.hidden; }
  function on(r) { return shown(r) && (!pick || r.tg.indexOf(pick) >= 0) && (!hot || hot === r); }
  function draw(time) {
    if (!t0) t0 = time; var t = (time - t0) / 1000; if (intro < 1) intro = Math.min(1, t / 2.6); var e0 = 1 - Math.pow(1 - intro, 3);
    cx.setTransform(1, 0, 0, 1, 0, 0); cx.clearRect(0, 0, cv.width, cv.height); cx.setTransform(dpr * Z, 0, 0, dpr * Z, OX * dpr, OY * dpr); LW = Math.min(2.4, 1 / Z); cx.globalCompositeOperation = "lighter";
    DUST.forEach(function (d) { var y = ((d.y - t * d.v) % 1 + 1) % 1; cx.fillStyle = "rgba(225,234,250," + (d.a * (0.6 + 0.4 * Math.sin(t + d.ph)) * e0).toFixed(3) + ")"; cx.fillRect(d.x * W, y * H, d.s * LW, d.s * LW); });
    // each report leaves its first topic and settles where it belongs
    R.forEach(function (r) { var fl = still ? 0 : 1, k = Math.max(0, Math.min(1, e0 * 1.5 - r.age * 0.5)), o = r.tg[0]; k = k * k * (3 - 2 * k);
      r.vx = o.x + (r.x - o.x) * k + Math.sin(t * 0.4 + r.ph) * 3 * fl; r.vy = o.y + (r.y - o.y) * k + Math.cos(t * 0.34 + r.ph * 1.6) * 3 * fl; r.k = k; });
    R.forEach(function (r, ri) {
      var lit = on(r), me = hot === r, base = (lit ? (me ? 0.55 : pick ? 0.2 : 0.085) : shown(r) ? 0.03 : 0.008) * e0 * r.k * (0.55 + 0.45 * (1 - r.age));
      r.tg.forEach(function (tp, k) {
        var dx = r.vx - tp.x, dy = r.vy - tp.y, l = Math.hypot(dx, dy) || 1, nx = -dy / l, ny = dx / l, bend = l * 0.1 * (k % 2 ? -1 : 1) * (r.j[0] > 0 ? 1 : -1), wide = Math.min(me ? 16 : 11, l * 0.07);
        var p1 = push(tp.x + dx / 3 + nx * bend, tp.y + dy / 3 + ny * bend), p2 = push(tp.x + dx * 2 / 3 + nx * bend, tp.y + dy * 2 / 3 + ny * bend);
        cx.lineWidth = 0.5 * LW;
        r.st[k].forEach(function (s) { var th = s.ph + (still ? 0 : t * s.sp * 0.5), o1 = wide * s.r * Math.sin(th), o2 = wide * s.r * Math.sin(th + 2.6 + s.tw);
          cx.strokeStyle = "rgba(226,236,252," + (base * (0.35 + 0.65 * (0.5 + 0.5 * Math.cos(th)))).toFixed(3) + ")"; cx.beginPath(); cx.moveTo(tp.x, tp.y); cx.bezierCurveTo(p1[0] + nx * o1, p1[1] + ny * o1, p2[0] + nx * o2, p2[1] + ny * o2, r.vx, r.vy); cx.stroke(); });
        if (still || !lit || intro < 1 || !(me || (ri + k) % 4 === 0)) return;
        function at(f) { var u = 1 - f; return [u * u * u * tp.x + 3 * u * u * f * p1[0] + 3 * u * f * f * p2[0] + f * f * f * r.vx, u * u * u * tp.y + 3 * u * u * f * p1[1] + 3 * u * f * f * p2[1] + f * f * f * r.vy]; }
        var f = (t * (me ? 0.5 : 0.16) + r.ph + k * 0.4) % 1; cx.lineCap = "round";
        for (var q = 0; q < 10; q++) { var f0 = f - q * 0.014, f1 = f - (q + 1) * 0.014; if (f1 < 0) break; var a0 = at(f0), a1 = at(f1); cx.strokeStyle = "rgba(240,246,255," + ((1 - q / 10) * (me ? 0.9 : 0.55)).toFixed(3) + ")"; cx.lineWidth = (me ? 1.6 : 1.1) * LW * (1 - q / 12); cx.beginPath(); cx.moveTo(a0[0], a0[1]); cx.lineTo(a1[0], a1[1]); cx.stroke(); }
        var hd = at(f); glow(hd[0], hd[1], me ? 10 : 6, me ? 0.95 : 0.7);
      });
    });
    T.forEach(function (tp) { var a = ((!pick || pick === tp) && (!hot || hot.tg.indexOf(tp) >= 0) ? 1 : 0.35) * e0, beat = still ? 0.5 : 0.5 + 0.5 * Math.sin(t * 1.3 + tp.ph * 3), hotT = pick === tp ? 1.35 : 1, X = tp.x, Y = tp.y, R0 = tp.r;
      glow(X, Y, R0 * (4.4 + 0.6 * beat) * hotT, 0.26 * a); glow(X, Y, R0 * 1.1, 0.9 * a); glow(X, Y, R0 * 0.42, a); flare(X, Y, R0 * (1 + 0.2 * beat) * hotT, a, 6, (still ? 0.3 : t * 0.07) + tp.ph, 1);
      cx.lineWidth = 0.5 * LW; tp.kn.forEach(function (z) { var a0 = still ? z.ph : t * z.sp + z.ph, ct = Math.cos(z.tilt), sn = Math.sin(z.tilt), RR = R0 * (0.9 + z.r);
        cx.strokeStyle = "rgba(225,234,250," + (0.34 * a * (0.4 + 0.6 * Math.abs(Math.sin(z.ph + t * 0.3)))).toFixed(3) + ")"; cx.beginPath();
        for (var w = 0; w <= 16; w++) { var qq = a0 + w / 16 * z.len, ox = Math.cos(qq) * RR, oy = Math.sin(qq) * RR * z.sq, x2 = X + ox * ct - oy * sn, y2 = Y + ox * sn + oy * ct; if (w) cx.lineTo(x2, y2); else cx.moveTo(x2, y2); } cx.stroke(); }); });
    R.forEach(function (r) { var me = hot === r, lit = on(r) || me, a = (me ? 1 : (lit ? 1 : shown(r) ? 0.42 : 0.08) * (0.4 + 0.6 * (1 - r.age))) * e0, tw = still ? 1 : 0.8 + 0.2 * Math.sin(t * 2.1 + r.ph * 5), R0 = me ? r.r * 2 : r.r;
      glow(r.vx, r.vy, R0 * 4.5, 0.24 * a * tw); glow(r.vx, r.vy, R0 * 1.1, 0.95 * a); flare(r.vx, r.vy, R0 * tw, a, 4, r.ph + (still ? 0 : t * 0.1), 0.7);
      if (me) { cx.strokeStyle = "rgba(242,243,243,.8)"; cx.lineWidth = 1 * LW; cx.beginPath(); cx.arc(r.vx, r.vy, R0 * 2.6 + 2 * Math.sin(t * 3), 0, 6.2832); cx.stroke(); } });
    cx.globalCompositeOperation = "source-over";
    if (hot) place();
  }
  // the card beside the report in hand, in the page's own type
  function fill() { if (!hot) { card.classList.remove("is-on"); return; }
    card.querySelector("b").textContent = hot.title; card.querySelector("span").textContent = [hot.date, hot.tg.map(function (q) { return q.el.firstChild.textContent; }).join(", "), hot.pages].filter(Boolean).join(" · ");
    card.setAttribute("href", hot.a.getAttribute("href")); card.classList.add("is-on"); place(); }
  function place() { if (!hot) return; var x = (hot.vx || hot.x) * Z + OX, y = (hot.vy || hot.y) * Z + OY, w = Math.min(320, CW - 24), left = x + 20; if (left + w > CW - 8) left = x - w - 20; if (left < 8) left = 8;
    card.style.width = w + "px"; card.style.left = left + "px"; card.style.top = Math.max(8, Math.min(CH - 96, y - 18)) + "px"; }
  function names_() { T.forEach(function (q) { q.el.classList.toggle("is-dim", !!((pick && pick !== q) || (hot && hot.tg.indexOf(q) < 0))); q.el.classList.toggle("is-on", pick === q); }); }
  var run = 0, visible = true;
  function frame(tm) { run = 0; draw(tm); if (!still && visible) run = requestAnimationFrame(frame); }
  function once() { if (!run) run = requestAnimationFrame(frame); }
  function pressed() { var k = "all"; chips.forEach(function (c) { if (c.getAttribute("aria-pressed") === "true") k = c.getAttribute("data-lib-tag"); }); return byK[k] || null; }
  var over = null; // the topic under the pointer, over the one the filter holds
  function sync() { pick = over || pressed(); names_(); once(); }
  function near(x, y) { var b = null, k = narrow ? Math.max(1, 0.75 / Z) : 1, bd = 17 * k; R.forEach(function (r) { if (!shown(r)) return; var d = Math.hypot(r.x - x, r.y - y); if (d < bd) { bd = d; b = r; } }); if (b) return b;
    var tp = null; T.forEach(function (q) { if (Math.hypot(q.x - x, q.y - y) < 34 * k) tp = q; }); return tp; }
  function at(e) { var b = map.getBoundingClientRect(); return [(e.clientX - b.left - OX) / Z, (e.clientY - b.top - OY) / Z, e.clientX - b.left, e.clientY - b.top]; }
  function point(n) { var h = n && n.li ? n : null, o = n && !n.li ? n : null; if (h !== hot || o !== over) { hot = h; over = o; fill(); sync(); } cv.style.cursor = n ? "pointer" : "default"; }
  var TP = {}, pin = null, moved = 0;
  function fingers() { var a = []; for (var k in TP) a.push(TP[k]); return a; }
  map.addEventListener("pointerdown", function (e) { if (e.pointerType !== "touch") return; var p = at(e); TP[e.pointerId] = { x: p[2], y: p[3], x0: p[2], y0: p[3], t: e.target }; var f = fingers(); moved = 0;
    pin = f.length === 2 ? { d: Math.hypot(f[0].x - f[1].x, f[0].y - f[1].y) || 1, z: Z, wx: ((f[0].x + f[1].x) / 2 - OX) / Z, wy: ((f[0].y + f[1].y) / 2 - OY) / Z } : null; });
  map.addEventListener("pointermove", function (e) { var p = at(e);
    if (e.pointerType === "touch") { var me = TP[e.pointerId]; if (!me) return; var dx = p[2] - me.x, dy = p[3] - me.y; me.x = p[2]; me.y = p[3]; moved = Math.max(moved, Math.hypot(p[2] - me.x0, p[3] - me.y0)); var f = fingers();
      if (pin && f.length === 2) { var mx = (f[0].x + f[1].x) / 2, my = (f[0].y + f[1].y) / 2; Z = Math.max(Z0, Math.min(Z0 * 5, pin.z * Math.hypot(f[0].x - f[1].x, f[0].y - f[1].y) / pin.d)); OX = mx - pin.wx * Z; OY = my - pin.wy * Z; view(); once(); e.preventDefault(); }
      else if (f.length === 1 && Z > Z0 * 1.03) { OX += dx; OY += dy; view(); once(); e.preventDefault(); }
      return; }
    if (e.target !== cv) return; px = p[0]; py = p[1]; point(near(p[0], p[1])); });
  function lift(e) { if (e.pointerType !== "touch") return; var me = TP[e.pointerId], was = fingers().length; delete TP[e.pointerId]; pin = null;
    if (me && was === 1 && moved < 8 && me.t === cv && e.type === "pointerup") { var p = at(e), n = near(p[0], p[1]); if (n && !n.li) { n.chip.click(); over = null; hot = null; fill(); } else { hot = n || null; over = null; fill(); } sync(); }
    fingers().forEach(function (o) { o.x0 = o.x; o.y0 = o.y; }); }
  map.addEventListener("pointerup", lift); map.addEventListener("pointercancel", lift);
  cv.addEventListener("click", function (e) { if (e.pointerType === "touch" || (e.sourceCapabilities && e.sourceCapabilities.firesTouchEvents)) return; var p = at(e), n = near(p[0], p[1]); if (!n) return; if (n.li) n.a.click(); else { n.chip.getAttribute("aria-pressed") === "true" ? chips[0].click() : n.chip.click(); } });
  cv.addEventListener("pointerleave", function (e) { if (e.pointerType === "touch") return; px = py = -1; if (e.relatedTarget === card) return; point(null); });
  card.addEventListener("pointerleave", function (e) { if (e.pointerType !== "touch") point(null); });
  chips.forEach(function (c) { c.addEventListener("click", function () { window.setTimeout(sync, 0); }); });
  var q = document.getElementById("lib-q"); if (q) q.addEventListener("input", function () { window.setTimeout(once, 0); });
  window.addEventListener("resize", function () { size(); once(); });
  if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { visible = en[0].isIntersecting; if (visible) once(); }).observe(map);
  map.hidden = false; size(); sync();
})();
