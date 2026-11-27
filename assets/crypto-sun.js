/* Crypto: the Bitcoin system (owner, 27 Nov 2026: the Bitcoin sun, then "more coins in the rings, and far more
   real"). Over the table of the hundred largest coins, a solar system in the site's sky, seen from a little above
   its plane and in perspective. Bitcoin is the sun: a WebGL disc whose surface boils (cells of light, darker at
   the limb) inside a corona of streamers. The twenty-four largest coins after it are planets, the larger the
   nearer, each a sphere with a surface of its own (banded if large, mottled if small, a grey cratered moon when
   it is pegged to a currency), lit by the sun exactly: full when beyond it, a crescent when between it and us,
   with a thin lit air at the edge. The rest of the hundred are the belt beyond the planets, a grain each. Every
   body is a row of the table and carries that row's figures: its size is its market value, and a press goes to
   its row. The turning (near orbits faster) is the one thing that is not data, and the line under the picture
   says so. Pointing at a body stops the system and lights its orbit. A phone sees the system from higher up, with
   fewer names. Without WebGL the sun is drawn flat; without this script the page is the table. */
(function () {
  "use strict";
  var box = document.querySelector(".cs"), trs = [].slice.call(document.querySelectorAll(".cs-tab tbody tr")); if (!box || trs.length < 12) return;
  var back = box.querySelector("canvas"), bx = back.getContext && back.getContext("2d"), layer = box.querySelector(".cs__names"); if (!bx) return;
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches, TAU = Math.PI * 2, AMB = "255,176,72";
  function hash(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function rng(s) { return function () { s = (s + 0x6D2B79F5) >>> 0; var t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  var rnd = rng(23);
  function read(tr) { return { id: tr.id, name: tr.querySelector(".cs-name").textContent, cap: +tr.getAttribute("data-cap"), capText: tr.querySelector(".cs-cap").textContent,
    price: tr.querySelector(".cs-price").textContent, day: tr.querySelector(".cs-day").innerHTML, stable: tr.hasAttribute("data-stable") }; }
  var all = trs.map(read), sun = all[0], NP = Math.min(+box.getAttribute("data-planets") || 24, all.length - 1), planets = all.slice(1, NP + 1), belt = all.slice(NP + 1), top = planets[0].cap;

  // the layers: what is behind the sun, the sun, what is in front of it, then the names
  var glc = document.createElement("canvas"); glc.className = "cs__sunface"; var front = document.createElement("canvas"); front.className = "cs__front";
  box.insertBefore(glc, layer); box.insertBefore(front, layer); var fx = front.getContext("2d");
  box.hidden = false; document.querySelector("main").classList.add("has-sun");

  // A planet's surface: a small map of latitude and longitude, made once from the coin's own name.
  var PAL = [[[226, 196, 150], [150, 104, 62]], [[214, 170, 120], [120, 70, 44]], [[232, 222, 204], [150, 138, 120]], [[196, 150, 108], [92, 60, 44]], [[222, 206, 170], [128, 112, 80]],
    [[206, 188, 176], [112, 92, 88]], [[236, 208, 160], [170, 120, 60]], [[184, 176, 160], [84, 80, 72]], [[210, 178, 150], [104, 76, 68]], [[190, 198, 188], [92, 104, 98]]];
  var MW = 64, MH = 32;
  function surface(k) {
    var r = rng(hash(k.id)), pal = k.stable ? [[196, 194, 188], [92, 90, 86]] : PAL[Math.floor(r() * PAL.length)], gas = !k.stable && k.cap > top * 0.045, m = new Uint8ClampedArray(MW * MH * 3), x, y, i;
    var bands = [], spots = []; for (i = 0; i < 9; i++) bands.push({ f: 1 + r() * 7, p: r() * TAU, a: r() });
    for (i = 0; i < (k.stable ? 26 : 14); i++) spots.push({ x: r() * MW, y: r() * MH, s: 1.5 + r() * (k.stable ? 4 : 6), d: r() < 0.6 ? -1 : 1 });
    for (y = 0; y < MH; y++) for (x = 0; x < MW; x++) {
      var v = 0.5, lat = y / MH * Math.PI;
      if (gas) { for (i = 0; i < 9; i++) v += Math.sin(lat * bands[i].f * 2 + bands[i].p + Math.sin(x / MW * TAU * 2 + bands[i].p) * 0.25) * 0.09 * bands[i].a; }
      else { for (i = 0; i < 5; i++) v += Math.sin(x / MW * TAU * Math.round(bands[i].f) + bands[i].p) * Math.sin(lat * bands[i].f + bands[i].p * 2) * 0.07; }
      for (i = 0; i < spots.length; i++) { var dx = Math.min(Math.abs(x - spots[i].x), MW - Math.abs(x - spots[i].x)), dy = y - spots[i].y, q = (dx * dx + dy * dy) / (spots[i].s * spots[i].s); if (q < 1) v += spots[i].d * (1 - q) * (k.stable ? 0.3 : gas ? 0.08 : 0.2); }
      v = Math.max(0, Math.min(1, v)); var o = (y * MW + x) * 3;
      m[o] = pal[1][0] + (pal[0][0] - pal[1][0]) * v; m[o + 1] = pal[1][1] + (pal[0][1] - pal[1][1]) * v; m[o + 2] = pal[1][2] + (pal[0][2] - pal[1][2]) * v;
    }
    k.map = m; k.spin = 0.25 + r() * 0.5; k.air = k.stable ? 0 : 0.35 + r() * 0.4;
  }
  planets.forEach(function (k, n) {
    k.n = n; k.u = rnd() * TAU; surface(k); k.cv = document.createElement("canvas"); k.cx = k.cv.getContext("2d"); k.age = 99;
    var a = document.createElement("a"); a.className = "cs__name" + (k.stable ? " is-pegged" : "") + (n >= 12 ? " is-small" : ""); a.href = "#" + k.id;
    a.innerHTML = "<b></b><span class=\"lens-read\"></span>"; a.firstChild.textContent = k.name; a.lastChild.innerHTML = k.capText + " · " + k.day; layer.appendChild(a); k.el = a;
    a.addEventListener("pointerenter", function () { pick = k; }); a.addEventListener("pointerleave", function () { if (pick === k) pick = null; });
    a.addEventListener("focus", function () { pick = k; }); a.addEventListener("blur", function () { if (pick === k) pick = null; });
  });
  belt.forEach(function (k) { k.u = rnd() * TAU; k.dr = rnd(); k.dy = (rnd() - 0.5); k.b = 0.5 + rnd() * 0.5; });
  var mid = document.createElement("a"); mid.className = "cs__sun"; mid.href = "#" + sun.id; mid.innerHTML = "<b></b><span class=\"lens-read\"></span>";
  mid.firstChild.textContent = sun.name; mid.lastChild.innerHTML = sun.price + " · " + sun.day; layer.appendChild(mid);
  var tip = document.createElement("a"); tip.className = "cs__name cs__tip"; tip.innerHTML = "<b></b><span class=\"lens-read\"></span>"; tip.style.opacity = 0; layer.appendChild(tip);

  // The sun's face, in WebGL: cells of light that boil, a darker limb, a corona of streamers.
  var gl = null, prog, uT, uR;
  try { gl = glc.getContext("webgl", { premultipliedAlpha: false, alpha: true, antialias: false }); } catch (e) { gl = null; }
  if (gl) {
    var VS = "attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}";
    var FS = "precision highp float;uniform float t;uniform vec2 res;" +
      "float h(vec3 p){p=fract(p*.3183099+.1);p*=17.;return fract(p.x*p.y*p.z*(p.x+p.y+p.z));}" +
      "float n(vec3 x){vec3 i=floor(x),f=fract(x);f=f*f*(3.-2.*f);return mix(mix(mix(h(i),h(i+vec3(1,0,0)),f.x),mix(h(i+vec3(0,1,0)),h(i+vec3(1,1,0)),f.x),f.y),mix(mix(h(i+vec3(0,0,1)),h(i+vec3(1,0,1)),f.x),mix(h(i+vec3(0,1,1)),h(i+vec3(1,1,1)),f.x),f.y),f.z);}" +
      "float fbm(vec3 p){float a=.5,s=0.;for(int i=0;i<5;i++){s+=a*n(p);p=p*2.03+7.1;a*=.5;}return s;}" +
      "void main(){vec2 uv=(gl_FragCoord.xy-.5*res)/res.y*12.;float r=length(uv);vec3 col=vec3(0.);float a=0.;" +
      "if(r<1.){float z=sqrt(1.-r*r);vec3 sp=vec3(uv,z);float g=fbm(sp*3.4+vec3(0.,0.,t*.06));float c=fbm(sp*24.+vec3(t*.07,g*3.,-t*.11));float c2=fbm(sp*9.+vec3(-t*.04,2.,t*.05));" +
      "float cell=smoothstep(.38,.62,c)*.7+smoothstep(.35,.7,c2)*.3;float limb=pow(z,.5);vec3 hot=mix(vec3(1.,.60,.16),vec3(1.,.86,.50),cell);hot=mix(hot,vec3(1.,.97,.88),smoothstep(.5,.78,g)*.55);" +
      "float spot=smoothstep(.27,.2,fbm(sp*2.2+vec3(3.,t*.015,1.)));hot*=1.-spot*.3;col=hot*(.5+.62*limb);a=1.;}" +
      "float ang=atan(uv.y,uv.x);float st=fbm(vec3(ang*3.2,r*.9-t*.11,t*.05))*.75+fbm(vec3(ang*9.,r*2.-t*.16,3.))*.25;" +
      "float d=max(r-1.,0.);float cor=exp(-d*1.7)*(.42+st*.85)+exp(-d*.5)*(.16+.14*st)+exp(-d*9.)*.95;" +
      "vec3 cc=mix(vec3(1.,.56,.14),vec3(1.,.9,.66),exp(-d*4.));float edge=smoothstep(6.,3.2,r);" +
      "if(r>=1.){col=cc*cor*edge;a=clamp(cor*edge,0.,1.);}else{col+=cc*.16;}" +
      "gl_FragColor=vec4(col,a);}";
    var mk = function (type, src) { var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return gl.getShaderParameter(s, gl.COMPILE_STATUS) ? s : null; };
    var v = mk(gl.VERTEX_SHADER, VS), f = mk(gl.FRAGMENT_SHADER, FS);
    if (v && f) {
      prog = gl.createProgram(); gl.attachShader(prog, v); gl.attachShader(prog, f); gl.linkProgram(prog); gl.useProgram(prog);
      var buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
      var loc = gl.getAttribLocation(prog, "p"); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
      uT = gl.getUniformLocation(prog, "t"); uR = gl.getUniformLocation(prog, "res");
    } else gl = null;
  }
  if (!gl) glc.style.display = "none";

  var W = 0, H = 0, D = 1, cx = 0, cy = 0, R0 = 0, R1 = 0, RB = 0, SR = 0, SQ = 0.34, CQ = 0.94, TILT = -0.16, CAM = 1, narrow = false, pick = null, t = 0, last = 0, run = 0, seen = true, orbits = null;
  // a point of the plane (radius, angle, height) on the screen: [x, y, scale, depth towards us]
  function at(R, u, yUp) {
    var X = R * Math.cos(u), Z = R * Math.sin(u), Y = yUp || 0, dep = Z * CQ + Y * SQ, f = CAM / (CAM - dep), sx = X * f, sy = (Z * SQ - Y * CQ) * f, ct = Math.cos(TILT), st = Math.sin(TILT);
    return [cx + sx * ct - sy * st, cy + sx * st + sy * ct, f, dep];
  }
  function size() {
    D = Math.min(window.devicePixelRatio || 1, 2); W = box.clientWidth; H = box.clientHeight; if (!W) return;
    narrow = W < 900; SQ = narrow ? 0.66 : 0.36; CQ = Math.sqrt(1 - SQ * SQ); TILT = narrow ? -0.3 : -0.15;
    cx = W / 2; cy = H * (narrow ? 0.45 : 0.46); SR = narrow ? 30 : Math.min(50, H * 0.078);
    RB = narrow ? W * 0.5 : Math.min(W * 0.455, (H * 0.4) / SQ); R1 = RB * 0.84; R0 = SR * (narrow ? 1.75 : 2.3); CAM = RB * 3.4;
    planets.forEach(function (k, n) { k.R = R0 + (R1 - R0) * Math.pow(n / (planets.length - 1), 0.86); k.r = Math.max(narrow ? 2.2 : 2.8, SR * 0.36 * Math.pow(k.cap / top, 0.36)); k.sp = 0.06 * Math.pow(R0 / k.R, 1.5); k.w = 0; k.age = 99; });
    belt.forEach(function (k) { k.R = RB * (0.9 + k.dr * 0.12); k.sp = 0.06 * Math.pow(R0 / k.R, 1.5); });
    [back, front].forEach(function (cv) { cv.width = Math.round(W * D); cv.height = Math.round(H * D); cv.getContext("2d").setTransform(D, 0, 0, D, 0, 0); });
    var S = SR * 12; glc.style.width = glc.style.height = S + "px"; glc.style.left = (cx - S / 2) + "px"; glc.style.top = (cy - S / 2) + "px"; glc.width = glc.height = Math.round(S * D);
    if (gl) { gl.viewport(0, 0, glc.width, glc.height); gl.uniform2f(uR, glc.width, glc.height); }
    mid.style.left = cx + "px"; mid.style.top = (cy + SR + (narrow ? 28 : 44)) + "px";
    // the orbits do not move: drawn once, the near side brighter than the far
    orbits = document.createElement("canvas"); orbits.width = back.width; orbits.height = back.height; var oc = orbits.getContext("2d"); oc.setTransform(D, 0, 0, D, 0, 0); oc.lineWidth = 0.7;
    planets.forEach(function (k) { for (var n = 0; n < 144; n++) { var a = at(k.R, n / 144 * TAU), b = at(k.R, (n + 1) / 144 * TAU), near = 0.5 + 0.5 * Math.sin(n / 144 * TAU);
      oc.strokeStyle = "rgba(" + AMB + "," + (0.07 + 0.2 * near).toFixed(3) + ")"; oc.beginPath(); oc.moveTo(a[0], a[1]); oc.lineTo(b[0], b[1]); oc.stroke(); } });
    draw();
  }
  // One planet, lit: every point of its disc from the map, by the angle between its surface and the sun.
  function shade(k, f) {
    var rad = Math.max(2, Math.round(k.r * f * D)), n = rad * 2 + 6, c = k.cx; if (k.cv.width !== n) { k.cv.width = k.cv.height = n; }
    var img = c.createImageData(n, n), px = img.data, cu = Math.cos(k.u), su = Math.sin(k.u), ct = Math.cos(TILT), st = Math.sin(TILT);
    var lx0 = -cu, ly0 = -su * SQ, lz = -su * CQ * 0.72 + 0.3, lx = lx0 * ct - ly0 * st, ly = lx0 * st + ly0 * ct, rot = t * k.spin, m = k.map, h = n / 2, x, y;
    for (y = 0; y < n; y++) for (x = 0; x < n; x++) {
      var nx = (x + 0.5 - h) / rad, ny = (y + 0.5 - h) / rad, r2 = nx * nx + ny * ny, o = (y * n + x) * 4;
      if (r2 > 1.14) continue;
      if (r2 >= 1) { var out = Math.sqrt(r2), lit0 = Math.max(0, (nx * lx + ny * ly) / out * 0.8 + lz * 0.2 + 0.25), a0 = k.air * lit0 * Math.max(0, 1 - (out - 1) / 0.14); px[o] = 255; px[o + 1] = 214; px[o + 2] = 160; px[o + 3] = a0 * 150; continue; }
      var nz = Math.sqrt(1 - r2), dif = Math.max(0, nx * lx + ny * ly + nz * lz), lon = Math.atan2(nx, nz) + rot, lat = Math.acos(Math.max(-1, Math.min(1, -ny)));
      var mx = ((Math.floor(lon / TAU * MW) % MW) + MW) % MW, my = Math.min(MH - 1, Math.floor(lat / Math.PI * MH)), q = (my * MW + mx) * 3;
      var li = 0.13 + 1.1 * Math.pow(dif, 0.75), rim = k.air * Math.pow(1 - nz, 3) * Math.min(1, dif * 3) * 0.9, edge = Math.min(1, (1 - Math.sqrt(r2)) * rad);
      px[o] = m[q] * li + 255 * rim; px[o + 1] = m[q + 1] * li + 196 * rim; px[o + 2] = m[q + 2] * li + 130 * rim; px[o + 3] = 255 * edge;
    }
    c.putImageData(img, 0, 0); k.half = n / 2 / D; k.age = 0;
  }
  function body(c, k) {
    var p = k.p, dim = pick && pick !== k ? 0.4 : 1;
    if (k.age > (pick === k ? 0 : 3)) shade(k, p[2]); k.age++;
    c.globalAlpha = dim; c.drawImage(k.cv, p[0] - k.half, p[1] - k.half, k.half * 2, k.half * 2); c.globalAlpha = 1;
  }
  function grain(c, k) { var p = k.p, lit = 0.55 + 0.45 * (0.5 - 0.5 * Math.sin(k.u)); c.fillStyle = "rgba(255," + Math.round(214 * k.b + 20) + "," + Math.round(160 * k.b) + "," + (lit * (pick && pick !== k ? 0.35 : 0.95)).toFixed(3) + ")"; c.beginPath(); c.arc(p[0], p[1], (pick === k ? 2.6 : 1.5) * p[2], 0, TAU); c.fill(); }
  function draw() {
    if (!W) return;
    bx.clearRect(0, 0, W, H); fx.clearRect(0, 0, W, H); if (orbits) bx.drawImage(orbits, 0, 0, W, H);
    if (pick && pick.R && pick.n != null) { bx.lineWidth = 1; bx.strokeStyle = "rgba(" + AMB + ",.7)"; bx.beginPath(); for (var n = 0; n <= 144; n++) { var a = at(pick.R, n / 144 * TAU); if (n) bx.lineTo(a[0], a[1]); else bx.moveTo(a[0], a[1]); } bx.stroke(); }
    belt.forEach(function (k) { k.p = at(k.R, k.u, k.dy * RB * 0.022); grain(Math.sin(k.u) < 0 ? bx : fx, k); });
    planets.slice().sort(function (a, b) { return Math.sin(a.u) - Math.sin(b.u); }).forEach(function (k) { k.p = at(k.R, k.u); k.backSide = Math.sin(k.u) < 0; body(k.backSide ? bx : fx, k); });
    if (gl) { gl.uniform1f(uT, t); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4); }
    else { var g = bx.createRadialGradient(cx, cy, 0, cx, cy, SR * 4); g.addColorStop(0, "#fff3dc"); g.addColorStop(0.24, "#ffb048"); g.addColorStop(0.26, "rgba(255,176,72,.5)"); g.addColorStop(1, "rgba(255,176,72,0)"); fx.fillStyle = g; fx.beginPath(); fx.arc(cx, cy, SR * 4, 0, TAU); fx.fill(); }
    // the names: outward of each body, the larger coins first; one gives way where it would cross another, the sun or Bitcoin's own
    var taken = [[cx - SR * 1.15, cy - SR * 1.15, cx + SR * 1.15, cy + SR * 1.15], [cx - (narrow ? 100 : 130), cy + SR + 8, cx + (narrow ? 100 : 130), cy + SR + (narrow ? 62 : 86)]];
    planets.forEach(function (k) {
      var p = k.p, side = p[0] >= cx ? 1 : -1, s = k.el.style, w = k.w || (k.w = k.el.offsetWidth), hh = k.n < 12 && !narrow ? 34 : 18, rr = k.r * p[2];
      var lx = side > 0 ? p[0] + rr + 9 : p[0] - rr - 9 - w; if (narrow) lx = Math.max(6, Math.min(W - w - 6, lx));
      var box2 = [lx - 6, p[1] - hh / 2 - 3, lx + w + 6, p[1] + hh / 2 + 3], free = taken.every(function (q) { return box2[2] < q[0] || box2[0] > q[2] || box2[3] < q[1] || box2[1] > q[3]; });
      var want = pick === k ? 1 : !free || (narrow && k.n > 6) ? 0 : pick ? 0.3 : 1; if (want > 0 || pick === k) taken.push(box2);
      s.left = lx + "px"; s.top = p[1] + "px"; s.textAlign = side > 0 ? "left" : "right"; s.opacity = document.activeElement === k.el ? 1 : want; s.pointerEvents = want > 0.5 ? "auto" : "none";
    });
    if (pick && pick.n == null) { var q = pick.p, ts = tip.style; tip.href = "#" + pick.id; tip.firstChild.textContent = pick.name; tip.lastChild.innerHTML = pick.capText + " · " + pick.day; ts.left = (q[0] + 12) + "px"; ts.top = q[1] + "px"; ts.opacity = 1; } else tip.style.opacity = 0;
  }
  function frame(now) {
    var dt = last ? Math.min(0.05, (now - last) / 1000) : 0; last = now; t += dt;
    if (!pick) { planets.forEach(function (k) { k.u += k.sp * dt; }); belt.forEach(function (k) { k.u += k.sp * dt; }); }
    draw(); run = !still && seen && !document.hidden ? requestAnimationFrame(frame) : 0;
  }
  function wake() { if (!run && !still && seen && !document.hidden) { last = 0; run = requestAnimationFrame(frame); } }
  // a body itself can be pointed at and pressed, as its name can
  function near(e) { var b = box.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top, hit = null, best = 1e9;
    planets.forEach(function (k) { var d = Math.hypot(k.p[0] - x, k.p[1] - y); if (d < Math.max(12, k.r * k.p[2] + 6) && d < best) { best = d; hit = k; } });
    if (!hit) belt.forEach(function (k) { var d = Math.hypot(k.p[0] - x, k.p[1] - y); if (d < 9 && d < best) { best = d; hit = k; } });
    return hit; }
  front.addEventListener("pointermove", function (e) { pick = near(e); front.style.cursor = pick ? "pointer" : ""; if (still) draw(); });
  front.addEventListener("pointerleave", function () { pick = null; if (still) draw(); });
  front.addEventListener("click", function (e) { var k = near(e); if (k) location.hash = k.id; });
  if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { seen = en[0].isIntersecting; wake(); }).observe(box);
  document.addEventListener("visibilitychange", wake);
  if ("ResizeObserver" in window) new ResizeObserver(size).observe(box); else window.addEventListener("resize", size);
  size(); wake();
})();
