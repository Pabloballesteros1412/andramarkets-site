/* Lab and Simulators: one figure that turns into each tool's own curve (owner, 25 Nov 2026). Over the list, the
   tools' names stand at the left and one figure of fine lines at the right, drawn as the lenses are (assets/lens.js):
   48 thin strands laid over one another, so that where they gather it is brighter, and one or two lines in full ink.
   Each tool has a family of curves that is its own (a bond's price against its yield at 48 maturities, two assets at
   48 correlations, 48 paths a market might take); pointing at a name bends the strands from one family into the next.
   Until a name is pointed at, the figure goes through them by itself. On a phone the names are the list below: the
   figure stands over it with the tool's name under it, and "Next" steps through. Every family is calculated here from
   the tool's own formula; those that are made-up paths say "Illustrative". Always white on the black ground. */
(function () {
  "use strict";
  var list = document.querySelector(".lab-groups"), head = document.querySelector("main .page__head");
  if (!list || !head || !document.createElement("canvas").getContext) return;
  var N = 48, M = 97, INK = "242,243,243", MINUS = "−";
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches, wide = window.matchMedia("(min-width: 900px)");

  // A small seeded generator: the same figure every time.
  function rng(s) { s >>>= 0; return function () { s = (s + 0x6D2B79F5) >>> 0; var t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function gauss(r) { return Math.sqrt(-2 * Math.log(r() + 1e-9)) * Math.cos(6.2832 * r()); }
  function cdf(x) { var t = 1 / (1 + 0.2316419 * Math.abs(x)), d = 0.3989423 * Math.exp(-x * x / 2), p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274)))); return x > 0 ? 1 - p : p; }
  function call(S, K, v, T, r) { if (T < 1e-6) return Math.max(S - K, 0); var d1 = (Math.log(S / K) + (r + v * v / 2) * T) / (v * Math.sqrt(T)); return S * cdf(d1) - K * Math.exp(-r * T) * cdf(d1 - v * Math.sqrt(T)); }
  function bond(y, n, c) { return n < 1e-6 ? 1 : c / y * (1 - Math.pow(1 + y, -n)) + Math.pow(1 + y, -n); }

  // Every strand has the same number of points, set evenly along its length, so that one can turn into another.
  function resample(v) {
    var L = [0], i, j = 1, o = new Float32Array(M * 2);
    for (i = 1; i < v.length; i++) L.push(L[i - 1] + Math.hypot(v[i][0] - v[i - 1][0], v[i][1] - v[i - 1][1]));
    var T = L[L.length - 1] || 1;
    for (i = 0; i < M; i++) { var d = T * i / (M - 1); while (j < v.length - 1 && L[j] < d) j++; var s = L[j] - L[j - 1], u = s ? (d - L[j - 1]) / s : 0; o[i * 2] = v[j - 1][0] + (v[j][0] - v[j - 1][0]) * u; o[i * 2 + 1] = v[j - 1][1] + (v[j][1] - v[j - 1][1]) * u; }
    return o;
  }
  // A figure: N thin strands and two heavy lines (the second unseen when there is only one), fitted to the frame.
  function figure(lines, mains, round) {
    var all = lines.concat(mains.map(function (m) { return m.v; })), x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    all.forEach(function (v) { v.forEach(function (p) { if (p[0] < x0) x0 = p[0]; if (p[0] > x1) x1 = p[0]; if (p[1] < y0) y0 = p[1]; if (p[1] > y1) y1 = p[1]; }); });
    var p = all.map(function (v) { return resample(v.map(function (q) { return [(q[0] - x0) / (x1 - x0 || 1), 0.03 + 0.94 * (q[1] - y0) / (y1 - y0 || 1)]; })); });
    var a = new Float32Array(N + 2); for (var i = 0; i < N; i++) a[i] = 0.16;
    a[N] = mains[0].a || 0.95; if (mains[1]) a[N + 1] = mains[1].a || 0.95; else { p.push(p[N]); a[N + 1] = 0; }
    return { p: p, a: a, q: round ? 1 : 0 };
  }
  function graph(fn, p) { var v = []; for (var i = 0; i <= 96; i++) v.push([i / 96, fn(p, i / 96)]); return v; }
  // A family of curves of one formula: fn(p, x), p from 0 to 1 across the strands; the heavy lines are fn at m and m2.
  function family(fn, m, m2) {
    var lines = []; for (var j = 0; j < N; j++) lines.push(graph(fn, j / (N - 1)));
    return figure(lines, m2 == null ? [{ v: graph(fn, m) }] : [{ v: graph(fn, m) }, { v: graph(fn, m2) }]);
  }
  // Made-up paths: N thin ones and the heavy ones after them. shape(t, j) adds a pull to path j at time t.
  function paths(seed, steps, vol, drift, shape, heavy) {
    var r = rng(seed), out = [];
    for (var j = 0; j < N + heavy.length; j++) { var v = 0, p = [[0, 0]]; for (var i = 1; i <= steps; i++) { v += drift + vol * gauss(r) + (shape ? shape(i / steps, j) : 0); p.push([i / steps, v]); } out.push(p); }
    return figure(out.slice(0, N), heavy.map(function (a, k) { return { v: out[N + k], a: a }; }));
  }

  var FIGS = {
    "options-payoff": ["A call, strike 100 · its value from a year out to expiry", function () {
      return family(function (p, x) { return call(60 + 80 * x, 100, 0.28, p * p * 1.2, 0.03); }, 0); }],
    "black-scholes": ["Delta of a call, strike 100 · 48 expiries, a week to two years", function () {
      return family(function (p, x) { var S = 60 + 80 * x, T = 0.02 + p * p * 1.98, v = 0.28; return cdf((Math.log(S / 100) + (0.03 + v * v / 2) * T) / (v * Math.sqrt(T))); }, 0.35); }],
    "bond-calculator": ["Price against yield, 4% coupon · 48 maturities, 1 to 30 years", function () {
      return family(function (p, x) { return bond(0.005 + 0.095 * x, 1 + p * 29, 0.04); }, 9 / 29); }],
    "yield-to-maturity": ["A ten-year 4% bond pulled to par · 48 yields, 0.5% to 9.5%", function () {
      return family(function (p, x) { return bond(0.005 + p * 0.09, 10 * (1 - x), 0.04); }, 0.61); }],
    "portfolio-analyser": ["Illustrative · 48 paths a portfolio might take over a year", function () {
      return paths(7, 52, 0.022, 0.0016, null, [0.95]); }],
    "risk-correlation": ["Illustrative · nine companies, more strands between those that move together", function () {
      var r = rng(11), n = 9, P = [], pairs = [], lines = [], ring = [], i, k;
      for (i = 0; i < n; i++) { var a = i / n * 6.2832 - 1.5708; P.push([Math.cos(a), Math.sin(a)]); }
      for (i = 0; i < n; i++) for (k = i + 1; k < n; k++) pairs.push([i, k, r() * r()]);
      pairs.sort(function (x, y) { return y[2] - x[2]; });
      for (i = 0; lines.length < N; i = (i + 1) % 14) {   // the closest pairs get the most strands
        var A = P[pairs[i][0]], B = P[pairs[i][1]], cx = (r() - 0.5) * 0.7, cy = (r() - 0.5) * 0.7, v = [];
        for (k = 0; k <= 24; k++) { var t = k / 24, u = 1 - t; v.push([u * u * A[0] + 2 * u * t * cx + t * t * B[0], u * u * A[1] + 2 * u * t * cy + t * t * B[1]]); }
        lines.push(v);
      }
      for (i = 0; i <= 96; i++) ring.push([Math.cos(i / 96 * 6.2832 - 1.5708), Math.sin(i / 96 * 6.2832 - 1.5708)]);
      return figure(lines, [{ v: ring, a: 0.5 }], true); }],
    "efficient-frontier": ["Two assets, risk across and return up · 48 correlations, " + MINUS + "1 to +1", function () {
      function mix(rho) { var v = []; for (var i = 0; i <= 96; i++) { var a = i / 96, sa = 0.3, sb = 0.11; v.push([Math.sqrt(Math.max(0, a * a * sa * sa + (1 - a) * (1 - a) * sb * sb + 2 * a * (1 - a) * rho * sa * sb)), a]); } return v; }
      var lines = []; for (var j = 0; j < N; j++) lines.push(mix(-1 + 2 * j / (N - 1)));
      lines.push([[0, 0], [0, 1]]);   // risk is measured from zero
      var f = figure(lines, [{ v: mix(0.3) }]); f.p.splice(N, 1); return f; }],
    "position-sizing": ["A day's gain or loss · 48 volatilities, the widest four times the narrowest", function () {
      return family(function (p, x) { var s = 0.09 + p * 0.27, z = (x - 0.5) / s; return Math.exp(-z * z / 2) / s; }, 0.3); }],
    "dcf": ["A cash flow growing 6% a year, in today's money · 48 discount rates, 2% to 22%", function () {
      return family(function (p, x) { return Math.pow(1.06 / (1.02 + p * 0.2), x * 12); }, 0.3); }],
    "compound-growth": ["Thirty years of compounding · 48 returns, 0% to 11.5% a year", function () {
      return family(function (p, x) { return Math.pow(1 + p * 0.115, x * 30); }, 7 / 11.5); }],
    "real-return": ["7% a year for thirty years, before and after inflation · 48 rates, 0% to 9%", function () {
      return family(function (p, x) { return Math.pow(1.07 / (1 + p * 0.09), x * 30); }, 0, 2.5 / 9); }],
    "trading-simulator": ["Illustrative · 48 ways two years might go, and the one you get", function () {
      return paths(3, 120, 0.03, 0.002, null, [0.95]); }],
    "panic-test": ["Illustrative · 48 crashes and what came after", function () {
      return paths(5, 120, 0.014, 0, function (t, j) { var d = 0.25 + (j * 37 % 20) / 60; return t < 0.4 ? -0.056 * d : t < 0.5 ? -0.004 : 0.018 * d; }, [0.95]); }],
    "guess-the-fed": ["Illustrative · 48 paths of the Fed's target over ten months", function () {
      var r = rng(9), lines = [];
      function steps(moves, v) { var p = [[0, v]]; moves.forEach(function (m, i) { p.push([(i + 1) / 10, v]); v = Math.max(0.04, Math.min(0.96, v + m)); if (m) p.push([(i + 1) / 10, v]); }); return p; }
      for (var j = 0; j < N; j++) { var mv = []; for (var i = 0; i < 10; i++) { var d = r(); mv.push(d < 0.3 ? -0.06 : d > 0.72 ? 0.06 : 0); } lines.push(steps(mv, 0.25 + r() * 0.5)); }
      return figure(lines, [{ v: steps([0.06, 0.06, 0.06, 0, 0, 0, -0.06, -0.06, 0, -0.06], 0.42) }]); }],
    "portfolio-builder": ["Illustrative · the same ten years in 48 mixes, from all bonds to all stocks", function () {
      var r = rng(21), s = [], b = [], i;
      for (i = 0; i < 120; i++) { s.push(0.0075 + 0.045 * gauss(r)); b.push(0.003 + 0.012 * gauss(r)); }
      function mixed(w) { var v = 0, p = [[0, 0]]; for (var k = 0; k < 120; k++) { v += w * s[k] + (1 - w) * b[k]; p.push([(k + 1) / 120, v]); } return p; }
      var lines = []; for (i = 0; i < N; i++) lines.push(mixed(i / (N - 1)));
      return figure(lines, [{ v: mixed(0.6) }]); }],
    "your-fund": ["Illustrative · a fund and, fainter, the index it is measured against", function () {
      return paths(31, 120, 0.012, 0.0014, null, [0.95, 0.5]); }]
  };

  // The tools, read from the list below: only those with a figure of their own.
  var tools = [], names = document.createElement("nav");
  names.className = "tf__names"; names.setAttribute("aria-label", head.querySelector(".page__title").textContent + ", with a figure for each");
  [].forEach.call(list.querySelectorAll(".archive__month"), function (sec) {
    var h = sec.querySelector("h2"), g = null;
    [].forEach.call(sec.querySelectorAll("li a"), function (a) {
      var slug = a.getAttribute("href").replace(/\//g, ""), t = a.querySelector(".learn-list__title"), d = a.querySelector(".learn-list__desc");
      if (!FIGS[slug] || !t) return;
      if (!g && h) { g = document.createElement("p"); g.className = "tf__group"; g.textContent = h.textContent; names.appendChild(g); }
      var n = document.createElement("a"); n.href = a.getAttribute("href"); n.textContent = t.textContent; names.appendChild(n);
      tools.push({ slug: slug, href: n.href, title: t.textContent, desc: d ? d.textContent : "", read: FIGS[slug][0], make: FIGS[slug][1], name: n });
    });
  });
  if (tools.length < 3) return;

  var box = document.createElement("div"); box.className = "tf" + (tools.length <= 6 ? " tf--few" : "");
  var stage = document.createElement("div"); stage.className = "tf__stage";
  stage.innerHTML = '<a class="tf__fig" tabindex="-1" aria-hidden="true"><canvas></canvas></a>' +
    '<div class="tf__foot"><p class="lens-read tf__read"></p><p class="lens-read tf__step"><span></span><button type="button">Next</button></p></div>' +
    '<p class="tf__title"><a></a></p><p class="tf__desc"></p><a class="link tf__open">Open</a>';
  box.appendChild(names); box.appendChild(stage);
  var down = document.createElement("a"); down.className = "lib-map__down tf__down"; if (!list.id) list.id = "all-tools"; down.href = "#" + list.id;
  down.textContent = "All " + tools.length + " in a list";
  head.parentNode.insertBefore(box, head.nextSibling); box.parentNode.insertBefore(down, box.nextSibling);
  document.querySelector("main").classList.add("has-figure");
  var fig = stage.querySelector(".tf__fig"), cv = fig.querySelector("canvas"), c = cv.getContext("2d"), read = stage.querySelector(".tf__read"),
    count = stage.querySelector(".tf__step span"), next = stage.querySelector(".tf__step button"), title = stage.querySelector(".tf__title a"),
    desc = stage.querySelector(".tf__desc"), open = stage.querySelector(".tf__open");

  var cur = null, from = null, to = null, at = -1, t0 = 0, raf = 0, W = 0, H = 0;
  function copy(f) { return { p: f.p.map(function (s) { return new Float32Array(s); }), a: new Float32Array(f.a), q: f.q }; }
  function fit() {
    var d = Math.min(window.devicePixelRatio || 1, 2), w = cv.clientWidth, h = cv.clientHeight; if (!w || !h) return;
    W = w; H = h; cv.width = Math.round(w * d); cv.height = Math.round(h * d); c.setTransform(d, 0, 0, d, 0, 0); draw();
  }
  function draw() {
    if (!cur || !W) return;
    c.clearRect(0, 0, W, H); c.globalCompositeOperation = "lighter"; c.lineJoin = "round";
    var side = Math.min(W, H), ox = (W - side) / 2, oy = (H - side) / 2, q = cur.q, m = 2;   // q: how far the frame is a square (the ring)
    for (var s = 0; s < N + 2; s++) {
      var a = cur.a[s], p = cur.p[s]; if (a < 0.004) continue;
      c.beginPath();
      for (var i = 0; i < M; i++) {
        var x = p[i * 2], y = 1 - p[i * 2 + 1], px = m + x * (W - 2 * m), py = m + y * (H - 2 * m);
        if (q) { px += (ox + m + x * (side - 2 * m) - px) * q; py += (oy + m + y * (side - 2 * m) - py) * q; }
        if (i) c.lineTo(px, py); else c.moveTo(px, py);
      }
      c.strokeStyle = "rgba(" + INK + "," + a.toFixed(3) + ")"; c.lineWidth = s < N ? 0.7 : 1.5; c.stroke();
    }
  }
  function tick(now) {
    var k = Math.min(1, (now - t0) / 750), e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
    for (var s = 0; s < N + 2; s++) { var f = from.p[s], g = to.p[s], o = cur.p[s]; for (var i = 0; i < M * 2; i++) o[i] = f[i] + (g[i] - f[i]) * e; cur.a[s] = from.a[s] + (to.a[s] - from.a[s]) * e; }
    cur.q = from.q + (to.q - from.q) * e; draw();
    raf = k < 1 ? requestAnimationFrame(tick) : 0;
  }
  function show(i) {
    if (i === at) return;
    var t = tools[i]; if (!t.fig) t.fig = t.make();
    if (at >= 0) tools[at].name.classList.remove("is-on");
    at = i; t.name.classList.add("is-on");
    read.textContent = t.read; count.textContent = (i + 1) + " / " + tools.length; title.textContent = t.title; desc.textContent = t.desc;
    title.href = fig.href = open.href = t.href; open.textContent = "Open " + t.title;
    to = t.fig;
    if (still) { cur = copy(to); draw(); return; }
    if (!cur) { cur = copy(to); for (var s = 0; s < N + 2; s++) cur.a[s] = 0; }   // the first one draws in from nothing
    from = copy(cur); t0 = performance.now(); if (!raf) raf = requestAnimationFrame(tick);
  }

  // It goes through the tools by itself until the reader takes over, and only while it can be seen.
  var auto = !still, seen = true, timer = 0;
  function turn() { clearTimeout(timer); if (auto && seen && !document.hidden) timer = setTimeout(function () { show((at + 1) % tools.length); turn(); }, 4200); }
  function take() { auto = false; clearTimeout(timer); }
  tools.forEach(function (t, i) {
    t.name.addEventListener("pointerenter", function () { take(); show(i); });
    t.name.addEventListener("focus", function () { take(); show(i); });
  });
  next.addEventListener("click", function () { take(); show((at + 1) % tools.length); });
  if ("IntersectionObserver" in window) new IntersectionObserver(function (e) { seen = e[0].isIntersecting; turn(); }).observe(box);
  document.addEventListener("visibilitychange", turn);
  if ("ResizeObserver" in window) new ResizeObserver(fit).observe(cv); else window.addEventListener("resize", fit);
  show(0); fit(); turn();
})();
