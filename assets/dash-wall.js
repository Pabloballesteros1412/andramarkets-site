/* Dashboards: the nine tiles as a wall of screens (owner, 24 Nov 2026). Over the first screen the dashboards hang
   in a curved wall, like a control room seen from its middle: each screen is a tile's own title, reading and
   chart (cloned from the list below, so the figures are the page's own), marked by four corners of light rather
   than a box. The wall leans with the pointer; the screen pointed at comes forward and the rest dim; a press
   opens that dashboard. Wide screens only: on a phone the list of tiles is the page. */
(function () {
  "use strict";
  var grid = document.querySelector(".dash-index .dash-grid"), head = document.querySelector(".page__head"); if (!grid || !head) return;
  if (!window.matchMedia("(min-width: 900px)").matches) return;
  var tiles = [].filter.call(grid.querySelectorAll(".dash-tile"), function (t) { return t.querySelector(".dash-tile__chart svg"); }); if (tiles.length < 6) return;
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var wall = document.createElement("div"); wall.className = "dash-wall"; var stage = document.createElement("div"); stage.className = "dash-wall__stage"; wall.appendChild(stage);
  var cols = 3, rows = Math.ceil(tiles.length / cols);
  tiles.slice(0, 9).forEach(function (t, i) {
    var a = t.querySelector("a"), h = t.querySelector("h3"), fig = t.querySelector(".dash-tile__fig"), svg = t.querySelector(".dash-tile__chart svg").cloneNode(true);
    svg.removeAttribute("role"); svg.removeAttribute("aria-label"); svg.setAttribute("aria-hidden", "true"); [].forEach.call(svg.querySelectorAll("[id]"), function (n) { n.removeAttribute("id"); });
    var s = document.createElement("a"); s.className = "dash-wall__screen"; s.href = a.getAttribute("href"); s.setAttribute("aria-label", h.textContent + (fig ? ": " + fig.textContent : ""));
    var c = i % cols - (cols - 1) / 2, r = Math.floor(i / cols) - (rows - 1) / 2;   // where it hangs: the wall curves round the viewer
    s.style.setProperty("--c", c); s.style.setProperty("--r", r); s.style.setProperty("--d", (i * 0.37 % 1).toFixed(2));
    s.innerHTML = '<span class="dash-wall__name"></span><span class="dash-wall__fig"></span><span class="dash-wall__chart"></span><i></i><i></i><i></i><i></i>';
    s.children[0].textContent = h.textContent; if (fig) s.children[1].innerHTML = fig.innerHTML; s.children[2].appendChild(svg); stage.appendChild(s); });
  var down = document.createElement("a"); down.className = "lib-map__down"; down.href = "#dash-all"; down.textContent = "All dashboards"; wall.appendChild(down);
  var sec = document.querySelector(".dash-index"); if (sec && !sec.id) sec.id = "dash-all";
  head.appendChild(wall); document.querySelector("main").classList.add("has-wall");
  function fit() { var b = wall.getBoundingClientRect(), t = head.querySelector(".page__title").getBoundingClientRect(), top = t.bottom - b.top + 24, room = b.height - top - 64; // under the title, over the link at the foot
    var k = Math.min(1, room / 800, b.width / 1640); stage.style.setProperty("--k", k.toFixed(3)); stage.style.top = (top + room / 2) + "px"; }
  fit(); window.addEventListener("resize", fit); if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
  if (still) return;
  var tx = 0, ty = 0, x = 0, y = 0, run = 0;
  function step() { x += (tx - x) * 0.07; y += (ty - y) * 0.07; stage.style.setProperty("--px", x.toFixed(4)); stage.style.setProperty("--py", y.toFixed(4)); run = Math.abs(tx - x) + Math.abs(ty - y) > 0.001 ? requestAnimationFrame(step) : 0; }
  wall.addEventListener("pointermove", function (e) { var b = wall.getBoundingClientRect(); tx = (e.clientX - b.left) / b.width - 0.5; ty = (e.clientY - b.top) / b.height - 0.5; if (!run) run = requestAnimationFrame(step); });
  wall.addEventListener("pointerleave", function () { tx = ty = 0; if (!run) run = requestAnimationFrame(step); });
})();
