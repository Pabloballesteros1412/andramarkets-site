/* Tools: two atoms (owner, 25 Nov 2026: "two atoms, the same size"). The Lab at the left and Simulators at the
   right, each an atom of light: a nucleus, and round it one orbit for each of its themes (four for the Lab: options,
   bonds, risk and portfolio, valuation and growth; two for Simulators: market replays, strategy games), with that
   theme's tools as the electrons on it. Each electron carries its tool's name and is its link; the atom's name under
   it, and its nucleus, open the Lab or Simulators page. The electrons go slowly round; a name fades as its electron
   passes near the nucleus, where the orbits cross, and returns as it comes out. Pointing at an atom, or reaching it
   with the keyboard, stops it; pointing at a tool lights its orbit and names its theme. Both atoms are drawn to the
   same radius. On a phone they stand one over the other, and each shows one orbit's names at a time, lit, with its
   theme under the atom's name, moving on to the next orbit every few seconds. The nested list of links is the page's own markup: this
   script lays it out, and without it the list stays a list. */
(function () {
  "use strict";
  var nav = document.querySelector(".atoms"); if (!nav || !document.createElement("canvas").getContext) return;
  var items = [].slice.call(nav.querySelectorAll(":scope > ol > li")); if (!items.length) return;
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches, TAU = Math.PI * 2, INK = "214,228,255";
  var seed = 7; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
  var want = location.hash.slice(1);

  var atoms = items.map(function (li, n) {
    var box = document.createElement("div"), stage = document.createElement("div"), cv = document.createElement("canvas");
    box.className = "atom"; stage.className = "atom__stage"; stage.appendChild(cv); box.appendChild(stage);
    var name = li.querySelector(":scope > .atoms__name"), sub = li.querySelector(":scope > .atoms__sub");
    var core = document.createElement("a"); core.className = "atom__core"; core.href = name.getAttribute("href"); core.tabIndex = -1; core.setAttribute("aria-hidden", "true"); stage.appendChild(core);
    var themes = [].slice.call(li.querySelectorAll(":scope > ol > li")), electrons = [];
    // Every atom has the same number of orbits, so that both are as full: a theme takes as many of them as its share
    // of the tools (the Lab's four themes one each; Simulators' two themes two each), its tools dealt among them.
    var ORB = Math.max(4, themes.length), counts = themes.map(function (th) { return th.querySelectorAll("a").length; }), take = themes.map(function () { return 1; }), left = ORB - themes.length;
    while (left-- > 0) { var best = 0; counts.forEach(function (c, i) { if (c / take[i] > counts[best] / take[best]) best = i; }); take[best]++; }
    var specs = []; themes.forEach(function (th, i) { var links = [].slice.call(th.querySelectorAll("a")), group = []; for (var q = 0; q < take[i]; q++) specs.push({ th: th, group: group, links: links.filter(function (a, j) { return j % take[i] === q; }) }); });
    var N = specs.length;
    var orbits = specs.map(function (sp, i) { var th = sp.th;
      // the orbits fan evenly either side of level; each is a few fine strands, set a little apart
      var tilt = (i - (N - 1) / 2) * (N > 2 ? 0.7 : 1.0), strands = [];
      for (var k = 0; k < 20; k++) strands.push({ rx: (rnd() - 0.5) * 0.08, ry: (rnd() - 0.5) * 0.06, t: (rnd() - 0.5) * 0.05, a: k ? 0.09 : 0.5 });
      var o = { tilt: tilt, strands: strands, name: th.querySelector(".atoms__theme").textContent, key: th.getAttribute("data-key"), sp: (i % 2 ? -1 : 1) * (0.05 + rnd() * 0.03), lit: 0, n: sp.links.length };
      var links = sp.links, m = links.length; sp.group.push(o);
      links.forEach(function (a, j) {
        // spread round the orbit, started clear of the nucleus
        var e = { o: o, a: a, u0: (m === 4 ? Math.PI / 4 : m === 3 ? 0.5 : m === 2 ? 0.45 : 0.3) + j * TAU / m + i * 0.35 };
        a.className = "atom__tool"; stage.appendChild(a); electrons.push(e);
        function on() { sp.group.forEach(function (g) { g.lit = 1; }); subline.textContent = o.name; }
        function off() { sp.group.forEach(function (g) { g.lit = g.key === want ? 1 : 0; }); subline.textContent = base; }
        a.addEventListener("pointerenter", on); a.addEventListener("pointerleave", off); a.addEventListener("focus", on); a.addEventListener("blur", off);
      });
      if (o.key === want) o.lit = 1;
      return o;
    });
    var foot = document.createElement("div"); foot.className = "atom__foot"; name.className = "atom__name"; foot.appendChild(name);
    var subline = document.createElement("p"); subline.className = "lens-read atom__sub"; var base = sub ? sub.textContent : ""; subline.textContent = base; subline.setAttribute("aria-live", "off"); foot.appendChild(subline);
    box.appendChild(foot); nav.appendChild(box);
    var at = { box: box, stage: stage, cv: cv, c: cv.getContext("2d"), orbits: orbits, electrons: electrons, sub: subline, base: base, turn: undefined, t: n * 40, held: false, R: 0, S: 0 };
    box.addEventListener("pointerenter", function () { at.held = true; }); box.addEventListener("pointerleave", function () { at.held = false; });
    box.addEventListener("focusin", function () { at.held = true; }); box.addEventListener("focusout", function () { at.held = false; });
    return at;
  });
  nav.querySelector(":scope > ol").remove(); nav.classList.add("is-live"); document.querySelector("main").classList.add("has-atoms");

  function size() {
    var d = Math.min(window.devicePixelRatio || 1, 2);
    atoms.forEach(function (at) { at.d = d;
      var w = at.stage.clientWidth, h = at.stage.clientHeight; if (!w) return;
      at.S = w; at.H = h; at.narrow = w < 520; at.R = at.narrow ? w * 0.29 : Math.min(w * 0.4, h * 0.46, 210);
      at.electrons.forEach(function (e) { e.w = e.a.offsetWidth; });   // one radius for both: the stages are the same size
      at.cv.width = Math.round(w * d); at.cv.height = Math.round(h * d); at.c.setTransform(d, 0, 0, d, 0, 0);
      if (!at.oc) { at.oc = document.createElement("canvas"); at.ox = at.oc.getContext("2d"); }
      at.oc.width = at.cv.width; at.oc.height = at.cv.height; at.ox.setTransform(d, 0, 0, d, 0, 0); at.okey = null;
    });
    frame(0);
  }
  function glow(c, x, y, r, a) { var g = c.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, "rgba(255,255,255," + a + ")"); g.addColorStop(0.25, "rgba(" + INK + "," + a * 0.35 + ")"); g.addColorStop(1, "rgba(" + INK + ",0)"); c.fillStyle = g; c.beginPath(); c.arc(x, y, r, 0, TAU); c.fill(); }
  function draw(at) {
    var c = at.c, R = at.R, cx = at.S / 2, cy = at.H / 2; if (!R) return;
    c.clearRect(0, 0, at.S, at.H); c.globalCompositeOperation = "lighter";
    var turn = at.narrow && !still ? at.orbits[Math.floor(at.t / 4) % at.orbits.length] : null; if (turn && !turn.n) turn = null;   // a phone: the orbit whose names show
    if (turn !== at.turn) { at.turn = turn; at.orbits.forEach(function (o) { o.lit = turn ? (o === turn ? 1 : 0) : (o.key === want ? 1 : 0); }); at.sub.textContent = turn ? turn.name : at.base; }
    // The orbits and the nucleus's glow stand still: they are drawn once to a canvas of their own, and again only when an
    // orbit is lit or put out, or the size changes. Light adds, so the picture is the same as drawing them every frame.
    var key = at.orbits.map(function (o) { return o.lit; }).join();
    if (key !== at.okey) { at.okey = key; var c0 = c; c = at.ox; c.clearRect(0, 0, at.S, at.H); c.globalCompositeOperation = "lighter";
    at.orbits.forEach(function (o) {
      o.strands.forEach(function (s) {
        var rx = R * (1 + s.rx), ry = R * (0.3 + s.ry), ct = Math.cos(o.tilt + s.t), st = Math.sin(o.tilt + s.t);
        c.beginPath(); for (var k = 0; k <= 72; k++) { var u = k / 72 * TAU, x = rx * Math.cos(u), y = ry * Math.sin(u); if (k) c.lineTo(cx + x * ct - y * st, cy + x * st + y * ct); else c.moveTo(cx + x * ct - y * st, cy + x * st + y * ct); }
        c.strokeStyle = "rgba(" + INK + "," + (s.a * (o.lit ? 2.4 : 1)).toFixed(3) + ")"; c.lineWidth = s.a > 0.3 ? 1.1 : 0.7; c.stroke();
      });
    });
    glow(c, cx, cy, R * 0.5, 0.45); glow(c, cx, cy, R * 0.16, 1); c = c0; }
    c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(at.oc, 0, 0); c.setTransform(at.d, 0, 0, at.d, 0, 0);
    c.fillStyle = "rgba(255,255,255,.92)"; for (var q = 0; q < 7; q++) { var a = q * 2.4 + at.t * 0.2, d = q ? R * 0.03 : 0; c.beginPath(); c.arc(cx + Math.cos(a) * d, cy + Math.sin(a) * d, R * 0.016 + 1.2, 0, TAU); c.fill(); }
    at.electrons.forEach(function (e) {
      var o = e.o, u = e.u0 + at.t * o.sp, x = R * Math.cos(u), y = R * 0.3 * Math.sin(u), ct = Math.cos(o.tilt), st = Math.sin(o.tilt), dx = x * ct - y * st, dy = x * st + y * ct, far = Math.hypot(dx, dy) / R;
      glow(c, cx + dx, cy + dy, 15, 0.9); c.fillStyle = "#fff"; c.beginPath(); c.arc(cx + dx, cy + dy, 2.6, 0, TAU); c.fill();
      // its name: outward of the electron, sliding from one side of it to the other as it crosses the middle
      var k = Math.max(-1, Math.min(1, dx / (R * 0.3))), up = Math.max(-1, Math.min(1, dy / (R * 0.3))), s = e.a.style, see = turn && o !== turn ? 0 : Math.max(0, Math.min(1, (far - (turn ? 0.3 : 0.5)) / 0.22));
      var lx = cx + dx + k * 14 + (-0.5 + 0.5 * k) * e.w;   // the name's left edge; on a phone it never leaves the screen
      if (at.narrow) lx = Math.max(2, Math.min(at.S - e.w - 2, lx));
      s.left = lx + "px"; s.top = (cy + dy + (1 - Math.abs(k)) * up * 22) + "px";
      s.transform = "translate(0,-50%)"; s.textAlign = k > 0.5 ? "left" : k < -0.5 ? "right" : "center";
      s.opacity = (document.activeElement === e.a ? 1 : see).toFixed(2); s.pointerEvents = see > 0.4 ? "auto" : "none";
    });
  }
  var last = 0, run = 0, seen = true;
  function frame(now) {
    var dt = last && now ? Math.min(0.05, (now - last) / 1000) : 0; last = now;
    atoms.forEach(function (at) { if (!at.held && !still) at.t += dt; draw(at); });
    run = !still && seen && !document.hidden ? requestAnimationFrame(frame) : 0;
  }
  function wake() { if (!run && !still && seen && !document.hidden) { last = 0; run = requestAnimationFrame(frame); } }
  if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { seen = en[0].isIntersecting; wake(); }).observe(nav);
  document.addEventListener("visibilitychange", wake);
  if ("ResizeObserver" in window) new ResizeObserver(size).observe(nav); else window.addEventListener("resize", size);
  size(); wake();
})();
