// Andra Markets calendar: week tabs, filters by type, region, earnings market and importance,
// and today's date in New York (the page is built ahead of time, so the day
// it marks as today is checked again here). Without JS every week shows.
(function () {
  var table = document.querySelector(".cl__table");
  if (!table) return;
  var groups = Array.prototype.slice.call(table.querySelectorAll(".cl__day-group"));
  var controls = document.querySelector(".cl__controls");
  var status = document.querySelector(".cl__status");
  var empty = document.querySelector(".cl__empty");
  var tabs = Array.prototype.slice.call(document.querySelectorAll(".cl__weeks .chip"));
  var state = { week: null, type: "all", region: "all", er: "all", imp: "all" };

  var today = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit"
  }).format(new Date());

  // Today, in New York.
  groups.forEach(function (g) {
    var th = g.querySelector(".cl__day th");
    var on = g.getAttribute("data-day") === today;
    g.classList.toggle("is-today", on);
    th.textContent = (on ? "Today, " : "") + th.getAttribute("data-label");
  });

  function weekOf(day) {
    var match = null;
    tabs.forEach(function (t) {
      var w = t.getAttribute("data-week");
      if (w <= day) match = w;
    });
    return match;
  }

  function press(chips, chip) {
    chips.forEach(function (c) {
      c.setAttribute("aria-pressed", String(c === chip));
    });
  }

  function apply() {
    var shown = 0;
    var total = 0;
    groups.forEach(function (g) {
      var inWeek = !state.week || g.getAttribute("data-week") === state.week;
      var n = 0;
      g.querySelectorAll(".cl__row").forEach(function (r) {
        var ok = (state.type === "all" || r.getAttribute("data-type") === state.type) &&
          (state.region === "all" || r.getAttribute("data-region") === state.region) &&
          // Earnings by market: only earnings rows answer to it.
          (state.er === "all" || !r.hasAttribute("data-er") || r.getAttribute("data-er") === state.er) &&
          (state.imp === "all" || r.getAttribute("data-imp") === state.imp);
        if (inWeek) total++;
        r.hidden = !(inWeek && ok);
        if (!r.hidden) n++;
      });
      shown += n;
      g.hidden = !inWeek || n === 0;
    });
    if (empty) empty.hidden = shown > 0;
    if (status) {
      var span = state.week ? " this week" : "";
      if (state.week && tabs.length && tabs[0].getAttribute("data-week") !== state.week) span = " that week";
      status.textContent = shown === total
        ? "Showing all " + total + " events" + span
        : "Showing " + shown + " of " + total + " events" + span;
    }
  }

  if (controls) {
    controls.hidden = false;
    var target = location.hash.match(/^#d-(\d{4}-\d{2}-\d{2})$/);
    var start = (target && weekOf(target[1])) || weekOf(today);
    if (tabs.length) {
      var first = tabs.filter(function (t) { return t.getAttribute("data-week") === start; })[0] || tabs[0];
      press(tabs, first);
      state.week = first.getAttribute("data-week");
      tabs.forEach(function (t) {
        t.addEventListener("click", function () {
          press(tabs, t);
          state.week = t.getAttribute("data-week");
          apply();
        });
      });
    }
    ["type", "region", "er", "imp"].forEach(function (key) {
      var chips = Array.prototype.slice.call(controls.querySelectorAll(".chip[data-" + key + "]"));
      chips.forEach(function (chip) {
        chip.addEventListener("click", function () {
          press(chips, chip);
          state[key] = chip.getAttribute("data-" + key);
          apply();
        });
      });
    });
  }
  apply();
  if (location.hash) {
    var el = document.getElementById(location.hash.slice(1));
    if (el && !el.hidden) el.scrollIntoView();
  }
})();
