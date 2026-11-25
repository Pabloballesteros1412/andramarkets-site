/* Recruiting calendar: what lies ahead, as a timeline (owner, 25 Nov 2026). Under the page head, one row for every
   firm that has something ahead of it, in the firm types of the tables, over the eight months from this one, with a
   line at today. Four marks, and only what the firm has said: a full dot where applications close and a ring where
   they open (both dates from the firm, joined by a line when it gave both), a soft bar over the months in which a
   window is expected, and a dotted line for a programme that takes applications on a rolling basis. Each dated mark
   carries its date in words. Firms that have announced nothing are counted at the foot, not drawn. Over it, the next
   closing date in a sentence. The figures are the page's own (the rc-ahead block, written with the tables below);
   today is the reader's. On a phone the sentence and the next few dates stand as a list: the table below is the rest. */
(function () {
  "use strict";
  var src = document.getElementById("rc-ahead"), head = document.querySelector("main .page__head"); if (!src || !head) return;
  var data; try { data = JSON.parse(src.textContent); } catch (e) { return; }
  var NS = "http://www.w3.org/2000/svg", DAY = 864e5, MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var now = new Date(), today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
  var x0 = Date.UTC(now.getFullYear(), now.getMonth(), 1), x1 = Date.UTC(now.getFullYear(), now.getMonth() + 8, 1);
  function T(s) { var a = s.split("-"); return Date.UTC(+a[0], a[1] - 1, +a[2]); }
  function day(t) { var d = new Date(t); return d.getUTCDate() + " " + MON[d.getUTCMonth()]; }
  function away(t) { var n = Math.round((t - today) / DAY); return n === 0 ? "today" : n === 1 ? "tomorrow" : "in " + n + " days"; }

  // What is still ahead, firm by firm, and every dated event to come.
  var rows = [], events = [];
  data.firms.forEach(function (f) {
    var items = [], rolling = false;
    f.items.forEach(function (it) {
      if (it.k === "r") { if (!rolling) { rolling = true; items.push({ k: "r", p: it.p }); } return; }
      if (it.k === "w") { var a = T(it.a), b = T(it.b); if (b >= today && a < x1) items.push({ k: "w", a: a, b: b, t: it.t, x: it.x, p: it.p }); return; }
      var o = it.o ? T(it.o) : null, c = it.c ? T(it.c) : null;
      if (c != null ? c < today : o == null) return;
      items.push({ k: "d", o: o, c: c, p: it.p });
      if (c != null) events.push({ t: c, what: "closes", f: f.f, p: it.p });
      if (o != null && o >= today) events.push({ t: o, what: "opens", f: f.f, p: it.p });
    });
    if (items.length) rows.push({ f: f.f, g: f.g, items: items });
  });
  if (rows.length < 3) return;
  events.sort(function (a, b) { return a.t - b.t; });
  var next = events.filter(function (e) { return e.what === "closes"; })[0];

  var box = document.createElement("div"); box.className = "rk";
  if (next) { var say = document.createElement("p"); say.className = "rk__next"; say.textContent = "Next to close: " + next.f + ", " + day(next.t) + ", " + away(next.t); box.appendChild(say); }
  if (events.length) {   // the phone's list: the next few dates
    var ol = document.createElement("ol"); ol.className = "rk__soon";
    events.slice(0, 4).forEach(function (e) {
      var li = document.createElement("li"), i = document.createElement("span"), b = document.createElement("b"), s = document.createElement("span");
      i.className = "lens-read"; i.textContent = e.what + " " + day(e.t) + " · " + away(e.t); b.textContent = e.f; s.textContent = e.p;
      li.appendChild(i); li.appendChild(b); li.appendChild(s); ol.appendChild(li);
    });
    box.appendChild(ol);
  }
  var plot = document.createElement("div"); plot.className = "rk__plot"; box.appendChild(plot);
  var foot = document.createElement("p"); foot.className = "lens-read rk__key";
  var none = data.all - rows.length;
  foot.innerHTML = '<span><i class="rk__k rk__k--c"></i>closes<i class="rk__k rk__k--o"></i>opens<i class="rk__k rk__k--w"></i>expected in these months<i class="rk__k rk__k--r"></i>open, rolling</span><span></span>';
  foot.lastChild.textContent = rows.length + " firms with something ahead" + (none > 0 ? " · " + none + " have announced nothing" : "");
  box.appendChild(foot);
  head.parentNode.insertBefore(box, head.nextSibling); document.querySelector("main").classList.add("has-ahead");

  function el(n, a, p) { var e = document.createElementNS(NS, n); for (var k in a) e.setAttribute(k, a[k]); if (p) p.appendChild(e); return e; }
  function draw() {
    var W = plot.clientWidth; if (!W) return;   // not shown on a phone
    plot.textContent = "";
    var NAME = W >= 1000 ? 130 : 0, L = NAME + Math.max.apply(null, rows.map(function (r) { return r.f.length; })) * 7.2 + 18, RH = 22, GAP = 12, TOP = 30, y = TOP, last = null, groups = 0;
    rows.forEach(function (r) { if (r.g !== last) { last = r.g; groups++; } });
    var H = TOP + rows.length * RH + (groups - 1) * GAP + 30, svg = el("svg", { width: W, height: H, viewBox: "0 0 " + W + " " + H, "aria-hidden": "true" }, plot);
    function X(t) { return L + (Math.max(x0, Math.min(x1, t)) - x0) / (x1 - x0) * (W - L); }
    function text(p, x, yy, s, cls, anchor) { var t = el("text", { x: x, y: yy, "class": cls, "text-anchor": anchor || "start" }, p); t.textContent = s; return t; }
    for (var m = 0; m < 8; m++) {
      var d = new Date(Date.UTC(now.getFullYear(), now.getMonth() + m, 1)), x = X(d.getTime());
      el("line", { x1: x, x2: x, y1: TOP - 10, y2: H - 24, "class": "rk-grid" }, svg);
      text(svg, x + 6, H - 6, MON[d.getUTCMonth()] + (m === 0 || d.getUTCMonth() === 0 ? " " + d.getUTCFullYear() : ""), "rk-mono");
    }
    var tx = X(today); last = null;
    rows.forEach(function (r, n) {
      if (r.g !== last) { if (last) y += GAP; last = r.g; if (NAME) text(svg, 0, y + 4, data.groups[r.g] || r.g, "rk-group"); }
      var g = el("g", { "class": "rk-row", style: "--i:" + n }, svg), taken = [];   // taken: the stretches of this row a label may not cross
      el("rect", { x: 0, y: y - RH / 2, width: W, height: RH, fill: "transparent" }, g);
      el("line", { x1: NAME, x2: W, y1: y + RH / 2, y2: y + RH / 2, "class": "rk-rule" }, g);
      text(g, NAME, y + 4, r.f, "rk-firm");
      var labels = [];
      function mark(xx) { taken.push([xx - 5, xx + 5]); }
      r.items.forEach(function (it) {
        var t = el("title", {}, null), node;
        if (it.k === "r") { node = el("line", { x1: L, x2: W, y1: y, y2: y, "class": "rk-roll" }, g); t.textContent = r.f + ", " + it.p + ": open, rolling"; node.appendChild(t); labels.push({ x: tx, s: "rolling", soft: true, side: true }); return; }
        if (it.k === "w") {
          var a = X(it.a), b = X(it.b); node = el("rect", { x: a, y: y - 4, width: Math.max(4, b - a), height: 8, "class": "rk-win" }, g);
          t.textContent = r.f + ", " + it.p + ": " + (it.x ? "expected, " : "") + it.t; node.appendChild(t); return;
        }
        var o = it.o, c = it.c;
        if (o != null && c != null) el("line", { x1: X(o), x2: X(c), y1: y, y2: y, "class": "rk-open" }, g);
        if (o != null && c == null) el("line", { x1: X(o), x2: W, y1: y, y2: y, "class": "rk-open rk-open--on" }, g);
        if (o != null && o >= x0) { node = el("circle", { cx: X(o), cy: y, r: 3.4, "class": "rk-o" }, g); t.textContent = r.f + ", " + it.p + ": opens " + day(o); node.appendChild(t); mark(X(o)); }
        if (o != null && o >= today) labels.push({ x: X(o), s: "opens " + day(o), soft: true });
        else if (o != null && c == null) labels.push({ x: tx, s: "open since " + day(o) + ", no closing date", soft: true, side: true });
        if (c != null) { node = el("circle", { cx: X(c), cy: y, r: 4, "class": "rk-c" }, g); var t2 = el("title", {}, node); t2.textContent = r.f + ", " + it.p + ": closes " + day(c); mark(X(c)); labels.push({ x: X(c), s: "closes " + day(c) }); }
      });
      // Each date in words on a black ground: right of its mark, in full or as the date alone; else left of it; else left out (the mark keeps its title).
      labels.sort(function (p, q) { return (p.side ? 1 : 0) - (q.side ? 1 : 0) || p.x - q.x; });
      labels.forEach(function (lb) {
        var short = lb.s.replace(/^(closes|opens) /, ""), tries = [[lb.s, 1], [short, 1], [lb.s, -1], [short, -1]], k, w, a, b;
        var others = taken.filter(function (q) { return !(q[0] < lb.x && lb.x < q[1]) || lb.side; });
        for (k = 0; k < tries.length; k++) {
          if (lb.side && k) break;
          w = tries[k][0].length * 7.7; a = tries[k][1] > 0 ? lb.x + 10 : lb.x - 10 - w; b = a + w;
          if (a < (tries[k][1] > 0 ? L : tx + 4) || b > W || !others.every(function (q) { return b < q[0] || a > q[1]; })) continue;
          el("rect", { x: a - 4, y: y - 7, width: w + 8, height: 14, "class": "rk-under" }, g);
          text(g, a, y + 4, tries[k][0], "rk-mono" + (lb.soft ? "" : " rk-ink")); taken.push([a - 4, b + 4]); break;
        }
      });
      [].forEach.call(g.querySelectorAll("circle"), function (c) { g.appendChild(c); });   // the marks over the labels' grounds
      y += RH;
    });
    el("rect", { x: L, y: TOP - 10, width: Math.max(0, tx - L), height: H - 24 - TOP + 10, "class": "rk-past" }, svg);
    el("line", { x1: tx, x2: tx, y1: 6, y2: H - 24, "class": "rk-today" }, svg);
    text(svg, tx + 6, 12, "Today, " + day(today), "rk-mono rk-ink");
  }
  draw();
  if ("ResizeObserver" in window) new ResizeObserver(draw).observe(plot); else window.addEventListener("resize", draw);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(draw);
})();
