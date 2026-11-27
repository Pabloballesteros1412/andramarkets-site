/* Crypto: the Bitcoin system (owner, 27 Nov 2026: the Bitcoin sun; then more coins in the rings; then "it still
   looks artificial"). A solar system in true 3D (WebGL, a perspective camera a little above the plane), made with
   real imagery: the surfaces of the Sun and of the planets are photographic maps from NASA missions (Solar System
   Scope, CC BY 4.0, credited on the page), in assets/crypto/. Bitcoin is the Sun: its surface turns slowly, darker
   at the limb, inside a corona of streamers. The twenty-four largest coins after it are planets, the larger the
   nearer; each is given one of the planets' surfaces (a grey moon or Mercury when the coin is pegged to a
   currency) and is lit by the Sun exactly: a full disc beyond it, a crescent between it and us, a black
   silhouette when it crosses its face. The first coin given Saturn's surface carries its rings. The rest of the
   hundred are the belt beyond, a grain each. Every body is a row of the table: its size is its market value, and
   a press goes to its row. The surfaces and the turning are not data, and the page says so. Pointing at a body
   stops the orbits and lights its own. A phone sees the system from higher up. Without WebGL the page is the
   table. */
(function () {
  "use strict";
  var box = document.querySelector(".cs"), trs = [].slice.call(document.querySelectorAll(".cs-tab tbody tr")); if (!box || trs.length < 12) return;
  var cv = box.querySelector("canvas"), layer = box.querySelector(".cs__names"), gl = null;
  try { gl = cv.getContext("webgl", { antialias: true, alpha: true, premultipliedAlpha: true }); } catch (e) { gl = null; }
  if (!gl) return;
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches, TAU = Math.PI * 2, FOV = 30 * Math.PI / 180;
  var BASE = (document.body.getAttribute("data-base") || "../") + "assets/crypto/";
  function hash(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function rng(s) { return function () { s = (s + 0x6D2B79F5) >>> 0; var t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  var rnd = rng(29);
  function read(tr) { return { id: tr.id, name: tr.querySelector(".cs-name").textContent, cap: +tr.getAttribute("data-cap"), capText: tr.querySelector(".cs-cap").textContent,
    price: tr.querySelector(".cs-price").textContent, day: tr.querySelector(".cs-day").innerHTML, stable: tr.hasAttribute("data-stable") }; }
  var all = trs.map(read), sun = all[0], NP = Math.min(+box.getAttribute("data-planets") || 24, all.length - 1), planets = all.slice(1, NP + 1), belt = all.slice(NP + 1), top = planets[0].cap;

  // ---- the bodies ------------------------------------------------------------------------------------------
  var GAS = ["jupiter", "saturn", "neptune", "mars", "uranus", "venus", "makemake", "eris", "haumea"], ROCK = ["moon", "mercury", "ceres"], gi = 0, ri = 0, ringed = false;
  planets.forEach(function (k, n) {
    var r = rng(hash(k.id));
    k.n = n; k.tex = k.stable ? ROCK[ri++ % ROCK.length] : GAS[gi++ % GAS.length];
    k.ring = !ringed && k.tex === "saturn"; if (k.ring) ringed = true;
    k.R = 0; k.u = n < 8 ? -Math.PI / 2 + (n % 2 ? 1 : -1) * (0.55 + 0.32 * Math.floor(n / 2)) + (r() - 0.5) * 0.2 : rnd() * TAU; k.spin = r() * TAU; k.spinSp = 0.12 + r() * 0.3; k.tilt = (r() - 0.5) * 0.5; k.uoff = r();
    var cycle = Math.floor((k.stable ? ri : gi) / (k.stable ? ROCK.length : GAS.length) - 0.001);   // a surface given twice is turned and tinted a little
    k.tint = cycle > 0 ? [0.92 + r() * 0.16, 0.9 + r() * 0.14, 0.86 + r() * 0.16] : [1, 1, 1];
    k.air = k.stable ? 0 : (k.tex === "venus" || k.tex === "neptune" || k.tex === "uranus" || k.tex === "jupiter" || k.tex === "saturn") ? 0.55 : 0.18;
    k.r = 0.12 + 0.62 * Math.pow(k.cap / top, 0.45);
    var a = document.createElement("a"); a.className = "cs__name" + (k.stable ? " is-pegged" : "") + (n >= 12 ? " is-small" : ""); a.href = "#" + k.id;
    a.innerHTML = "<b></b><span class=\"lens-read\"></span>"; a.firstChild.textContent = k.name; a.lastChild.innerHTML = k.capText + " · " + k.day; layer.appendChild(a); k.el = a;
    a.addEventListener("pointerenter", function () { pick = k; wake(); }); a.addEventListener("pointerleave", function () { if (pick === k) pick = null; wake(); });
    a.addEventListener("focus", function () { pick = k; wake(); }); a.addEventListener("blur", function () { if (pick === k) pick = null; wake(); });
  });
  var SR = 1.5, R0 = 3.6, R1 = 14.5, BR0 = 16, BR1 = 19;
  planets.forEach(function (k, n) { k.R = R0 + (R1 - R0) * Math.pow(n / (planets.length - 1), 0.92); });
  function omega(R) { return 0.07 * Math.pow(R0 / R, 1.5); }
  belt.forEach(function (k) { k.R = BR0 + rnd() * (BR1 - BR0); k.a0 = rnd() * TAU; k.y = (rnd() - 0.5) * 0.7; });
  var mid = document.createElement("a"); mid.className = "cs__sun"; mid.href = "#" + sun.id; mid.innerHTML = "<b></b><span class=\"lens-read\"></span>";
  mid.firstChild.textContent = sun.name; mid.lastChild.innerHTML = sun.price + " · " + sun.day; layer.appendChild(mid);
  var tip = document.createElement("a"); tip.className = "cs__name cs__tip"; tip.innerHTML = "<b></b><span class=\"lens-read\"></span>"; tip.style.opacity = 0; layer.appendChild(tip);

  // ---- WebGL -----------------------------------------------------------------------------------------------
  function sh(type, src) { var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; }
  function program(vs, fs) { var p = gl.createProgram(); gl.attachShader(p, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(p, sh(gl.FRAGMENT_SHADER, fs)); gl.linkProgram(p);
    var u = {}, n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS), i; for (i = 0; i < n; i++) { var nm = gl.getActiveUniform(p, i).name; u[nm] = gl.getUniformLocation(p, nm); }
    var a = {}; n = gl.getProgramParameter(p, gl.ACTIVE_ATTRIBUTES); for (i = 0; i < n; i++) { var an = gl.getActiveAttrib(p, i).name; a[an] = gl.getAttribLocation(p, an); }
    return { p: p, u: u, a: a }; }
  var NOISE = "float h(vec3 p){p=fract(p*.3183099+.1);p*=17.;return fract(p.x*p.y*p.z*(p.x+p.y+p.z));}" +
    "float n3(vec3 x){vec3 i=floor(x),f=fract(x);f=f*f*(3.-2.*f);return mix(mix(mix(h(i),h(i+vec3(1,0,0)),f.x),mix(h(i+vec3(0,1,0)),h(i+vec3(1,1,0)),f.x),f.y),mix(mix(h(i+vec3(0,0,1)),h(i+vec3(1,0,1)),f.x),mix(h(i+vec3(0,1,1)),h(i+vec3(1,1,1)),f.x),f.y),f.z);}" +
    "float fbm(vec3 p){float a=.5,s=0.;for(int i=0;i<4;i++){s+=a*n3(p);p=p*2.03+7.1;a*=.5;}return s;}";
  var P, S, Rg, L, B, C;
  try {
    var SPH_V = "attribute vec3 p;attribute vec2 uv;uniform mat4 M,VP;varying vec3 wp,wn;varying vec2 vuv;void main(){vec4 w=M*vec4(p,1.);wp=w.xyz;wn=mat3(M)*p;vuv=uv;gl_Position=VP*w;}";
    P = program(SPH_V, "precision highp float;uniform sampler2D tex;uniform vec3 eye,tint;uniform float air,dim,uoff;varying vec3 wp,wn;varying vec2 vuv;" +
      "void main(){vec3 n=normalize(wn),l=normalize(-wp),v=normalize(eye-wp);vec3 c=texture2D(tex,vec2(vuv.x+uoff,vuv.y)).rgb*tint;c=pow(c,vec3(1.15));" +
      "float d=dot(n,l);float lit=smoothstep(-.06,.5,d)*.85+max(d,0.)*.35;vec3 col=c*(.045+lit*1.3)*vec3(1.,.95,.86);" +
      "float fr=pow(1.-max(dot(n,v),0.),2.6);col+=air*fr*smoothstep(-.25,.45,d)*vec3(1.,.74,.44)*.9;" +
      "gl_FragColor=vec4(col*dim,1.);}");
    S = program(SPH_V, "precision highp float;uniform sampler2D tex;uniform vec3 eye;uniform float t;varying vec3 wp,wn;varying vec2 vuv;" + NOISE +
      "void main(){vec3 n=normalize(wn),v=normalize(eye-wp);float mu=max(dot(n,v),0.);vec3 c=texture2D(tex,vec2(vuv.x+t*.003,vuv.y)).rgb;" +
      "float g=dot(c,vec3(.45,.4,.15));g+=(fbm(n*9.+vec3(0.,t*.05,0.))-.5)*.22;g=clamp(g*1.25,0.,1.);" +
      "vec3 col=mix(vec3(.92,.32,.04),vec3(1.,.74,.32),smoothstep(.15,.7,g));col=mix(col,vec3(1.,.97,.86),smoothstep(.62,1.,g));" +
      "col*=.4+.75*pow(mu,.45);col+=vec3(1.,.55,.18)*pow(1.-mu,3.)*.35;gl_FragColor=vec4(col,1.);}");
    Rg = program("attribute vec3 p;attribute vec2 uv;uniform mat4 M,VP;varying vec3 wp,rn;varying vec2 vuv;void main(){vec4 w=M*vec4(p,1.);wp=w.xyz;rn=mat3(M)*vec3(0.,1.,0.);vuv=uv;gl_Position=VP*w;}",
      "precision highp float;uniform sampler2D tex;uniform float dim;varying vec3 wp,rn;varying vec2 vuv;void main(){vec4 c=texture2D(tex,vec2(vuv.x,.5));vec3 l=normalize(-wp);float lit=.25+.75*abs(dot(normalize(rn),l));" +
      "float a=c.a*.9*dim;gl_FragColor=vec4(c.rgb*lit*a*1.1,a);}");
    L = program("attribute vec3 p;uniform mat4 VP;uniform float R;void main(){gl_Position=VP*vec4(p*R,1.);}", "precision mediump float;uniform vec4 col;void main(){gl_FragColor=vec4(col.rgb*col.a,col.a);}");
    B = program("attribute vec4 b;uniform mat4 VP;uniform float t,ps;varying float vb;void main(){float w=.07*pow(" + R0.toFixed(2) + "/b.x,1.5);float a=b.y+w*t;vec4 c=VP*vec4(b.x*cos(a),b.z,b.x*sin(a),1.);gl_Position=c;" +
      "gl_PointSize=max(2.,ps*.14/c.w);vb=b.w;}", "precision mediump float;varying float vb;void main(){float d=length(gl_PointCoord-.5);float a=smoothstep(.5,.2,d)*vb;gl_FragColor=vec4(vec3(.86,.8,.72)*a,a);}");
    C = program("attribute vec2 q;uniform mat4 VP;uniform vec3 rt,up;uniform float sz;varying vec2 vq;void main(){vq=q*7.;gl_Position=VP*vec4((rt*q.x+up*q.y)*sz,1.);}",
      "precision highp float;uniform float t;varying vec2 vq;" + NOISE +
      "void main(){float r=length(vq);float d=max(r-1.,0.);float an=atan(vq.y,vq.x);float st=fbm(vec3(an*2.6,r*.7-t*.09,t*.04))*.7+fbm(vec3(an*8.,r*1.6-t*.14,3.))*.3;" +
      "float g=exp(-d*2.4)*(.38+st*.75)+exp(-d*.55)*(.07+.09*st)+exp(-d*10.)*.8;" +
      "vec3 c=mix(vec3(1.,.5,.12),vec3(1.,.88,.62),exp(-d*4.));float fade=smoothstep(7.,4.,r);gl_FragColor=vec4(c*g*fade,0.);}");
  } catch (e) { return; }

  function buf(data, idx) { var b = gl.createBuffer(); gl.bindBuffer(idx ? gl.ELEMENT_ARRAY_BUFFER : gl.ARRAY_BUFFER, b); gl.bufferData(idx ? gl.ELEMENT_ARRAY_BUFFER : gl.ARRAY_BUFFER, data, gl.STATIC_DRAW); return b; }
  // a sphere of latitude and longitude, its texture from the north pole down
  var LA = 48, LO = 96, sv = [], si = [], i, j;
  for (i = 0; i <= LA; i++) for (j = 0; j <= LO; j++) { var th = i / LA * Math.PI, ph = j / LO * TAU; sv.push(Math.sin(th) * Math.cos(ph), Math.cos(th), -Math.sin(th) * Math.sin(ph), j / LO, i / LA); }
  for (i = 0; i < LA; i++) for (j = 0; j < LO; j++) { var a0 = i * (LO + 1) + j, b0 = a0 + LO + 1; si.push(a0, b0, a0 + 1, a0 + 1, b0, b0 + 1); }
  var SPV = buf(new Float32Array(sv)), SPI = buf(new Uint16Array(si), true), SPN = si.length;
  var rv = []; for (i = 0; i <= 128; i++) { var ra = i / 128 * TAU; rv.push(Math.cos(ra) * 1.24, 0, Math.sin(ra) * 1.24, 0, 0.5, Math.cos(ra) * 2.27, 0, Math.sin(ra) * 2.27, 1, 0.5); }
  var RGV = buf(new Float32Array(rv));
  var cvv = []; for (i = 0; i < 192; i++) { var ca = i / 192 * TAU; cvv.push(Math.cos(ca), 0, Math.sin(ca)); } var CIR = buf(new Float32Array(cvv));
  var bv = []; belt.forEach(function (k) { bv.push(k.R, k.a0, k.y, 0.45 + rnd() * 0.5); }); var BLT = buf(new Float32Array(bv));
  var QUAD = buf(new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]));

  var TEX = {}, waiting = 0;
  function texture(name, png) {
    if (TEX[name]) return TEX[name]; var t = { t: gl.createTexture(), ok: false }; TEX[name] = t; waiting++;
    var img = new Image(); img.onload = function () {
      gl.bindTexture(gl.TEXTURE_2D, t.t); gl.texImage2D(gl.TEXTURE_2D, 0, png ? gl.RGBA : gl.RGB, png ? gl.RGBA : gl.RGB, gl.UNSIGNED_BYTE, img);
      gl.generateMipmap(gl.TEXTURE_2D); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      t.ok = true; if (--waiting === 0) { box.classList.add("is-ready"); wake(); } };
    img.onerror = function () { if (--waiting === 0) { box.classList.add("is-ready"); wake(); } };
    img.src = BASE + name + (png ? ".png" : ".jpg"); return t;
  }
  texture("sun"); planets.forEach(function (k) { texture(k.tex); }); if (ringed) texture("ring", true);

  // ---- the camera and the matrices (column-major) ----------------------------------------------------------------
  function mul(a, b) { var o = new Array(16), r, c, k, s; for (c = 0; c < 4; c++) for (r = 0; r < 4; r++) { s = 0; for (k = 0; k < 4; k++) s += a[k * 4 + r] * b[c * 4 + k]; o[c * 4 + r] = s; } return o; }
  function persp(f, asp, n, fa) { var t = 1 / Math.tan(f / 2); return [t / asp, 0, 0, 0, 0, t, 0, 0, 0, 0, (fa + n) / (n - fa), -1, 0, 0, 2 * fa * n / (n - fa), 0]; }
  function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
  function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
  function norm(a) { var l = Math.hypot(a[0], a[1], a[2]); return [a[0] / l, a[1] / l, a[2] / l]; }
  function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
  function look(e, c) { var z = norm(sub(e, c)), x = norm(cross([0, 1, 0], z)), y = cross(z, x); return { m: [x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0, -dot(x, e), -dot(y, e), -dot(z, e), 1], x: x, y: y }; }
  function model(pos, tilt, spin, r) { var c = Math.cos(spin), s = Math.sin(spin), ct = Math.cos(tilt), st = Math.sin(tilt);
    return [ct * c * r, st * c * r, -s * r, 0, -st * r, ct * r, 0, 0, ct * s * r, st * s * r, c * r, 0, pos[0], pos[1], pos[2], 1]; }
  var W = 0, H = 0, D = 1, VP = null, EYE = null, CAMX = null, CAMY = null, PS = 0, narrow = false, pick = null, orb = 0, clock = 0, last = 0, run = 0, seen = true;
  function project(p) { var x = VP[0] * p[0] + VP[4] * p[1] + VP[8] * p[2] + VP[12], y = VP[1] * p[0] + VP[5] * p[1] + VP[9] * p[2] + VP[13], w = VP[3] * p[0] + VP[7] * p[1] + VP[11] * p[2] + VP[15];
    return [(x / w * 0.5 + 0.5) * W, (0.5 - y / w * 0.5) * H, w]; }
  function camera(dist, elev, lift) { EYE = [0, dist * Math.sin(elev), dist * Math.cos(elev)]; var lk = look(EYE, [0, lift, 0]); CAMX = lk.x; CAMY = lk.y;
    VP = mul(persp(FOV, W / H, 0.5, 400), lk.m); PS = (H * D) / (2 * Math.tan(FOV / 2)); }
  function size() {
    D = Math.min(window.devicePixelRatio || 1, 2); W = box.clientWidth; H = box.clientHeight; if (!W) return; narrow = W < 900;
    cv.width = Math.round(W * D); cv.height = Math.round(H * D); gl.viewport(0, 0, cv.width, cv.height);
    var elev = narrow ? 0.95 : 0.5, lift = narrow ? 0 : -1.2, dist;
    // the nearest camera that keeps the belt inside the picture, with room for the names
    for (dist = 24; dist < 200; dist += 0.5) { camera(dist, elev, lift); var ok = true;
      for (i = 0; i < 48 && ok; i++) { var q = project([(R1 + 1) * Math.cos(i / 48 * TAU), 0, (R1 + 1) * Math.sin(i / 48 * TAU)]); if (q[2] <= 0 || q[0] < W * 0.04 || q[0] > W * 0.96 || q[1] < H * 0.05 || q[1] > H * 0.9) ok = false; }
      if (ok) break; }
    planets.forEach(function (k) { k.w = 0; }); wake();
  }

  // ---- drawing -----------------------------------------------------------------------------------------------
  function bindSphere(pr) { gl.bindBuffer(gl.ARRAY_BUFFER, SPV); gl.enableVertexAttribArray(pr.a.p); gl.vertexAttribPointer(pr.a.p, 3, gl.FLOAT, false, 20, 0);
    gl.enableVertexAttribArray(pr.a.uv); gl.vertexAttribPointer(pr.a.uv, 2, gl.FLOAT, false, 20, 12); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, SPI); }
  function off() { for (var a = 0; a < 6; a++) gl.disableVertexAttribArray(a); }
  function draw() {
    if (!W || !VP) return;
    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT); gl.enable(gl.DEPTH_TEST); gl.depthMask(true); gl.disable(gl.BLEND);
    // the Sun
    gl.useProgram(S.p); off(); bindSphere(S); gl.uniformMatrix4fv(S.u.VP, false, VP); gl.uniformMatrix4fv(S.u.M, false, model([0, 0, 0], 0.12, clock * 0.01, SR));
    gl.uniform3fv(S.u.eye, EYE); gl.uniform1f(S.u.t, clock); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, TEX.sun.t); gl.uniform1i(S.u.tex, 0);
    gl.drawElements(gl.TRIANGLES, SPN, gl.UNSIGNED_SHORT, 0);
    // the planets
    gl.useProgram(P.p); off(); bindSphere(P); gl.uniformMatrix4fv(P.u.VP, false, VP); gl.uniform3fv(P.u.eye, EYE); gl.uniform1i(P.u.tex, 0);
    planets.forEach(function (k) {
      var a = k.u + omega(k.R) * orb; k.pos = [k.R * Math.cos(a), 0, k.R * Math.sin(a)];
      gl.uniformMatrix4fv(P.u.M, false, model(k.pos, k.tilt, k.spin + clock * k.spinSp, k.r)); gl.uniform3fv(P.u.tint, k.tint); gl.uniform1f(P.u.air, k.air);
      gl.uniform1f(P.u.dim, pick && pick !== k ? 0.42 : 1); gl.uniform1f(P.u.uoff, k.uoff); gl.bindTexture(gl.TEXTURE_2D, TEX[k.tex].t);
      gl.drawElements(gl.TRIANGLES, SPN, gl.UNSIGNED_SHORT, 0);
    });
    gl.enable(gl.BLEND); gl.depthMask(false);
    // Saturn's rings, on the coin that has them
    if (ringed && TEX.ring.ok) { var rk = planets.filter(function (k) { return k.ring; })[0];
      gl.useProgram(Rg.p); off(); gl.bindBuffer(gl.ARRAY_BUFFER, RGV); gl.enableVertexAttribArray(Rg.a.p); gl.vertexAttribPointer(Rg.a.p, 3, gl.FLOAT, false, 20, 0); gl.enableVertexAttribArray(Rg.a.uv); gl.vertexAttribPointer(Rg.a.uv, 2, gl.FLOAT, false, 20, 12);
      gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA); gl.uniformMatrix4fv(Rg.u.VP, false, VP); gl.uniformMatrix4fv(Rg.u.M, false, model(rk.pos, 0.42, 0, rk.r)); gl.uniform1f(Rg.u.dim, pick && pick !== rk ? 0.42 : 1);
      gl.bindTexture(gl.TEXTURE_2D, TEX.ring.t); gl.uniform1i(Rg.u.tex, 0); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 258); }
    // the orbits, faint
    gl.useProgram(L.p); off(); gl.bindBuffer(gl.ARRAY_BUFFER, CIR); gl.enableVertexAttribArray(L.a.p); gl.vertexAttribPointer(L.a.p, 3, gl.FLOAT, false, 0, 0); gl.uniformMatrix4fv(L.u.VP, false, VP); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    planets.forEach(function (k) { gl.uniform1f(L.u.R, k.R); gl.uniform4f(L.u.col, 1, 0.72, 0.4, pick === k ? 0.55 : pick ? 0.025 : 0.065); gl.drawArrays(gl.LINE_LOOP, 0, 192); });
    // the belt
    gl.useProgram(B.p); off(); gl.bindBuffer(gl.ARRAY_BUFFER, BLT); gl.enableVertexAttribArray(B.a.b); gl.vertexAttribPointer(B.a.b, 4, gl.FLOAT, false, 0, 0); gl.blendFunc(gl.ONE, gl.ONE);
    gl.uniformMatrix4fv(B.u.VP, false, VP); gl.uniform1f(B.u.t, orb); gl.uniform1f(B.u.ps, PS); gl.drawArrays(gl.POINTS, 0, belt.length);
    // the corona, over all, hidden only where a body stands in front of it
    gl.useProgram(C.p); off(); gl.bindBuffer(gl.ARRAY_BUFFER, QUAD); gl.enableVertexAttribArray(C.a.q); gl.vertexAttribPointer(C.a.q, 2, gl.FLOAT, false, 0, 0);
    gl.uniformMatrix4fv(C.u.VP, false, VP); gl.uniform3fv(C.u.rt, CAMX); gl.uniform3fv(C.u.up, CAMY); gl.uniform1f(C.u.sz, 7 * SR); gl.uniform1f(C.u.t, clock); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    gl.depthMask(true);
    labels();
  }
  // the names: outward of each body, the larger coins first; one gives way where it would cross another, the Sun or Bitcoin's own
  function labels() {
    var c0 = project([0, 0, 0]), sr = SR * PS / D / c0[2], taken = [[c0[0] - sr * 1.15, c0[1] - sr * 1.15, c0[0] + sr * 1.15, c0[1] + sr * 1.15]];
    mid.style.left = c0[0] + "px"; mid.style.top = (c0[1] + sr + (narrow ? 26 : 38)) + "px"; taken.push([c0[0] - (narrow ? 100 : 130), c0[1] + sr + 8, c0[0] + (narrow ? 100 : 130), c0[1] + sr + (narrow ? 60 : 84)]);
    planets.forEach(function (k) { var q = project(k.pos); k.sx = q[0]; k.sy = q[1]; k.sr = k.r * PS / D / q[2] * (k.ring ? 2.27 : 1); k.depth = q[2]; });
    planets.forEach(function (k) { var e = k.sr + 2; taken.push([k.sx - e, k.sy - e, k.sx + e, k.sy + e]); });
    planets.forEach(function (k) {
      var side = k.sx >= c0[0] ? 1 : -1, s = k.el.style, w = k.w || (k.w = k.el.offsetWidth), hh = k.n < 12 && !narrow ? 34 : 18;
      // beside it, outward of the Sun; else above it; else below it
      var spots = [[side > 0 ? k.sx + k.sr + 9 : k.sx - k.sr - 9 - w, k.sy, side > 0 ? "left" : "right"],
        [k.sx - w / 2, k.sy - k.sr - 7 - hh / 2, "center"], [k.sx - w / 2, k.sy + k.sr + 7 + hh / 2, "center"]], at = null, bx2;
      for (var c = 0; c < 3 && !at; c++) { var sp = spots[c], lx = narrow ? Math.max(6, Math.min(W - w - 6, sp[0])) : sp[0];
        bx2 = [lx - 6, sp[1] - hh / 2 - 3, lx + w + 6, sp[1] + hh / 2 + 3];
        if (taken.every(function (q) { return bx2[2] < q[0] || bx2[0] > q[2] || bx2[3] < q[1] || bx2[1] > q[3]; })) at = [lx, sp[1], sp[2], bx2]; }
      var free = !!at; if (!at) { var s0 = spots[0]; at = [s0[0], s0[1], s0[2], null]; }
      var behind = Math.hypot(k.sx - c0[0], k.sy - c0[1]) < sr && k.depth > c0[2];
      var want = pick === k ? 1 : behind || !free || (narrow && k.n > 6) ? 0 : pick ? 0.3 : 1; if (at[3] && want > 0) taken.push(at[3]);
      s.left = at[0] + "px"; s.top = at[1] + "px"; s.textAlign = at[2]; s.opacity = document.activeElement === k.el ? 1 : want; s.pointerEvents = want > 0.5 ? "auto" : "none";
    });
    if (pick && pick.n == null) { var a = pick.a0 + omega(pick.R) * orb, q2 = project([pick.R * Math.cos(a), pick.y, pick.R * Math.sin(a)]), ts = tip.style;
      tip.href = "#" + pick.id; tip.firstChild.textContent = pick.name; tip.lastChild.innerHTML = pick.capText + " · " + pick.day; ts.left = (q2[0] + 12) + "px"; ts.top = q2[1] + "px"; ts.opacity = 1; } else tip.style.opacity = 0;
  }
  function frame(now) {
    var dt = last ? Math.min(0.05, (now - last) / 1000) : 0; last = now; clock += dt; if (!pick) orb += dt;
    draw(); run = !still && seen && !document.hidden ? requestAnimationFrame(frame) : 0;
  }
  function wake() { if (still) { requestAnimationFrame(draw); return; } if (!run && seen && !document.hidden) { last = 0; run = requestAnimationFrame(frame); } }
  // a body itself can be pointed at and pressed, as its name can
  function near(e) { var b = cv.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top, hit = null, best = 1e9;
    planets.forEach(function (k) { var d = Math.hypot(k.sx - x, k.sy - y); if (d < Math.max(12, k.sr * (k.ring ? 0.5 : 1) + 6) && d < best) { best = d; hit = k; } });
    if (!hit) belt.forEach(function (k) { var a = k.a0 + omega(k.R) * orb, q = project([k.R * Math.cos(a), k.y, k.R * Math.sin(a)]), d = Math.hypot(q[0] - x, q[1] - y); if (d < 9 && d < best) { best = d; hit = k; } });
    return hit; }
  cv.addEventListener("pointermove", function (e) { var k = near(e); if (k !== pick) { pick = k; wake(); } cv.style.cursor = pick ? "pointer" : ""; });
  cv.addEventListener("pointerleave", function () { pick = null; wake(); });
  cv.addEventListener("click", function (e) { var k = near(e); if (k) location.hash = k.id; });
  box.hidden = false; document.querySelector("main").classList.add("has-sun");
  if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { seen = en[0].isIntersecting; wake(); }).observe(box);
  document.addEventListener("visibilitychange", wake);
  if ("ResizeObserver" in window) new ResizeObserver(size).observe(box); else window.addEventListener("resize", size);
  size();
})();
