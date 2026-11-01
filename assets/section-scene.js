// Andra Markets section pages: the backdrop (owner-approved, 31 Oct 2026).
//
// Every page but the homepage sits inside a black sphere: particles float slowly round
// you, most on the sphere's wall and some inside it, near ones large and soft, far ones
// small and sharp. At the far end, in the middle of the screen, stands the horse: black,
// lit from behind and a little to the right, so only its outline catches the light. The
// pointer turns you a little inside the sphere and scrolling carries you towards the
// horse while the scene dims behind the page.
//
// The horse comes from assets/section-horse.png (tools/make_section_horse.py, from
// andra-horse.png). The light theme shows the same scene inverted in CSS. Reduced motion:
// one still frame. Without WebGL the page keeps its plain ground.
//
// Moving between pages (owner-approved, 1 Nov 2026): arriving from the homepage, whose hero
// went back into the point at the centre of the screen (assets/hero-horse.js), the sphere
// opens out of that point (the page's head marks html.arrive). From one section to the next
// the sphere carries on: its clock, its light and its turn are kept for the next page, so it
// neither restarts nor goes dark while the page cross-fades.
(function () {
  "use strict";
  var canvas = document.querySelector(".scene__canvas");
  if (!canvas || !window.WebGLRenderingContext) return;
  var gl = null;
  // No antialiasing (owner-approved, 1 Nov 2026, for a smoother site): the particles are soft
  // dots and the horse's edge is smoothed in its own shader, so it only cost a four-times
  // buffer to clear and resolve on every frame, heaviest on laptops with integrated graphics.
  try { gl = canvas.getContext("webgl", { antialias: false, alpha: false }); } catch (e) { gl = null; }
  if (!gl) return;

  var mq = window.matchMedia("(prefers-reduced-motion: reduce)");
  var reduce = mq.matches;
  var BOX = { w: 510, h: 560 };     // the horse texture's source box, in andra-horse.png pixels

  // The particles. The camera sits near the middle of a sphere of radius 1, looking at the
  // far pole; each particle drifts slowly round the line of view and floats a little.
  var VS_P = [
    "attribute vec4 a;",
    "uniform float t, focal, dpr, side, zSplit, power, op; uniform mediump float ink; uniform vec2 res, center, turn; uniform vec3 cam;",
    "varying float va; varying float vsoft;",
    "vec3 rotY(vec3 p, float a){ float c = cos(a), s = sin(a); return vec3(c*p.x + s*p.z, p.y, -s*p.x + c*p.z); }",
    "vec3 rotX(vec3 p, float a){ float c = cos(a), s = sin(a); return vec3(p.x, c*p.y - s*p.z, s*p.y + c*p.z); }",
    "void main(){",
    "  float r = a.w;",
    "  float w = t * (0.003 + 0.004 * r);",
    "  vec3 p = vec3(a.x * cos(w) - a.y * sin(w), a.x * sin(w) + a.y * cos(w), a.z);",
    "  p += 0.03 * vec3(sin(t * 0.06 + r * 40.0), cos(t * 0.05 + r * 23.0), sin(t * 0.04 + r * 61.0));",
    "  vec3 q = rotX(rotY(p, turn.x), turn.y) - cam;",
    // drawn in two passes: beyond the horse, then in front of it
    "  float behind = step(zSplit, q.z);",
    "  if (q.z < 0.06 || abs(behind - side) > 0.5) { gl_Position = vec4(2.0, 2.0, 0.0, 1.0); gl_PointSize = 0.0; va = 0.0; vsoft = 0.0; return; }",
    "  vec2 s = center + vec2(q.x, -q.y) / q.z * focal;",
    // arriving from the homepage: out of the point at the centre, quick out of it and slowing
    // into place
    "  float oe = clamp(op * 1.6 - 0.6 * fract(r * 5.31), 0.0, 1.0);",
    "  oe = 1.0 - (1.0 - oe) * (1.0 - oe) * (1.0 - oe);",
    "  s = center + (s - center) * oe;",
    "  gl_Position = vec4(s.x / res.x * 2.0 - 1.0, 1.0 - s.y / res.y * 2.0, 0.0, 1.0);",
    // a little brighter near the light behind the horse
    "  vec3 L = vec3(0.0, 0.02, 1.0) - cam;",
    "  float d = length(q - L);",
    "  float lit = 0.22 + 0.5 * exp(-d * d * 3.2);",
    // near ones big and soft (out of focus), far ones small and sharp
    "  float near = 1.0 - smoothstep(0.15, 0.7, q.z);",
    "  float size = (1.1 + 1.6 * fract(r * 7.13)) * (0.9 / q.z) * (1.0 + near * 5.0);",
    "  gl_PointSize = clamp(size * dpr * mix(0.35, 1.0, oe), 1.0, mix(4.0, 26.0, oe) * dpr);",
    "  vsoft = near;",
    // (brighter while they fly out, so the opening reads against the black)
    "  va = lit * (0.35 + 0.65 * fract(r * 3.71)) / (1.0 + near * 7.0) * power * (1.0 + 2.5 * (1.0 - oe) * step(op, 0.999));",
    "}"
  ].join("\n");
  // The light theme inverts the canvas in CSS; there the particles print in full black
  // (owner, 31 Oct 2026): the dark theme's scene as it is, sizes, blur and motion, reversed:
  // drawn white and two and a half times as strong, so what glows on black prints in black.
  var FS_P = [
    "precision mediump float; varying float va; varying float vsoft; uniform float ink;",
    "void main(){ vec2 d = gl_PointCoord - 0.5; float k = exp(-dot(d, d) * mix(18.0, 5.0, vsoft));",
    "  float v = mix(va, min(1.0, va * 2.5), ink);",
    "  gl_FragColor = vec4(mix(vec3(0.86, 0.9, 0.96), vec3(1.0), ink) * v * k, 0.0); }"
  ].join("\n");

  // The horse: black, so it hides what floats behind it. The light is behind it, a little to
  // the right and above: a 1.2px edge of light where the outline faces it, a 4px spill just
  // outside, a faint glow behind the neck, and the engraving's shading barely there.
  // The texture is read the same way for every pixel, with no branch round the read: a
  // phone's GPU picks the wrong mipmap along the edge of such a branch and drew the
  // texture's square round the horse.
  // Only the pixels round the horse are drawn, not the whole screen: the horse's own box
  // (uv 0 to 1) and the glow out to where it falls under a tenth of a level (0.79 of the
  // box's height from the glow's centre). Every pixel left out would have come out the same,
  // and the shader runs on about a twentieth of the screen instead of all of it.
  var VS_H = [
    "attribute vec2 p; uniform vec2 res; uniform vec4 box;",
    "void main(){",
    "  vec2 s = box.xy + mix(vec2(-0.3, -0.45), vec2(1.55, 1.25), p) * box.zw;",
    "  gl_Position = vec4(s.x / res.x * 2.0 - 1.0, 1.0 - s.y / res.y * 2.0, 0.0, 1.0);",
    "}"
  ].join("\n");
  var FS_H = [
    "precision highp float;",
    "uniform sampler2D horse; uniform vec2 res; uniform vec4 box; uniform float dpr, power, srcpx;",
    "vec4 at(vec2 uv){",
    "  vec4 h = texture2D(horse, clamp(uv, 0.0, 1.0));",
    "  vec2 inb = step(vec2(0.0), uv) * step(uv, vec2(1.0));",
    "  return mix(vec4(1.0, 0.0, 0.0, 1.0), h, inb.x * inb.y);",
    "}",
    "void main(){",
    "  vec2 p = vec2(gl_FragCoord.x, res.y * dpr - gl_FragCoord.y) / dpr;",
    "  vec2 uv = (p - box.xy) / box.zw;",
    "  vec2 L = normalize(vec2(0.78, -0.62));",
    "  vec2 dh = (uv - vec2(0.62, 0.40)) * vec2(box.z / box.w, 1.0);",
    "  float glow = exp(-dot(dh, dh) / 0.12) * 0.075;",
    "  vec4 h = at(uv);",
    "  vec2 e = vec2(3.0 / 1020.0, 3.0 / 1120.0);",
    "  vec2 g = vec2(at(uv + vec2(e.x, 0.0)).g - at(uv - vec2(e.x, 0.0)).g, at(uv + vec2(0.0, e.y)).g - at(uv - vec2(0.0, e.y)).g);",
    "  vec2 outward = length(g) > 0.002 ? -normalize(g) : vec2(0.0);",
    "  float facing = pow(clamp((dot(outward, L) + 0.15) / 0.9, 0.0, 1.0), 1.5);",
    "  float rim = exp(-h.r * 9.0 * srcpx / 1.2) * h.g * facing;",
    "  float spill = exp(-h.a * 14.0 * srcpx / 4.0) * (1.0 - h.g) * facing * (1.0 - smoothstep(0.6, 1.0, h.a));",
    "  vec3 light = vec3(0.92, 0.94, 0.97);",
    "  vec3 col = light * (rim + spill * 0.16) + light * h.b * h.g * 0.045 + light * glow * (1.0 - h.g);",
    // premultiplied: the body covers what is behind it, the light adds
    "  gl_FragColor = vec4(col * power, h.g);",
    "}"
  ].join("\n");

  function shader(type, src) { var o = gl.createShader(type); gl.shaderSource(o, src); gl.compileShader(o); return o; }
  function program(vs, fs) {
    var p = gl.createProgram();
    gl.attachShader(p, shader(gl.VERTEX_SHADER, vs));
    gl.attachShader(p, shader(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(p);
    return gl.getProgramParameter(p, gl.LINK_STATUS) ? p : null;
  }
  function uniforms(p, names) { var u = {}; names.forEach(function (n) { u[n] = gl.getUniformLocation(p, n); }); return u; }
  var PP = program(VS_P, FS_P), PH = program(VS_H, FS_H);
  if (!PP || !PH) return;
  var UP = uniforms(PP, ["t", "focal", "dpr", "side", "zSplit", "power", "op", "res", "center", "turn", "cam", "ink"]);
  var UH = uniforms(PH, ["horse", "res", "box", "dpr", "power", "srcpx"]);
  var aP = gl.getAttribLocation(PP, "a"), aQ = gl.getAttribLocation(PH, "p");

  // particles, placed once: 72% on the wall, the rest inside
  var N = Math.min(window.innerWidth, window.innerHeight * 1.6) > 960 ? 9000 : 4500;
  var seed = 1412;
  function rnd() {
    seed |= 0; seed = seed + 0x6D2B79F5 | 0;
    var q = Math.imul(seed ^ seed >>> 15, 1 | seed);
    q = q + Math.imul(q ^ q >>> 7, 61 | q) ^ q;
    return ((q ^ q >>> 14) >>> 0) / 4294967296;
  }
  var pts = new Float32Array(N * 4);
  for (var i = 0; i < N; i++) {
    var u = rnd() * 2 - 1, th = rnd() * Math.PI * 2, sq = Math.sqrt(1 - u * u);
    var rad = rnd() < 0.72 ? 0.96 + rnd() * 0.08 : Math.cbrt(rnd()) * 0.94;
    pts[i * 4] = sq * Math.cos(th) * rad; pts[i * 4 + 1] = sq * Math.sin(th) * rad; pts[i * 4 + 2] = u * rad; pts[i * 4 + 3] = rnd();
  }
  var pBuf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, pBuf); gl.bufferData(gl.ARRAY_BUFFER, pts, gl.STATIC_DRAW);
  var qBuf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, qBuf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([0, 0, 1, 0, 0, 1, 1, 1]), gl.STATIC_DRAW);
  var tex = gl.createTexture();

  var W = 0, H = 0, DPR = 1, ready = false, running = false, t0 = 0, on = 0;
  var ptr = { x: 0, y: 0, sx: 0, sy: 0 };
  // texReady: the horse's texture is in; hz: the horse's own light, so a texture that comes
  // in after the first frame fades in rather than appearing at once
  var texReady = false, hz = 0, drawn = false;
  // opening: arriving from the homepage, the sphere opens out of the point over OPEN seconds
  var root = document.documentElement;
  // (its clock moves at most 1/20s a frame, so a frame held up while the page loads pauses
  // the opening rather than skipping it)
  var opening = !reduce && root.classList.contains("arrive"), OPEN = 1.3, openT = 0, openLast = 0;
  var CAM_Z = -0.25, ASP = BOX.w / BOX.h;

  // the page's scroll and the window's height, kept as they change rather than asked for on
  // every frame (asking can make the browser work out the page's layout again mid-frame)
  var sy = 0, vh = 1;
  function resize() {
    W = Math.max(1, canvas.clientWidth); H = Math.max(1, canvas.clientHeight);
    sy = window.scrollY || 0; vh = window.innerHeight || 1;
    DPR = Math.min(window.devicePixelRatio || 1, 1.5);
    canvas.width = Math.round(W * DPR); canvas.height = Math.round(H * DPR);
  }

  function frame(now) {
    var t = reduce ? 30 : (now - t0) / 1000;
    var o = 1;
    if (opening) {
      openT += openLast ? Math.max(0, Math.min(now - openLast, 50)) : 0;
      openLast = now;
      o = Math.min(1, openT / 1000 / OPEN);
      if (o >= 1) opening = false;
    }
    if (texReady && hz < 1) hz = Math.min(1, hz + 0.06);
    drawn = true;
    on = reduce ? 1 : Math.min(1, on + 0.008);               // the light comes up over about two seconds
    ptr.sx += (ptr.x - ptr.sx) * 0.025; ptr.sy += (ptr.y - ptr.sy) * 0.025;
    var sc = Math.min(1, sy / (vh * 0.8));
    var power = 1 - Math.pow(1 - on, 3);
    var fade = 0.32 + 0.68 * (1 - sc);                        // dimmer behind the page as it scrolls
    var turn = [ptr.sx * 0.12 + (reduce ? 0 : Math.sin(t * 0.03) * 0.02), -ptr.sy * 0.08];
    var cam = [0, 0, CAM_Z + 0.18 * sc];
    var focal = Math.min(W, H) * 0.85;
    // where the far pole, the horse, lands once turned
    var pz0 = Math.cos(turn[0]), px = Math.sin(turn[0]);
    var py = -pz0 * Math.sin(turn[1]), pz = pz0 * Math.cos(turn[1]);
    var dz = pz - cam[2];
    var cx = W / 2, cy = H / 2;
    var hx = cx + px / dz * focal, hy = cy - py / dz * focal;
    // opening: the horse grows out of the point a little after the particles
    var ho = 1 - Math.pow(1 - Math.min(1, Math.max(0, (o - 0.2) / 0.8)), 3);
    var hh = (W > 960 ? H * 0.185 : H * 0.165) * (1 + 0.2 * sc) * ho;
    var box = [hx - hh * ASP / 2, hy - hh / 2, hh * ASP, hh];

    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.clearColor(0, 0, 0, 1); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.enable(gl.BLEND);
    function particles(side) {
      gl.useProgram(PP); gl.blendFunc(gl.ONE, gl.ONE);
      gl.disableVertexAttribArray(aQ);
      gl.bindBuffer(gl.ARRAY_BUFFER, pBuf); gl.enableVertexAttribArray(aP); gl.vertexAttribPointer(aP, 4, gl.FLOAT, false, 0, 0);
      gl.uniform1f(UP.t, t); gl.uniform1f(UP.focal, focal); gl.uniform1f(UP.dpr, DPR); gl.uniform1f(UP.side, side);
      gl.uniform1f(UP.zSplit, dz - 0.02); gl.uniform1f(UP.power, (0.35 + 0.65 * power) * fade); gl.uniform1f(UP.op, o);
      gl.uniform2f(UP.res, W, H); gl.uniform2f(UP.center, cx, cy); gl.uniform2f(UP.turn, turn[0], turn[1]);
      gl.uniform3f(UP.cam, cam[0], cam[1], cam[2]);
      gl.uniform1f(UP.ink, document.documentElement.getAttribute("data-theme") === "dark" ? 0 : 1);
      gl.drawArrays(gl.POINTS, 0, N);
    }
    particles(1);
    if (texReady && hh > 1) {
      gl.useProgram(PH); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
      gl.disableVertexAttribArray(aP);
      gl.bindBuffer(gl.ARRAY_BUFFER, qBuf); gl.enableVertexAttribArray(aQ); gl.vertexAttribPointer(aQ, 2, gl.FLOAT, false, 0, 0);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex); gl.uniform1i(UH.horse, 0);
      gl.uniform2f(UH.res, W, H); gl.uniform4f(UH.box, box[0], box[1], box[2], box[3]); gl.uniform1f(UH.dpr, DPR);
      gl.uniform1f(UH.power, power * fade * hz * ho); gl.uniform1f(UH.srcpx, box[2] / BOX.w);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    }
    particles(0);
  }

  function loop(now) { if (!running) return; requestAnimationFrame(loop); frame(now); }
  function start() { if (ready && !running && !reduce && !document.hidden) { running = true; requestAnimationFrame(loop); } }
  function stop() { running = false; }
  function still() { if (ready) frame(performance.now()); }

  // from the page before, if it was a section a moment ago: the sphere carries on from there
  var kept = null, age = -1;
  if (!reduce && !opening) {
    try { kept = JSON.parse(sessionStorage.getItem("andra-scene") || "null"); } catch (e) { kept = null; }
    age = kept ? Date.now() - kept.at : -1;
    if (!(age >= 0 && age < 8000 && isFinite(kept.t))) kept = null;
  }
  window.addEventListener("pagehide", function () {
    if (reduce || !ready) return;
    try {
      sessionStorage.setItem("andra-scene", JSON.stringify({ t: (performance.now() - t0) / 1000, on: on,
        x: ptr.x, y: ptr.y, sx: ptr.sx, sy: ptr.sy, at: Date.now() }));
    } catch (e) { /* private mode */ }
  });

  // the particles draw at once; the horse joins them when its texture is in
  var img = new Image();
  img.decoding = "async";
  function texture() {
    if (texReady || !img.naturalWidth) return;
    gl.bindTexture(gl.TEXTURE_2D, tex);
    // the texture holds measurements, not colours: read as stored
    gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    gl.generateMipmap(gl.TEXTURE_2D);   // power of two: the outline stays smooth at any size
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    texReady = true;
    if (!drawn || reduce || kept) hz = 1;
    if (!running) still();
  }
  img.onload = texture;
  img.src = canvas.getAttribute("data-src");
  if (img.complete) texture();     // already in memory from the page before

  ready = true;
  resize();
  t0 = performance.now() - (kept ? kept.t * 1000 + age : 0);
  if (opening) on = 0.4;           // the light is partly up already as the sphere opens
  if (kept) {
    on = Math.min(1, Math.max(0, +kept.on || 0));
    ptr.x = +kept.x || 0; ptr.y = +kept.y || 0; ptr.sx = +kept.sx || 0; ptr.sy = +kept.sy || 0;
  }
  if (opening || kept) canvas.parentNode.classList.add("is-now");
  canvas.parentNode.classList.add("is-live");
  if (reduce) still(); else start();

  if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
    window.addEventListener("pointermove", function (e) {
      ptr.x = e.clientX / window.innerWidth - 0.5; ptr.y = e.clientY / window.innerHeight - 0.5;
    }, { passive: true });
  }
  document.addEventListener("visibilitychange", function () { if (document.hidden) stop(); else start(); });
  var rt;
  window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(function () { resize(); if (!running) still(); }, 120); });
  window.addEventListener("scroll", function () { sy = window.scrollY || 0; if (!running) still(); }, { passive: true });
  // a theme change redraws a still scene (reduced motion) in the new ink
  if (window.MutationObserver) new MutationObserver(function () { if (!running) still(); })
    .observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  var onMotion = function (e) { reduce = e.matches; if (reduce) { stop(); still(); } else start(); };
  if (mq.addEventListener) mq.addEventListener("change", onMotion);
})();
