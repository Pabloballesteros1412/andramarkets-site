/* Crypto: the Bitcoin sun (owner-approved sketch, 27 Nov 2026). Over the table of coins, Bitcoin is a sun of amber
   light in the site's sky and the largest coins after it are its planets: each a sphere lit from the sun's side,
   sized by its market value, the larger the nearer, on a tilted orbit of fine strands. Beside each planet its name,
   its market value and its change over the day, read from the table's own row; a coin pegged to a currency is
   drawn duller. The planets turn slowly, the near ones faster; that turning is the one thing here that is not
   data, and the line under the picture says so. Pointing at a planet or its name stops the system, lights that
   orbit and leaves the rest dim; a press goes to its row in the table. A planet passing behind the sun is hidden
   by it, and a name fades where it would cross Bitcoin's own. On a phone the system is seen from higher up, so it
   fits an upright screen. Without this script the page is the table. */
(function () {
  "use strict";
  var box = document.querySelector(".cs"), rows = [].slice.call(document.querySelectorAll(".cs-tab tbody tr")); if (!box || rows.length < 6) return;
  var cv = box.querySelector("canvas"), c = cv.getContext && cv.getContext("2d"), layer = box.querySelector(".cs__names"); if (!c) return;
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches, TAU = Math.PI * 2, AMB = "255,176,72", HOT = "255,226,170";
  var seed = 23; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
  function read(tr) { return { id: tr.id, name: tr.querySelector(".cs-name").textContent, cap: +tr.getAttribute("data-cap"), capText: tr.querySelector(".cs-cap").textContent,
    price: tr.querySelector(".cs-price").textContent, day: tr.querySelector(".cs-day").innerHTML, stable: tr.hasAttribute("data-stable") }; }
  var all = rows.slice(0, +box.getAttribute("data-shown") || 12).map(read), sun = all[0], coins = all.slice(1), top = coins[0].cap;
  box.hidden = false; document.querySelector("main").classList.add("has-sun");

  // The sun's corona: strands that lean and breathe. Each orbit: a few strands set a little apart.
  var corona = []; for (var i = 0; i < 420; i++) corona.push({ a: rnd() * TAU, l: Math.pow(rnd(), 2.4), w: (rnd() - 0.5) * 0.5, al: 0.035 + rnd() * 0.06, sp: 0.2 + rnd() * 0.6, ph: rnd() * TAU });
  var specks = []; for (i = 0; i < 46; i++) specks.push({ a: rnd() * TAU, d: Math.sqrt(rnd()), r: 1 + rnd() * 3, al: rnd() * 0.25, sp: (rnd() - 0.5) * 0.3 });
  coins.forEach(function (k, n) {
    k.n = n; k.u = rnd() * TAU; k.strands = []; for (var q = 0; q < 7; q++) k.strands.push({ d: q ? (rnd() - 0.5) * 0.02 : 0, al: q ? 0.05 : 0.2 });
    var a = document.createElement("a"); a.className = "cs__name" + (k.stable ? " is-pegged" : ""); a.href = "#" + k.id;
    a.innerHTML = "<b></b><span class=\"lens-read\"></span>"; a.firstChild.textContent = k.name; a.lastChild.innerHTML = k.capText + " · " + k.day;
    layer.appendChild(a); k.el = a;
    a.addEventListener("pointerenter", function () { pick = k; }); a.addEventListener("pointerleave", function () { if (pick === k) pick = null; });
    a.addEventListener("focus", function () { pick = k; }); a.addEventListener("blur", function () { if (pick === k) pick = null; });
  });
  var mid = document.createElement("a"); mid.className = "cs__sun"; mid.href = "#" + sun.id; mid.innerHTML = "<b></b><span class=\"lens-read\"></span>";
  mid.firstChild.textContent = sun.name; mid.lastChild.innerHTML = sun.price + " · " + sun.day; layer.appendChild(mid);

  var W = 0, H = 0, cx = 0, cy = 0, R0 = 0, R1 = 0, SR = 0, SQ = 0.34, TILT = -0.16, narrow = false, pick = null, t = 0, last = 0, run = 0, seen = true, hover = null;
  function size() {
    var d = Math.min(window.devicePixelRatio || 1, 2); W = box.clientWidth; H = box.clientHeight; if (!W) return;
    narrow = W < 900; SQ = narrow ? 0.72 : 0.34; TILT = narrow ? -0.32 : -0.16;
    cx = W / 2; cy = H * (narrow ? 0.46 : 0.5); SR = narrow ? 34 : Math.min(56, H * 0.088);
    R1 = narrow ? W * 0.47 : Math.min(W * 0.43, (H * 0.44) / SQ); R0 = SR * (narrow ? 1.9 : 2.7);
    coins.forEach(function (k, n) { k.R = R0 + (R1 - R0) * n / (coins.length - 1); k.r = Math.max(narrow ? 2.6 : 3.4, SR * 0.3 * Math.sqrt(k.cap / top)); k.sp = 0.05 * Math.pow(R0 / k.R, 1.5); });
    cv.width = Math.round(W * d); cv.height = Math.round(H * d); c.setTransform(d, 0, 0, d, 0, 0);
    mid.style.left = cx + "px"; mid.style.top = (cy + SR + (narrow ? 30 : 46)) + "px";
    coins.forEach(function (k) { k.w = 0; });
    draw();
  }
  function at(R, u) { var x = R * Math.cos(u), y = R * SQ * Math.sin(u), ct = Math.cos(TILT), st = Math.sin(TILT); return [cx + x * ct - y * st, cy + x * st + y * ct]; }
  function glow(x, y, r, a, col) { var g = c.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, "rgba(" + col + "," + a + ")"); g.addColorStop(0.3, "rgba(" + col + "," + a * 0.3 + ")"); g.addColorStop(1, "rgba(" + col + ",0)"); c.fillStyle = g; c.beginPath(); c.arc(x, y, r, 0, TAU); c.fill(); }
  function planet(k) {
    var p = k.p, dx = cx - p[0], dy = cy - p[1], d = Math.hypot(dx, dy) || 1, dim = pick && pick !== k ? 0.35 : 1, tone = k.stable ? 0.55 : 1;
    c.globalCompositeOperation = "lighter"; glow(p[0], p[1], k.r * 3.4, 0.5 * dim * tone, AMB); c.globalCompositeOperation = "source-over"; c.globalAlpha = dim;
    var g = c.createRadialGradient(p[0] + dx / d * k.r * 0.55, p[1] + dy / d * k.r * 0.55, k.r * 0.1, p[0], p[1], k.r);
    g.addColorStop(0, k.stable ? "#d8d2c6" : "#fff3dc"); g.addColorStop(0.5, k.stable ? "#8f8672" : "#d9a55c"); g.addColorStop(1, "#1c1408");
    c.fillStyle = g; c.beginPath(); c.arc(p[0], p[1], k.r, 0, TAU); c.fill(); c.globalAlpha = 1;
  }
  function draw() {
    if (!W) return; var q, n;
    c.clearRect(0, 0, W, H); c.globalCompositeOperation = "lighter";
    coins.forEach(function (k) {
      k.p = at(k.R, k.u); k.back = Math.sin(k.u) < 0;
      var lit = pick === k ? 3 : pick ? 0.5 : 1;
      k.strands.forEach(function (s) { c.beginPath(); for (n = 0; n <= 120; n++) { var p = at(k.R * (1 + s.d), n / 120 * TAU); if (n) c.lineTo(p[0], p[1]); else c.moveTo(p[0], p[1]); } c.strokeStyle = "rgba(" + AMB + "," + Math.min(1, s.al * lit).toFixed(3) + ")"; c.lineWidth = 0.7; c.stroke(); });
    });
    c.globalCompositeOperation = "source-over"; coins.forEach(function (k) { if (k.back) planet(k); });
    // the sun over what is behind it
    c.globalCompositeOperation = "lighter"; var beat = 1 + 0.04 * Math.sin(t * 0.9), reach = SR * (narrow ? 2.6 : 4.1);
    corona.forEach(function (s) { var a = s.a + Math.sin(t * s.sp * 0.3 + s.ph) * 0.05, l = SR * 1.25 + s.l * reach * (0.85 + 0.15 * Math.sin(t * s.sp + s.ph));
      c.beginPath(); c.moveTo(cx + Math.cos(a) * SR * 0.82, cy + Math.sin(a) * SR * 0.82); c.quadraticCurveTo(cx + Math.cos(a + s.w) * l * 0.6, cy + Math.sin(a + s.w) * l * 0.6, cx + Math.cos(a + s.w * 1.8) * l, cy + Math.sin(a + s.w * 1.8) * l);
      c.strokeStyle = "rgba(" + AMB + "," + s.al.toFixed(3) + ")"; c.lineWidth = 0.7; c.stroke(); });
    glow(cx, cy, SR * 5.9 * beat, 0.34, AMB); glow(cx, cy, SR * 2.7 * beat, 0.6, AMB); glow(cx, cy, SR * 1.5, 1, HOT);
    c.globalCompositeOperation = "source-over"; var g = c.createRadialGradient(cx - SR * 0.25, cy - SR * 0.28, SR * 0.07, cx, cy, SR * 1.04);
    g.addColorStop(0, "#fffaf0"); g.addColorStop(0.55, "#ffd99a"); g.addColorStop(1, "#f2a33a"); c.fillStyle = g; c.beginPath(); c.arc(cx, cy, SR, 0, TAU); c.fill();
    c.globalCompositeOperation = "lighter"; specks.forEach(function (s) { var a = s.a + t * s.sp, d = s.d * SR * 0.9; c.fillStyle = "rgba(255,255,255," + s.al.toFixed(3) + ")"; c.beginPath(); c.arc(cx + Math.cos(a) * d, cy + Math.sin(a) * d, s.r * SR / 56, 0, TAU); c.fill(); });
    c.globalCompositeOperation = "source-over"; coins.forEach(function (k) { if (!k.back) planet(k); });
    // the names: outward of each planet; gone behind the sun, and where they would cross Bitcoin's own
    coins.forEach(function (k) {
      var p = k.p, side = p[0] >= cx ? 1 : -1, s = k.el.style, far = Math.hypot(p[0] - cx, p[1] - cy), hid = k.back && far < SR * 1.25;
      var inSun = Math.abs(p[0] - cx) < (narrow ? 120 : 190) && p[1] > cy + SR && p[1] < cy + SR + (narrow ? 80 : 120);
      var show = hid || inSun ? 0 : (narrow && k.n > 5 && pick !== k ? 0 : pick && pick !== k ? 0.3 : 1);
      var w = k.w || (k.w = k.el.offsetWidth), lx = side > 0 ? p[0] + k.r + 10 : p[0] - k.r - 10 - w;
      if (narrow) lx = Math.max(6, Math.min(W - w - 6, lx));   // a phone: a name never leaves the screen
      s.left = lx + "px"; s.top = p[1] + "px"; s.transform = "translate(0,-50%)"; s.textAlign = side > 0 ? "left" : "right";
      s.opacity = document.activeElement === k.el ? 1 : show; s.pointerEvents = show > 0.5 ? "auto" : "none";
    });
  }
  function frame(now) {
    var dt = last ? Math.min(0.05, (now - last) / 1000) : 0; last = now; t += dt;
    if (!pick && !hover) coins.forEach(function (k) { k.u += k.sp * dt; });
    draw(); run = !still && seen && !document.hidden ? requestAnimationFrame(frame) : 0;
  }
  function wake() { if (!run && !still && seen && !document.hidden) { last = 0; run = requestAnimationFrame(frame); } }
  // a planet itself can be pointed at and pressed, as its name can
  function near(e) { var b = cv.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top, hit = null; coins.forEach(function (k) { if (Math.hypot(k.p[0] - x, k.p[1] - y) < Math.max(14, k.r + 8)) hit = k; }); return hit; }
  cv.addEventListener("pointermove", function (e) { hover = near(e); pick = hover; cv.style.cursor = hover ? "pointer" : ""; if (still) draw(); });
  cv.addEventListener("pointerleave", function () { hover = null; pick = null; if (still) draw(); });
  cv.addEventListener("click", function (e) { var k = near(e); if (k) location.hash = k.id; });
  if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { seen = en[0].isIntersecting; wake(); }).observe(box);
  document.addEventListener("visibilitychange", wake);
  if ("ResizeObserver" in window) new ResizeObserver(size).observe(box); else window.addEventListener("resize", size);
  size(); wake();
})();
