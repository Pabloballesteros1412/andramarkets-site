/* Crypto: where the coins trade (owner-approved sketch and build, 27 Nov 2026: "sober, like the maps, and
   realistic"). The real Earth in WebGL, lit as it was at the time of the data: its day surface, clouds and city
   lights from NASA imagery (Solar System Scope, CC BY 4.0, credited on the page), a thin atmosphere at the limb and
   the site's own sky behind. A fragment shader casts each pixel's ray at the sphere. Over it, on a 2D canvas, a column of
   amber light rises from each country where exchanges declare their seat, as tall as that country's share of the
   day's trading; the column leans outward from the globe and always rises up the screen, so a country seen from
   straight above keeps its height. The globe goes slowly from one place to the next, the largest first, and names
   the place it comes to. Pointing at a column stops it there and names its largest exchanges; dragging turns the
   globe, and the tour takes up again a few seconds after. The arrow keys move between places. The figures are the
   page's own (the JSON under the section and the table of seats); without WebGL the section stays hidden. It
   draws only while on screen, and holds still under reduced motion. */
(function () {
  "use strict";
  var box = document.querySelector(".cg"), src = box && box.querySelector('script[type="application/json"]'); if (!box || !src) return;
  var DATA; try { DATA = JSON.parse(src.textContent); } catch (e) { return; }
  var P = (DATA.places || []).filter(function (p) { return p.share > 0; }); if (!P.length) return;
  var gcv = box.querySelector(".cg__gl"), ov = box.querySelector(".cg__ov"), layer = box.querySelector(".cg__names"), status = box.querySelector(".cg__status");
  var gl = null; try { gl = gcv.getContext("webgl", { antialias: false, alpha: true, premultipliedAlpha: true }); } catch (e) { gl = null; }
  var c = ov.getContext("2d"); if (!gl || !c) return;
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches, RAD = Math.PI / 180, FOV = 30 * RAD, TN = Math.tan(FOV / 2);
  var BASE = (document.body.getAttribute("data-base") || "../") + "assets/crypto/", TOP = P[0].share;
  // Network (crypto/network/): the same Earth with a point of light for each Lightning node that publishes where it is; the places are then countries, named without a column.
  var PTS = DATA.points ? DATA.points.map(function (q) { var cl = Math.cos(q[1] * Math.PI / 180); return [cl * Math.sin(q[0] * Math.PI / 180), Math.sin(q[1] * Math.PI / 180), cl * Math.cos(q[0] * Math.PI / 180), q[2] || 0]; }) : null;
  function vec(lon, lat) { var cl = Math.cos(lat * RAD); return [cl * Math.sin(lon * RAD), Math.sin(lat * RAD), cl * Math.cos(lon * RAD)]; }
  function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
  function norm(a) { var l = Math.hypot(a[0], a[1], a[2]); return [a[0] / l, a[1] / l, a[2] / l]; }
  function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
  function pct(v) { return v < 0.01 ? (v * 100).toFixed(1) + "%" : Math.round(v * 100) + "%"; }
  // The Sun where it stood when the figures were taken (a low-precision solar position, ample for the light)
  function sunAt(t) { var n = (t - Date.UTC(2000, 0, 1, 12)) / 864e5, L = (280.46 + 0.9856474 * n) * RAD, g = (357.528 + 0.9856003 * n) * RAD;
    var lam = L + (1.915 * Math.sin(g) + 0.02 * Math.sin(2 * g)) * RAD, eps = 23.439 * RAD, dec = Math.asin(Math.sin(eps) * Math.sin(lam));
    var ra = Math.atan2(Math.cos(eps) * Math.sin(lam), Math.cos(lam)), gmst = (280.46061837 + 360.98564736629 * n) * RAD; return vec((ra - gmst) / RAD, dec / RAD); }
  var when = Date.parse(DATA.asof); var SUN = sunAt(isNaN(when) ? Date.now() : when);

  // ---- the Earth -------------------------------------------------------------------------------------------
  var FS = ["precision highp float;uniform vec2 res;uniform float oy,tn,t;uniform vec3 cam,fw,rt,up,sun;uniform sampler2D day,night,cloud;",
    "const float PI=3.14159265;vec2 ll(vec3 n){return vec2(atan(n.x,n.z)/(2.*PI)+.5,acos(clamp(n.y,-1.,1.))/PI);}",
    "void main(){vec2 f=(gl_FragCoord.xy-vec2(.5*res.x,(.5+oy)*res.y))/(.5*res.y);vec3 d=normalize(fw+f.x*tn*rt+f.y*tn*up);",
    "float b=dot(cam,d),h=b*b-dot(cam,cam)+1.;vec3 col;",
    // off the globe: the stars, and the atmosphere's glow where the ray passes close above the limb
    "if(h<0.||b>0.){col=vec3(0.);float ca=length(cam-d*b),alt=max(ca-1.,0.);vec3 pc=normalize(cam-d*b);",
    " float lit=smoothstep(-.35,.25,dot(pc,sun));col+=vec3(.3,.55,1.)*(exp(-alt*55.)*.85+exp(-alt*14.)*.2)*lit;",
    " col+=vec3(1.,.55,.3)*exp(-alt*60.)*.22*smoothstep(.25,0.,abs(dot(pc,sun)))*lit;gl_FragColor=vec4(col,clamp(max(col.r,max(col.g,col.b)),0.,1.));return;}",
    "vec3 p=cam+d*(-b-sqrt(h)),n=normalize(p),v=-d;vec2 uv=ll(n);",
    "vec3 dc=pow(texture2D(day,uv).rgb,vec3(1.1)),nc=texture2D(night,uv).rgb;float cl=texture2D(cloud,uv+vec2(t*.0004,0.)).r;",
    "float ndl=dot(n,sun),dayk=smoothstep(-.12,.22,ndl);",
    // the oceans by their colour, for the Sun's glint
    "float water=smoothstep(.02,.1,dc.b-dc.r)*(1.-smoothstep(.25,.45,dc.g));float spec=pow(max(dot(n,normalize(sun+v)),0.),60.)*water*.9*dayk;",
    "vec3 lit=dc*(.04+1.25*max(ndl,0.))*dayk+vec3(1.,.9,.75)*spec;vec3 lights=nc*nc*vec3(1.6,1.15,.7)*2.2*(1.-dayk)*(1.-cl*.8);",
    "vec3 cc=vec3(1.)*(.03+1.15*max(ndl,0.))*dayk+vec3(.02,.025,.035);col=mix(lit+lights,cc,cl*.85);",
    "float rim=pow(1.-max(dot(n,v),0.),3.);col+=vec3(.35,.6,1.)*rim*.9*smoothstep(-.2,.35,ndl);",
    "col=mix(col,vec3(1.,.5,.25)*rim*.7,smoothstep(.22,0.,abs(ndl))*rim*.6);col=col/(1.+col*.25);gl_FragColor=vec4(pow(col,vec3(.9)),1.);}"].join("");
  var pr, U = {};
  try {
    var sh = function (type, s) { var o = gl.createShader(type); gl.shaderSource(o, s); gl.compileShader(o); if (!gl.getShaderParameter(o, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(o)); return o; };
    pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, "attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}")); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(pr); if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) throw new Error("link");
  } catch (e) { return; }
  gl.useProgram(pr);
  ["res", "oy", "tn", "t", "cam", "fw", "rt", "up", "sun", "day", "night", "cloud"].forEach(function (k) { U[k] = gl.getUniformLocation(pr, k); });
  var qb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, qb); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  var ap = gl.getAttribLocation(pr, "p"); gl.enableVertexAttribArray(ap); gl.vertexAttribPointer(ap, 2, gl.FLOAT, false, 0, 0);
  var waiting = 0, ready = false;
  function texture(file, unit, name, grey) { waiting++; var tx = gl.createTexture(), im = new Image();
    im.onload = function () { gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, tx); var f = grey ? gl.LUMINANCE : gl.RGB; gl.texImage2D(gl.TEXTURE_2D, 0, f, f, gl.UNSIGNED_BYTE, im);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE); gl.uniform1i(U[name], unit);
      if (--waiting === 0) { ready = true; box.classList.add("is-ready"); wake(); } };
    im.onerror = function () { box.hidden = true; };   // without its surface there is no Earth to show: the tables stay
    im.src = BASE + file; }
  texture("earth-day.jpg", 0, "day"); texture("earth-night.jpg", 1, "night"); texture("earth-clouds.jpg", 2, "cloud", true);

  // ---- the places the globe goes to: the largest first, one stop for places close together --------------------------
  var STOPS = [];
  P.forEach(function (p) { if (STOPS.length >= 6) return; var v = vec(p.lon, p.lat);
    if (STOPS.every(function (s) { return dot(vec(s.lon, s.lat), v) < Math.cos(38 * RAD); })) STOPS.push({ p: p, lon: p.lon, lat: Math.max(-25, Math.min(38, p.lat)) }); });
  var W = 0, H = 0, D = 1, DIST = 3.9, OY = -0.1, narrow = false, CAM, FW, RT, UP;
  var view = { lon: STOPS[0].lon, lat: STOPS[0].lat }, from = null, to = null, k = 0, at = 0, hold = 0, focus = STOPS[0].p, pick = null, drag = null, idle = 0, clock = 0;
  function camera() { var dir = vec(view.lon, view.lat); CAM = [dir[0] * DIST, dir[1] * DIST, dir[2] * DIST]; FW = norm([-CAM[0], -CAM[1], -CAM[2]]); RT = norm(cross(FW, [0, 1, 0])); UP = cross(RT, FW); }
  function project(p) { var r = [p[0] - CAM[0], p[1] - CAM[1], p[2] - CAM[2]], z = dot(r, FW); return [W / 2 + dot(r, RT) / z / TN * H / 2, H / 2 - H * OY - dot(r, UP) / z / TN * H / 2]; }
  function size() {
    D = Math.min(window.devicePixelRatio || 1, 1.75); W = gcv.clientWidth; H = gcv.clientHeight; if (!W) return; narrow = W < 700;
    DIST = narrow ? 1 / Math.sin(Math.atan(TN * Math.min(1, W / H) * 0.86)) : 3.9; OY = narrow ? -0.04 : -0.1;
    gcv.width = ov.width = Math.round(W * D); gcv.height = ov.height = Math.round(H * D); gl.viewport(0, 0, gcv.width, gcv.height); c.setTransform(D, 0, 0, D, 0, 0); if (run) draw(); wake();
  }
  function go(i) { at = (i + STOPS.length) % STOPS.length; from = { lon: view.lon, lat: view.lat }; to = STOPS[at]; k = 0; focus = to.p; hold = 0; say(focus); }
  function say(p) { if (p.label) { if (status) status.textContent = p.name + ": " + p.label + "."; return; } if (status) status.textContent = p.name + ": " + pct(p.share) + " of the day's trading, " + p.n + " exchange" + (p.n > 1 ? "s" : "") + (p.top.length ? ", the largest " + p.top[0] : "") + "."; }
  function ease(x) { return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }
  function step(dt) {
    clock += dt;
    if (drag || pick) return;
    if (idle > 0) { idle -= dt; return; }
    if (to) { k = Math.min(1, k + dt / 2.6); var e = ease(k), dl = ((to.lon - from.lon + 540) % 360) - 180; view.lon = from.lon + dl * e; view.lat = from.lat + (to.lat - from.lat) * e; if (k >= 1) to = null; return; }
    hold += dt; if (hold > 4.5 && !still) go(at + 1);
  }

  // ---- drawing -----------------------------------------------------------------------------------------------
  function draw() {
    if (!W || !ready) return; camera();
    gl.uniform2f(U.res, gcv.width, gcv.height); gl.uniform1f(U.oy, OY); gl.uniform1f(U.tn, TN); gl.uniform1f(U.t, clock);
    gl.uniform3fv(U.cam, CAM); gl.uniform3fv(U.fw, FW); gl.uniform3fv(U.rt, RT); gl.uniform3fv(U.up, UP); gl.uniform3fv(U.sun, SUN); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    columns();
  }
  var COLS = [];
  function columns() {
    c.clearRect(0, 0, W, H); COLS = []; var scale = Math.min(1.25, H / 760) * (narrow ? 0.8 : 1), lit = pick || focus;
    if (PTS) { c.globalCompositeOperation = "lighter"; var inv = 1 / DIST;
      for (var q = 0; q < PTS.length; q++) { var v = PTS[q], f = (v[0] * CAM[0] + v[1] * CAM[1] + v[2] * CAM[2]) * inv; if (f < 0.3) continue; var s = project(v), r = 0.9 + v[3] * 1.6, al = Math.min(1, (f - 0.3) * 3);
        c.fillStyle = "rgba(255,176,72," + (0.22 * al).toFixed(3) + ")"; c.beginPath(); c.arc(s[0], s[1], r * 2.6, 0, 7); c.fill(); c.fillStyle = "rgba(255,226,170," + (0.9 * al).toFixed(3) + ")"; c.fillRect(s[0] - r / 2, s[1] - r / 2, r, r); }
      c.globalCompositeOperation = "source-over"; }
    P.forEach(function (p) {
      var n = vec(p.lon, p.lat), face = dot(n, norm([CAM[0] - n[0], CAM[1] - n[1], CAM[2] - n[2]])); if (face < 0.04) return;
      var a = project(n), o = project([n[0] * 1.05, n[1] * 1.05, n[2] * 1.05]), dx = o[0] - a[0], dy = o[1] - a[1], l = Math.hypot(dx, dy) || 1;
      var sk = Math.min(1, l / (0.05 * H * 0.9)); dx = dx / l * sk; dy = dy / l * sk - (1 - sk); l = Math.hypot(dx, dy) || 1; dx /= l; dy /= l;   // outward from the globe; up the screen where the outward way points at us
      var len = (12 + 170 * Math.sqrt(p.share / TOP)) * scale, fade = Math.min(1, (face - 0.04) / 0.25) * (lit && lit !== p ? 0.45 : 1), w = 1 + 2.2 * Math.sqrt(p.share / TOP);
      var tx = a[0] + dx * len, ty = a[1] + dy * len;
      if (PTS) { COLS.push({ p: p, a: a, t: [a[0], a[1] - 6], fade: fade }); return; }
      COLS.push({ p: p, a: a, t: [tx, ty], fade: fade });
      var g = c.createLinearGradient(a[0], a[1], tx, ty);
      g.addColorStop(0, "rgba(255,230,190," + 0.95 * fade + ")"); g.addColorStop(0.6, "rgba(255,180,90," + 0.6 * fade + ")"); g.addColorStop(1, "rgba(255,160,60,0)");
      c.lineCap = "round"; c.globalCompositeOperation = "lighter"; c.strokeStyle = g;
      c.globalAlpha = 0.16; c.lineWidth = w * 3.2; c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(tx, ty); c.stroke();
      c.globalAlpha = 1; c.lineWidth = w; c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(tx, ty); c.stroke();
      c.globalCompositeOperation = "source-over"; c.lineWidth = Math.max(0.8, w * 0.45); c.globalAlpha = 0.7 * fade; c.stroke(); c.globalAlpha = 1;   // a core that holds on the day side too
      var r = 3 + w * 2.4, rg = c.createRadialGradient(a[0], a[1], 0, a[0], a[1], r); c.globalCompositeOperation = "lighter";
      rg.addColorStop(0, "rgba(255,244,220," + fade + ")"); rg.addColorStop(0.35, "rgba(255,176,72," + 0.5 * fade + ")"); rg.addColorStop(1, "rgba(255,150,50,0)");
      c.fillStyle = rg; c.beginPath(); c.arc(a[0], a[1], r, 0, 7); c.fill(); c.globalCompositeOperation = "source-over";
    });
    names();
  }
  // the names at the columns' tops: the place in view first, then the larger; one gives way where it would cross another
  var pool = {};
  function names() {
    var taken = [box.querySelector(".cg__big")].filter(Boolean).map(function (el) { var b = el.getBoundingClientRect(), o = box.getBoundingClientRect(); return [b.left - o.left, b.top - o.top, b.right - o.left, b.bottom - o.top]; });
    var lit = pick || focus, order = COLS.slice().sort(function (x, y) { return (y.p === lit) - (x.p === lit) || y.p.share - x.p.share; }), shown = 0, MAX = narrow ? 1 : 10, live = {};
    order.forEach(function (col) {
      var p = col.p, mine = p === lit; if (!mine && (shown >= MAX || p.share < 0.006 || col.fade < 0.3)) return;
      var el = pool[p.name]; if (!el) { el = pool[p.name] = document.createElement("div"); el.className = "cg__name"; el.innerHTML = "<b></b><span class=\"lens-read\"></span>"; el.firstChild.textContent = p.name; layer.appendChild(el); }
      el.lastChild.textContent = p.label ? p.label + (mine && p.more ? " · " + p.more : "") : pct(p.share) + " · " + p.n + " exchange" + (p.n > 1 ? "s" : "") + (mine && p.top.length ? " · " + p.top.join(", ") : "");
      el.classList.toggle("is-on", mine); var w = el.offsetWidth, h = el.offsetHeight, t = col.t;
      var spots = [[t[0] - w / 2, t[1] - h - 6], [t[0] + 8, t[1] - h / 2], [t[0] - w - 8, t[1] - h / 2]], ok = null;
      for (var j = 0; j < 3 && !ok; j++) { var s = spots[j], bx = [s[0] - 4, s[1] - 2, s[0] + w + 4, s[1] + h + 2]; if (bx[0] < 4 || bx[2] > W - 4 || bx[1] < 4) continue;
        if (taken.every(function (q) { return bx[2] < q[0] || bx[0] > q[2] || bx[3] < q[1] || bx[1] > q[3]; })) ok = [s, bx]; }
      if (!ok) return; taken.push(ok[1]); shown++; live[p.name] = 1;
      el.style.transform = "translate(" + ok[0][0].toFixed(1) + "px," + ok[0][1].toFixed(1) + "px)"; el.style.opacity = mine ? 1 : Math.min(1, col.fade).toFixed(2);
    });
    Object.keys(pool).forEach(function (n) { if (!live[n]) pool[n].style.opacity = 0; });
  }

  // ---- motion and the reader's hand ------------------------------------------------------------------------------
  var run = 0, last = 0, seen = true;
  function frame(now) { var dt = last ? Math.min(0.05, (now - last) / 1000) : 0; last = now; step(dt); draw();
    run = !still && seen && !document.hidden ? requestAnimationFrame(frame) : 0; }
  function wake() { if (still) { requestAnimationFrame(draw); return; } if (!run && seen && !document.hidden) { last = 0; run = requestAnimationFrame(frame); } }
  function near(e) { var b = ov.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top, best = PTS ? 34 : 12, hit = null;
    COLS.forEach(function (col) { var ax = col.a[0], ay = col.a[1], vx = col.t[0] - ax, vy = col.t[1] - ay, u = Math.max(0, Math.min(1, ((x - ax) * vx + (y - ay) * vy) / (vx * vx + vy * vy || 1))), d = Math.hypot(ax + vx * u - x, ay + vy * u - y);
      if (d < best) { best = d; hit = col.p; } }); return hit; }
  ov.addEventListener("pointerdown", function (e) { drag = { x: e.clientX, y: e.clientY, lon: view.lon, lat: view.lat, moved: false }; to = null; ov.setPointerCapture(e.pointerId); });
  ov.addEventListener("pointermove", function (e) {
    if (drag) { var dx = e.clientX - drag.x, dy = e.clientY - drag.y; if (Math.abs(dx) + Math.abs(dy) > 4) drag.moved = true;
      var per = 140 / Math.min(W, H) / (narrow ? 1.6 : 1); view.lon = drag.lon - dx * per; view.lat = Math.max(-60, Math.min(70, drag.lat + dy * per)); wake(); draw(); return; }
    var p = near(e); if (p !== pick) { pick = p; if (p) say(p); wake(); if (still) draw(); } ov.style.cursor = p ? "pointer" : "grab"; });
  function release(e) { if (!drag) return; var moved = drag.moved; drag = null; idle = 6; hold = 0; if (!moved) { var p = near(e); if (p) { focus = p; say(p); } } wake(); }
  ov.addEventListener("pointerup", release); ov.addEventListener("pointercancel", release);
  ov.addEventListener("pointerleave", function () { if (pick) { pick = null; wake(); if (still) draw(); } });
  box.tabIndex = 0;
  box.addEventListener("keydown", function (e) { var d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (!d) return; e.preventDefault(); idle = 0; go(at + d); if (still) { view.lon = to.lon; view.lat = to.lat; to = null; draw(); } wake(); });
  box.hidden = false; document.querySelector("main").classList.add("has-globe"); say(focus);
  if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { seen = en[0].isIntersecting; wake(); }).observe(box);
  document.addEventListener("visibilitychange", function () { wake(); });
  if ("ResizeObserver" in window) new ResizeObserver(size).observe(box); else window.addEventListener("resize", size);
  size();
})();
