/* Markets Interview Prep: say it in thirty seconds (owner, 26 Nov 2026). Under the page head, a clock of light
   beside one of this week's topics and its "Say it in an interview" line: a ring of fine strands with thirty ticks
   round it, the seconds in its middle. Nothing runs until the reader presses Start; then the ring fills over thirty
   seconds while they say it aloud, and stops at "Time". Next and Previous change the topic (the arrow keys too, on
   the row of marks); the clock never moves on by itself. The topics are the page's own, read from the list below,
   which stays as it is; each topic's title leads down to it. Without this script the page is that list. */
(function () {
  "use strict";
  var list = document.querySelector(".ip-week"), head = document.querySelector("main .page__head");
  if (!list || !head || !document.createElement("canvas").getContext) return;
  var topics = [].map.call(list.querySelectorAll(".ip-topic"), function (li, i) {
    var h = li.querySelector("h3"), say = "", dts = li.querySelectorAll("dt");
    [].forEach.call(dts, function (dt) { if (/say it/i.test(dt.textContent) && dt.nextElementSibling) say = dt.nextElementSibling.textContent; });
    if (!li.id) li.id = "ip-topic-" + (i + 1);
    return h && say ? { id: li.id, title: h.textContent, say: say } : null;
  }).filter(Boolean);
  if (topics.length < 2) return;
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches, TAU = Math.PI * 2, SECS = 30, INK = "214,228,255";
  var seed = 5; function rnd() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
  var strands = []; for (var k = 0; k < 26; k++) strands.push({ r: (rnd() - 0.5) * 0.09, e: (rnd() - 0.5) * 0.05 });

  var box = document.createElement("section"); box.className = "ic"; box.setAttribute("aria-label", "Say it in thirty seconds");
  box.innerHTML = '<div class="ic__clock"><canvas aria-hidden="true"></canvas><div class="ic__mid"><span class="lens-read ic__over">Say it in</span><span class="ic__secs" role="timer" aria-live="off">0:30</span><span class="lens-read ic__under">thirty seconds</span></div></div>' +
    '<div class="ic__text"><p class="lens-read ic__count"></p><h2 class="ic__title"><a></a></h2><p class="ic__say"></p>' +
    '<div class="ic__acts"><button class="btn" type="button" data-ic="go">Start</button><button class="btn btn--ghost" type="button" data-ic="prev">Previous</button><button class="btn btn--ghost" type="button" data-ic="next">Next</button></div>' +
    '<div class="ic__marks" role="tablist" aria-label="This week\'s topics"></div><p class="visually-hidden" role="status" aria-live="polite"></p></div>';
  head.parentNode.insertBefore(box, head.nextSibling); document.querySelector("main").classList.add("has-clock");
  var cv = box.querySelector("canvas"), c = cv.getContext("2d"), secs = box.querySelector(".ic__secs"), over = box.querySelector(".ic__over"), under = box.querySelector(".ic__under"),
    count = box.querySelector(".ic__count"), title = box.querySelector(".ic__title a"), say = box.querySelector(".ic__say"), go = box.querySelector('[data-ic="go"]'),
    marks = box.querySelector(".ic__marks"), status = box.querySelector('[role="status"]');
  topics.forEach(function (t, i) { var b = document.createElement("button"); b.type = "button"; b.setAttribute("role", "tab"); b.setAttribute("aria-label", (i + 1) + ". " + t.title); b.addEventListener("click", function () { show(i); }); marks.appendChild(b); });

  var at = 0, t0 = 0, spent = 0, running = false, raf = 0, S = 0;
  function left() { return Math.max(0, SECS - spent); }
  function clock() { var s = Math.ceil(left() - 1e-6); secs.textContent = "0:" + (s < 10 ? "0" : "") + s; }
  function draw() {
    if (!S) return;
    var cx = S / 2, cy = S / 2, R = S * 0.42, f = Math.min(1, spent / SECS), a0 = -Math.PI / 2, i;
    c.clearRect(0, 0, S, S); c.globalCompositeOperation = "lighter";
    strands.forEach(function (s) {
      c.beginPath(); c.arc(cx, cy, R * (1 + s.r), 0, TAU); c.strokeStyle = "rgba(" + INK + ",.05)"; c.lineWidth = 0.7; c.stroke();
      if (f > 0) { c.beginPath(); c.arc(cx, cy, R * (1 + s.r), a0, a0 + Math.max(0.001, f * TAU + s.e)); c.strokeStyle = "rgba(" + INK + ",.16)"; c.stroke(); }
    });
    if (f > 0) {
      c.beginPath(); c.arc(cx, cy, R, a0, a0 + f * TAU); c.strokeStyle = "rgba(255,255,255,.95)"; c.lineWidth = 1.6; c.stroke();
      var a = a0 + f * TAU, x = cx + R * Math.cos(a), y = cy + R * Math.sin(a), g = c.createRadialGradient(x, y, 0, x, y, S * 0.055);
      g.addColorStop(0, "rgba(255,255,255,1)"); g.addColorStop(1, "rgba(" + INK + ",0)"); c.fillStyle = g; c.beginPath(); c.arc(x, y, S * 0.055, 0, TAU); c.fill();
    }
    for (i = 0; i < SECS; i++) { var t = i / SECS * TAU - Math.PI / 2, r1 = R * 1.11, r2 = R * (i % 5 ? 1.135 : 1.165); c.beginPath(); c.moveTo(cx + r1 * Math.cos(t), cy + r1 * Math.sin(t)); c.lineTo(cx + r2 * Math.cos(t), cy + r2 * Math.sin(t)); c.strokeStyle = "rgba(" + INK + "," + (i / SECS < f ? 0.9 : 0.4) + ")"; c.lineWidth = 0.8; c.stroke(); }
  }
  function size() { var d = Math.min(window.devicePixelRatio || 1, 2), w = cv.clientWidth; if (!w) return; S = w; cv.width = cv.height = Math.round(w * d); c.setTransform(d, 0, 0, d, 0, 0); draw(); }
  function words() {
    var done = left() <= 0;
    over.textContent = done ? "That was" : running ? "Say it aloud" : spent ? "Paused at" : "Say it in";
    under.textContent = done ? "thirty seconds" : running || spent ? "left of thirty seconds" : "thirty seconds";
    go.textContent = done ? "Again" : running ? "Pause" : spent ? "Resume" : "Start";
    box.classList.toggle("is-done", done);
  }
  function tick(now) {
    spent += (now - t0) / 1000; t0 = now;
    if (left() <= 0) { spent = SECS; running = false; status.textContent = "Time. Thirty seconds are up."; }
    clock(); draw(); words();
    raf = running ? requestAnimationFrame(tick) : 0;
  }
  function stop() { running = false; if (raf) cancelAnimationFrame(raf); raf = 0; }
  function reset() { stop(); spent = 0; status.textContent = ""; clock(); draw(); words(); }
  function show(i) {
    at = (i + topics.length) % topics.length; var t = topics[at];
    count.textContent = "This week · " + (at + 1) + " of " + topics.length; title.textContent = t.title; title.href = "#" + t.id; say.textContent = t.say;
    [].forEach.call(marks.children, function (b, j) { b.setAttribute("aria-selected", j === at ? "true" : "false"); b.tabIndex = j === at ? 0 : -1; });
    reset();
  }
  go.addEventListener("click", function () {
    if (running) { stop(); words(); return; }
    if (left() <= 0) spent = 0;
    running = true; status.textContent = "Thirty seconds, started."; t0 = performance.now(); words(); raf = requestAnimationFrame(tick);
  });
  box.querySelector('[data-ic="prev"]').addEventListener("click", function () { show(at - 1); });
  box.querySelector('[data-ic="next"]').addEventListener("click", function () { show(at + 1); });
  marks.addEventListener("keydown", function (e) { var d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (!d) return; e.preventDefault(); show(at + d); marks.children[at].focus(); });
  document.addEventListener("visibilitychange", function () { if (document.hidden && running) { stop(); words(); } });   // a hidden tab would lose count
  if ("ResizeObserver" in window) new ResizeObserver(size).observe(cv); else window.addEventListener("resize", size);
  if (still) box.classList.add("is-still");
  show(0); size();
})();
