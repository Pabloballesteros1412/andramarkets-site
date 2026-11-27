/* Daily close notes: the sessions as a ribbon of light (owner, 24 Nov 2026). Over the archive, the S&P 500's close
   runs as one line across every published note, and each note is a point of light on it, with a tick up for a day
   the index rose and down for a day it fell. Pointing at a session shows its date, its headline and the index's
   close and change, with its sign; a press opens the note. With nothing pointed at, the latest note shows. The
   archive's own rows are the source (their data-spx and data-chg), and the list stays below. */
(function () {
  "use strict";
  var head = document.querySelector(".page__head"), rows = [].slice.call(document.querySelectorAll(".note-list a[data-spx]")); if (!head || rows.length < 5) return;
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches, MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var N = rows.map(function (a) { var t = a.querySelector("time"), d = t.getAttribute("datetime"); return { href: a.getAttribute("href"), d: d, y: +d.slice(0, 4), m: +d.slice(5, 7) - 1, day: +d.slice(8, 10), title: a.querySelector(".note-list__title").textContent, v: +a.getAttribute("data-spx"), c: +a.getAttribute("data-chg") }; })
    .sort(function (a, b) { return a.d < b.d ? -1 : 1; });
  var box = document.createElement("div"); box.className = "nr"; var cv = document.createElement("canvas"); cv.setAttribute("aria-hidden", "true"); box.appendChild(cv); var cx = cv.getContext("2d"); if (!cx) return;
  var card = document.createElement("a"); card.className = "nr__card"; card.innerHTML = '<span class="nr__date"></span><b></b><span class="nr__fig"></span><em>Read the note</em>'; box.appendChild(card);
  var down = document.createElement("a"); down.className = "lib-map__down"; down.href = "#all-notes"; down.textContent = "All notes"; box.appendChild(down);
  head.appendChild(box); document.querySelector("main").classList.add("has-ribbon");
  var TOP = 0, W, H, dpr, narrow, X0, X1, Y0, Y1, lo = Infinity, hi = -Infinity, pick = N.length - 1, shown = -1, px = -1, run = 0, visible = true, t0 = performance.now();
  N.forEach(function (n) { lo = Math.min(lo, n.v); hi = Math.max(hi, n.v); });
  function xOf(i) { return X0 + i / (N.length - 1) * (X1 - X0); } function yOf(v) { return Y1 - (v - lo) / ((hi - lo) || 1) * (Y1 - Y0); }
  function signed(c) { return (c < 0 ? "−" : "+") + Math.abs(c).toFixed(2) + "%"; }
  function show(i) { if (i === shown) return; shown = i; var n = N[i]; card.href = n.href; card.children[0].textContent = n.day + " " + MON[n.m] + " " + n.y; card.children[1].textContent = n.title;
    card.children[2].innerHTML = "S&amp;P 500 " + n.v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' <span class="mv mv--' + (n.c < 0 ? "down" : "up") + '">' + signed(n.c) + "</span>"; place(); }
  function place() { if (narrow) { card.style.top = ""; return; } card.style.top = (TOP + 26) + "px"; } // the card keeps one place, under the title and over the line
  function size() { narrow = box.clientWidth < 900; W = box.clientWidth; H = box.clientHeight; dpr = Math.min(window.devicePixelRatio || 1, 2); cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
    var top = 24, t = head.querySelector(".page__title"); if (!narrow && t) { TOP = Math.max(24, t.getBoundingClientRect().bottom - box.getBoundingClientRect().top); top = TOP + 230; }
    var side = narrow ? 20 : Math.max(0, (W - 1328) / 2) + 76; X0 = side; X1 = W - side; Y0 = narrow ? 30 : top; Y1 = H - (narrow ? 46 : 150); place(); }
  function glow(x, y, r, a) { var g = cx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, "rgba(255,255,255," + a + ")"); g.addColorStop(0.25, "rgba(215,230,255," + a * 0.45 + ")"); g.addColorStop(1, "rgba(190,215,255,0)"); cx.fillStyle = g; cx.fillRect(x - r, y - r, r * 2, r * 2); }
  function line(off, upto) { cx.beginPath(); for (var i = 0; i <= upto; i++) { var x = xOf(i), y = yOf(N[i].v) + off; if (i) { var xp = xOf(i - 1), yp = yOf(N[i - 1].v) + off, mx = (xp + x) / 2; cx.bezierCurveTo(mx, yp, mx, y, x, y); } else cx.moveTo(x, y); } }
  function draw(now) {
    var t = still ? 9 : (now - t0) / 1000, e0 = still ? 1 : Math.min(1, t / 1.8), ease = 1 - Math.pow(1 - e0, 3), upto = Math.round((N.length - 1) * ease);
    cx.setTransform(dpr, 0, 0, dpr, 0, 0); cx.clearRect(0, 0, W, H); cx.globalCompositeOperation = "lighter";
    cx.font = "300 12px Inter,Arial,sans-serif"; cx.textBaseline = "middle"; cx.textAlign = "left"; var lastM = -1;
    N.forEach(function (n, i) { if (n.m === lastM) return; lastM = n.m; var x = xOf(i); cx.fillStyle = "rgba(226,236,252,0.45)"; cx.fillText(MON[n.m] + (narrow ? "" : " " + n.y), x, Y1 + (narrow ? 30 : 56)); cx.fillStyle = "rgba(226,236,252,0.12)"; cx.fillRect(x, Y0 - 10, 1, Y1 - Y0 + (narrow ? 26 : 50)); });
    cx.lineJoin = "round"; cx.strokeStyle = "rgba(200,220,255,0.06)"; cx.lineWidth = 9; line(0, upto); cx.stroke();
    cx.strokeStyle = "rgba(226,236,252,0.2)"; cx.lineWidth = 0.6; line(-2.2, upto); cx.stroke(); line(2.2, upto); cx.stroke();
    cx.strokeStyle = "rgba(240,246,255,0.9)"; cx.lineWidth = 1.2; line(0, upto); cx.stroke();
    var sel = shown < 0 ? pick : shown; if (!narrow && e0 >= 1) { cx.fillStyle = "rgba(226,236,252,0.3)"; cx.fillRect(xOf(sel), Y0 - 36, 1, yOf(N[sel].v) - Y0 + 28); }
    for (var i = 0; i <= upto; i++) { var n = N[i], x = xOf(i), y = yOf(n.v), on = i === sel, up = n.c >= 0, len = Math.min(26, 5 + Math.abs(n.c) * 4.5);
      cx.strokeStyle = up ? "rgba(70,210,130," + (on ? 0.95 : 0.6) + ")" : "rgba(245,95,95," + (on ? 0.95 : 0.6) + ")"; cx.lineWidth = on ? 1.6 : 1; cx.beginPath(); cx.moveTo(x, y + (up ? -5 : 5)); cx.lineTo(x, y + (up ? -5 - len : 5 + len)); cx.stroke(); // up for a rise, down for a fall
      glow(x, y, on ? 20 : 8, on ? 0.6 : 0.5); glow(x, y, on ? 5 : 2.6, 0.95); }
    if (e0 >= 1) { var s = N[sel], sx = xOf(sel), sy = yOf(s.v), beat = still ? 0.5 : 0.5 + 0.5 * Math.sin(t * 1.3);
      for (var r0 = 0; r0 < 4; r0++) { var ang = 0.3 + r0 * 1.5708 + (still ? 0 : t * 0.07), ln = (r0 % 2 ? 11 : 20) + 3 * beat, g2 = cx.createLinearGradient(sx, sy, sx + Math.cos(ang) * ln, sy + Math.sin(ang) * ln); g2.addColorStop(0, "rgba(255,255,255,0.9)"); g2.addColorStop(1, "rgba(190,215,255,0)"); cx.strokeStyle = g2; cx.lineWidth = 0.8; cx.beginPath(); cx.moveTo(sx, sy); cx.lineTo(sx + Math.cos(ang) * ln, sy + Math.sin(ang) * ln); cx.stroke(); }
      if (!still) { var f = (t * 0.06) % 1, fi = f * (N.length - 1), a = Math.floor(fi), u = fi - a, b = Math.min(N.length - 1, a + 1); glow(xOf(a) + (xOf(b) - xOf(a)) * u, yOf(N[a].v) + (yOf(N[b].v) - yOf(N[a].v)) * u, 10, 0.6); } }
    return e0 < 1;
  }
  function frame(now) { run = 0; var more = draw(now); if ((more || !still) && visible) run = requestAnimationFrame(frame); }
  function once() { if (!run) run = requestAnimationFrame(frame); }
  function near(e) { var b = box.getBoundingClientRect(); px = e.clientX - b.left; return Math.max(0, Math.min(N.length - 1, Math.round((px - X0) / (X1 - X0) * (N.length - 1)))); }
  cv.addEventListener("pointermove", function (e) { show(near(e)); cv.style.cursor = "pointer"; once(); });
  cv.addEventListener("pointerleave", function () { if (!narrow) show(pick); once(); });
  cv.addEventListener("click", function (e) { var i = near(e); if (narrow && i !== shown) { show(i); once(); return; } location.href = N[i].href; });
  window.addEventListener("resize", function () { size(); once(); });
  if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { visible = en[0].isIntersecting; if (visible) once(); }).observe(box);
  size(); show(pick); if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { size(); once(); }); once();
})();
