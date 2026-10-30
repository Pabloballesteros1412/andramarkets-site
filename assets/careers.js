// Break into Wall Street (break-into-wall-street/): the recruiting timeline (region, then year;
// bars by month, September to August) and the cold email templates. Without
// JavaScript the timeline is a list and every template shows.
(function () {
  "use strict";
  var T = JSON.parse(document.getElementById("pw-data").textContent);
  var MONTHS = ["Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"];
  var KIND = {};
  T.kinds.forEach(function (k) { KIND[k.id] = k.name; });
  var tl = document.getElementById("pw-tl");
  var yearsEl = document.getElementById("pw-years");
  var detail = document.getElementById("pw-detail");
  var region = T.regions[0], year = "all", focus = null;
  var nowCol = (new Date().getMonth() + 4) % 12; // September is column 0

  function span(it) {
    return it.from === it.to ? MONTHS[it.from] : it.from === 0 && it.to === 11 ? "All year" : MONTHS[it.from] + " to " + MONTHS[it.to];
  }

  function drawYears() {
    // Keep the glide fill site.js put in the group; replace only the chips.
    yearsEl.querySelectorAll(".chip").forEach(function (c) { c.remove(); });
    yearsEl.insertAdjacentHTML("beforeend", [{ id: "all", name: "All years" }].concat(region.years).map(function (y) {
      return '<button type="button" class="chip" data-year="' + y.id + '" aria-pressed="' + (y.id === year) + '">' + y.name + "</button>";
    }).join(""));
    yearsEl.querySelectorAll("[data-year]").forEach(function (b) {
      b.addEventListener("click", function () {
        year = b.getAttribute("data-year");
        focus = null;
        yearsEl.querySelectorAll("[data-year]").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        draw();
      });
    });
  }

  function draw() {
    var head = '<div class="pw-tl__row pw-tl__head"><span class="pw-tl__y"></span><div class="pw-tl__m">'
      + MONTHS.map(function (m, i) { return "<span" + (i === nowCol ? ' class="is-now"' : "") + ">" + m + "</span>"; }).join("") + "</div></div>";
    var rows = region.years.map(function (y) {
      var items = region.items.filter(function (it) { return it.year === y.id; });
      // lanes: an item goes in the first lane where it does not overlap
      var lanes = [];
      items.forEach(function (it) {
        var l = 0;
        while (lanes[l] && lanes[l].some(function (o) { return !(it.to < o.from || it.from > o.to); })) l++;
        (lanes[l] = lanes[l] || []).push(it);
        it._lane = l;
      });
      var bars = items.map(function (it) {
        var idx = region.items.indexOf(it);
        return '<button type="button" class="pw-bar pw-bar--' + it.kind + (focus === idx ? " is-focus" : "") + '" data-i="' + idx + '" style="grid-column:'
          + (it.from + 1) + " / " + (it.to + 2) + ";grid-row:" + (it._lane + 1) + '" aria-label="' + y.name + ", " + span(it) + ": " + it.title + " (" + KIND[it.kind] + ')"><span>' + it.title + "</span></button>";
      }).join("");
      var dim = year !== "all" && year !== y.id ? " is-dim" : "";
      return '<div class="pw-tl__row' + dim + '"><span class="pw-tl__y">' + y.name + '</span><div class="pw-tl__bars" style="grid-template-rows:repeat(' + Math.max(1, lanes.length) + ',auto)">'
        + '<i class="pw-tl__now" style="grid-column:' + (nowCol + 1) + '" aria-hidden="true"></i>' + bars + "</div></div>";
    }).join("");
    tl.innerHTML = '<div class="pw-tl__inner">' + head + rows + "</div>";
    tl.querySelectorAll(".pw-bar").forEach(function (b) {
      b.addEventListener("click", function () {
        var i = +b.getAttribute("data-i");
        focus = i;
        year = region.items[i].year;
        drawYears();
        draw();
        var f = detail.querySelector(".is-focus");
        if (f && f.scrollIntoView && window.innerWidth < 960) f.scrollIntoView({ block: "nearest", behavior: "smooth" });
      });
    });
    var list = region.items.map(function (it, i) { return [it, i]; }).filter(function (p) { return year === "all" || p[0].year === year; });
    var yname = {};
    region.years.forEach(function (y) { yname[y.id] = y.name; });
    detail.innerHTML = '<ol class="pw-steps">' + list.map(function (p) {
      var it = p[0];
      return '<li class="' + (p[1] === focus ? "is-focus" : "") + '"><span class="pw-steps__when">' + (year === "all" ? yname[it.year] + ", " : "") + span(it)
        + '</span><span class="pw-steps__kind"><i class="pw-sw pw-sw--' + it.kind + '"></i>' + KIND[it.kind] + '</span><b>' + it.title + "</b><p>" + it.detail + "</p></li>";
    }).join("") + "</ol>";
  }

  document.querySelectorAll("[data-region]").forEach(function (b) {
    b.addEventListener("click", function () {
      document.querySelectorAll("[data-region]").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      region = T.regions.filter(function (r) { return r.id === b.getAttribute("data-region"); })[0];
      year = "all";
      focus = null;
      drawYears();
      draw();
    });
  });
  drawYears();
  draw();

  // Templates: one at a time.
  var bodies = document.querySelectorAll("[data-tpl-body]");
  bodies.forEach(function (x, i) { x.hidden = i > 0; });
  var cur = bodies[0];
  document.querySelectorAll("[data-tpl]").forEach(function (b) {
    b.addEventListener("click", function () {
      document.querySelectorAll("[data-tpl]").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      document.querySelectorAll("[data-tpl-body]").forEach(function (x) {
        x.hidden = x.getAttribute("data-tpl-body") !== b.getAttribute("data-tpl");
        if (!x.hidden) cur = x;
      });
    });
  });
  var st = document.querySelector(".pw-copy__st");
  document.querySelector(".pw-copy").addEventListener("click", function () {
    var text = "Subject: " + cur.querySelector(".pw-tpl__subj").textContent.replace(/^Subject\s*/, "") + "\n\n" + cur.querySelector("pre").textContent;
    (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject()).then(function () {
      st.textContent = "Copied. Replace every [bracket] before sending.";
    }, function () {
      st.textContent = "Select the text and copy it.";
    });
  });
})();
