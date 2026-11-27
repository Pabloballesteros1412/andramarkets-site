/* Crypto: Prices (owner-approved sketch, 27 Nov 2026). Draws each coin's last seven days in its row (a single ink
   line on its own scale, a dot at its end) and switches the Moves heatmap between the coins without stablecoins and
   all of them. The figures are the page's own; without this script the page keeps its tables and Latest panel. */
(function () {
  "use strict";
  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  function spark(cv) {
    var s = (cv.getAttribute("data-sp") || "").split(",").map(Number).filter(function (v) { return v > 0; }); if (s.length < 2) return;
    var w = cv.clientWidth, h = cv.clientHeight; if (!w) return; cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
    var c = cv.getContext("2d"); c.setTransform(dpr, 0, 0, dpr, 0, 0); c.clearRect(0, 0, w, h);
    var lo = Math.min.apply(0, s), hi = Math.max.apply(0, s); if (hi - lo < hi * 1e-4) { lo -= hi * 1e-4; hi += hi * 1e-4; }
    function X(i) { return 1 + i / (s.length - 1) * (w - 6); } function Y(v) { return h - 3 - (v - lo) / (hi - lo) * (h - 6); }
    c.beginPath(); s.forEach(function (v, i) { i ? c.lineTo(X(i), Y(v)) : c.moveTo(X(i), Y(v)); }); c.strokeStyle = "rgba(242,243,243,.85)"; c.lineWidth = 1.1; c.stroke();
    c.fillStyle = "#f2f3f3"; c.beginPath(); c.arc(X(s.length - 1), Y(s[s.length - 1]), 2, 0, 7); c.fill();
  }
  var cvs = [].slice.call(document.querySelectorAll(".mk-sp canvas"));
  function all() { cvs.forEach(spark); }
  all(); if ("ResizeObserver" in window && cvs[0]) new ResizeObserver(all).observe(cvs[0].closest("table"));
  var box = document.querySelector(".mk-moves"); if (!box) return;
  var ctl = box.querySelector(".dd__ctl"), views = [].slice.call(box.querySelectorAll("[data-view]")); if (!ctl || views.length < 2) return;
  ctl.hidden = false;
  ctl.addEventListener("click", function (e) { var b = e.target.closest("button[data-show]"); if (!b) return; var v = b.getAttribute("data-show");
    [].forEach.call(ctl.querySelectorAll("button"), function (x) { x.setAttribute("aria-pressed", String(x === b)); });
    views.forEach(function (el) { el.hidden = el.getAttribute("data-view") !== v; }); });
})();
