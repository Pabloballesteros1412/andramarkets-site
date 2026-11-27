/* Market history: the falls under water (owner, 24 Nov 2026). Over the page, how far the S&P 500 stood below its
   last record close, every day since 1928: the surface is a record high, and each fall hangs from it as a valley
   of light, deeper the worse it was. The deepest are marked with their year and depth. Pointing shows the date,
   the depth there and the episode those months belong to, with its own fall; a press opens that episode. Drawn
   from the page's own data (#mh-overview: the closes and the episodes), and the chart and list stay below. */
(function () {
  "use strict";
  var el = document.getElementById("mh-overview"), head = document.querySelector(".page__head"); if (!el || !head) return;
  var D; try { D = JSON.parse(el.textContent); } catch (err) { return; } if (!D.d || D.d.length < 50 || !D.eps) return;
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches, MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  function day(s) { return Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +(s.slice(8, 10) || 1)) / 864e5; }
  function pct(v) { return (v < -0.0005 ? "−" : "") + Math.abs(v * 100).toFixed(1) + "%"; }
  var top = 0, P = D.d.map(function (r) { if (r[1] > top) top = r[1]; return { t: day(r[0]), s: r[0], dd: r[1] / top - 1 }; });
  var E = D.eps.map(function (e, i) { var nx = D.eps[i + 1]; return { a: day(e[0] + "-01"), b: nx ? day(nx[0] + "-01") : Infinity, name: e[2], href: e[3] + "/", years: e[4], fall: e[5] }; });
  // the valleys: each stretch below the surface, with its lowest point
  var V = [], cur = null; P.forEach(function (p, i) { if (p.dd < -0.0005) { if (!cur) cur = { i: i, dd: 0 }; if (p.dd < cur.dd) { cur.dd = p.dd; cur.i = i; } } else if (cur) { V.push(cur); cur = null; } }); if (cur) V.push(cur);
  var MARK = []; V.forEach(function (v) { if (v.dd <= -0.3) MARK.push(v.i); });
  // a long stretch under water can hold several great falls (1929 to 1954): mark each episode's own low when it is deep
  E.forEach(function (e) { var lo = -1; P.forEach(function (p, i) { if (p.t >= e.a && p.t < e.b && (lo < 0 || p.dd < P[lo].dd)) lo = i; }); if (lo >= 0 && P[lo].dd <= -0.3 && MARK.every(function (m) { return Math.abs(P[m].t - P[lo].t) > 900; })) MARK.push(lo); });
  var box = document.createElement("div"); box.className = "nr mhw"; var cv = document.createElement("canvas"); cv.setAttribute("aria-hidden", "true"); box.appendChild(cv); var cx = cv.getContext("2d"); if (!cx) return;
  var card = document.createElement("a"); card.className = "nr__card"; card.innerHTML = '<span class="nr__date"></span><b></b><span class="nr__fig"></span><em>Open the episode</em>'; box.appendChild(card);
  var down = document.createElement("a"); down.className = "lib-map__down"; down.href = "#mh-all"; down.textContent = "Every episode"; box.appendChild(down);
  var list = document.querySelector(".mh-tl__list"), sec = list && list.closest("section"); if (sec && !sec.id) sec.id = "mh-all"; else if (sec) down.href = "#" + sec.id;
  head.appendChild(box); document.querySelector("main").classList.add("has-ribbon");
  var W, H, dpr, narrow, X0, X1, Y0, Y1, TOP = 0, T0 = P[0].t, T1 = P[P.length - 1].t, DEEP = -0.9, at = P.length - 1, shown = -2, run = 0, visible = true, t0 = performance.now();
  function xOf(t) { return X0 + (t - T0) / (T1 - T0) * (X1 - X0); } function yOf(dd) { return Y0 + dd / DEEP * (Y1 - Y0); }
  function epOf(t) { for (var i = E.length - 1; i >= 0; i--) if (t >= E[i].a) return E[i]; return E[0]; }
  function show(i) { if (i === shown) return; shown = i; var p = P[i], e = epOf(p.t); card.href = e.href; card.children[0].textContent = e.years; card.children[1].textContent = e.name;
    card.children[2].innerHTML = "Fall in the episode <span class=\"mv mv--down\">" + e.fall + "</span> · " + (+p.s.slice(8, 10)) + " " + MON[+p.s.slice(5, 7) - 1] + " " + p.s.slice(0, 4) + ": " + (p.dd < -0.0005 ? '<span class="mv mv--down">' + pct(p.dd) + "</span> below the record" : "at a record close"); }
  function size() { narrow = box.clientWidth < 900; W = box.clientWidth; H = box.clientHeight; dpr = Math.min(window.devicePixelRatio || 1, 2); cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
    var t = head.querySelector(".page__title"), y0 = 34; if (!narrow && t) { TOP = Math.max(24, t.getBoundingClientRect().bottom - box.getBoundingClientRect().top); y0 = TOP + 190; card.style.top = (TOP + 26) + "px"; } else card.style.top = "";
    var side = narrow ? 20 : Math.max(0, (W - 1328) / 2) + 76; X0 = side + (narrow ? 0 : 40); X1 = W - side; Y0 = y0; Y1 = H - (narrow ? 40 : 120); }
  function glow(x, y, r, a) { var g = cx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, "rgba(255,255,255," + a + ")"); g.addColorStop(0.25, "rgba(215,230,255," + a * 0.45 + ")"); g.addColorStop(1, "rgba(190,215,255,0)"); cx.fillStyle = g; cx.fillRect(x - r, y - r, r * 2, r * 2); }
  function text(s, x, y, a, al, col) { cx.font = "10px Inter,Arial,sans-serif"; cx.textAlign = al || "left"; cx.textBaseline = "middle"; cx.fillStyle = col || "rgba(226,236,252," + a + ")"; cx.fillText(s, x, y); }
  function path(k) { cx.beginPath(); P.forEach(function (p, i) { var x = xOf(p.t), y = Y0 + (yOf(p.dd) - Y0) * k; if (i) cx.lineTo(x, y); else cx.moveTo(x, y); }); }
  function draw(now) {
    var t = still ? 9 : (now - t0) / 1000, e0 = still ? 1 : Math.min(1, t / 2), k = 1 - Math.pow(1 - e0, 3);   // the valleys sink from the surface
    cx.setTransform(dpr, 0, 0, dpr, 0, 0); cx.clearRect(0, 0, W, H); cx.globalCompositeOperation = "lighter";
    [-0.2, -0.4, -0.6, -0.8].forEach(function (v) { var y = yOf(v); cx.fillStyle = "rgba(226,236,252,0.07)"; cx.fillRect(X0, y, X1 - X0, 1); if (!narrow) text(pct(v), X0 - 10, y, 0.4, "right"); });
    for (var yr = 1930; yr <= 2030; yr += 10) { var x = xOf(day(yr + "-01-01")); if (x > X1) break; if (narrow && yr % 20) continue; if (x < X0 + 4) continue; cx.fillStyle = "rgba(226,236,252,0.1)"; cx.fillRect(x, Y0, 1, Y1 - Y0 + 8); text(String(yr), x, Y1 + 22, 0.45, "center"); }
    path(k); cx.lineTo(X1, Y0); cx.lineTo(X0, Y0); cx.closePath(); var g = cx.createLinearGradient(0, Y0, 0, Y1); g.addColorStop(0, "rgba(200,220,255,0.02)"); g.addColorStop(1, "rgba(200,220,255,0.3)"); cx.fillStyle = g; cx.fill();
    cx.lineJoin = "round"; cx.strokeStyle = "rgba(200,220,255,0.07)"; cx.lineWidth = 7; path(k); cx.stroke(); cx.strokeStyle = "rgba(240,246,255,0.9)"; cx.lineWidth = 1.05; path(k); cx.stroke();
    cx.strokeStyle = "rgba(240,246,255,0.55)"; cx.lineWidth = 1; cx.beginPath(); cx.moveTo(X0, Y0); cx.lineTo(X1, Y0); cx.stroke(); if (!narrow) text("RECORD", X0 - 10, Y0, 0.5, "right");
    var lastX = -99; if (e0 >= 1) MARK.slice().sort(function (a, b) { return a - b; }).forEach(function (m) { var p = P[m], x = xOf(p.t), y = yOf(p.dd); if (narrow && (p.dd > -0.45 || x - lastX < 44)) return; lastX = x; // on a phone, only the deepest, and none on top of another
      var side = x < X0 + 44; glow(x, y, 16, 0.5); glow(x, y, 4, 0.95); cx.globalCompositeOperation = "source-over"; if (side) { text(p.s.slice(0, 4), x + 12, y - 6, 0.6, "left"); text(pct(p.dd), x + 12, y + 7, 1, "left", "#ff7a7a"); } else { text(p.s.slice(0, 4), x, y + 16, 0.6, "center"); text(pct(p.dd), x, y + 29, 1, "center", "#ff7a7a"); } cx.globalCompositeOperation = "lighter"; });
    if (e0 >= 1) { var p = P[at], x = xOf(p.t), y = yOf(p.dd), e = epOf(p.t), xa = Math.max(X0, xOf(e.a)), xb = Math.min(X1, e.b === Infinity ? X1 : xOf(e.b));
      cx.fillStyle = "rgba(200,220,255,0.07)"; cx.fillRect(xa, Y0, Math.max(2, xb - xa), Y1 - Y0); cx.fillStyle = "rgba(240,246,255,0.8)"; cx.fillRect(xa, Y0 - 3, Math.max(2, xb - xa), 2);   // the episode those months belong to
      cx.fillStyle = "rgba(226,236,252,0.35)"; cx.fillRect(x, Y0 - 24, 1, y - Y0 + 24); glow(x, y, 18, 0.6); glow(x, y, 5, 0.95); }
    return e0 < 1;
  }
  function frame(now) { run = 0; var more = draw(now); if (more && visible) run = requestAnimationFrame(frame); }
  function once() { if (!run) run = requestAnimationFrame(frame); }
  function near(e) { var b = box.getBoundingClientRect(), t = T0 + (e.clientX - b.left - X0) / (X1 - X0) * (T1 - T0), lo = 0, hi = P.length - 1; while (lo < hi) { var m = (lo + hi) >> 1; if (P[m].t < t) lo = m + 1; else hi = m; }
    var e2 = epOf(P[lo].t), best = lo; for (var i = Math.max(0, lo - 12); i <= Math.min(P.length - 1, lo + 12); i++) if (Math.abs(xOf(P[i].t) - xOf(P[lo].t)) < 5 && P[i].dd < P[best].dd && epOf(P[i].t) === e2) best = i; return best; }
  cv.addEventListener("pointermove", function (e) { at = near(e); show(at); cv.style.cursor = "pointer"; once(); });
  cv.addEventListener("pointerleave", function () { if (!narrow) { at = P.length - 1; show(at); once(); } });
  cv.addEventListener("click", function (e) { var i = near(e); if (narrow && epOf(P[i].t) !== epOf(P[shown < 0 ? 0 : shown].t)) { at = i; show(i); once(); return; } location.href = epOf(P[i].t).href; });
  window.addEventListener("resize", function () { size(); once(); });
  if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { visible = en[0].isIntersecting; if (visible) once(); }).observe(box);
  size(); show(at); if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { size(); once(); }); once();
})();
