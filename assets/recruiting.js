// Recruiting calendar (recruiting-calendar/): view
// (by date or by firm), month tabs and filters, and "Closes in n days" from
// today's New York date. Without JavaScript both views show in full.
(function () {
  "use strict";
  var ctl = document.querySelector(".rc-ctl");
  var today = new Date(new Date().toLocaleString("en-US", { timeZone: "America/New_York" }));
  today = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
  document.querySelectorAll("[data-close]").forEach(function (el) {
    var days = Math.round((Date.parse(el.getAttribute("data-close")) - today) / 864e5);
    if (days >= 0 && days <= 14) el.textContent = days === 0 ? "Closes today" : "Closes in " + days + " day" + (days > 1 ? "s" : "");
    else if (days < 0) el.textContent = "Closed";
  });
  if (!ctl) return;
  ctl.hidden = false;
  var f = { view: "date", month: null, kind: "all", group: "all", div: "all", status: "all" };
  var first = document.querySelector("[data-month]");
  if (first) f.month = first.getAttribute("data-month");
  var status = document.querySelector(".rc-status");
  function match(r) {
    return (f.kind === "all" || r.dataset.kind === f.kind) && (f.group === "all" || r.dataset.group === f.group)
      && (f.div === "all" || (" " + r.dataset.div + " ").indexOf(" " + f.div + " ") > -1)
      && (f.status === "all" || r.dataset.status === f.status);
  }
  function apply() {
    var byDate = document.querySelector(".rc-bydate");
    if (byDate) byDate.hidden = f.view !== "date";
    document.querySelector(".rc-byfirm").hidden = f.view !== "firm";
    document.querySelector(".rc-months").hidden = f.view !== "date";
    var n = 0, label = "";
    if (f.view === "date") {
      document.querySelectorAll(".rc-bydate tbody").forEach(function (tb) {
        var on = tb.getAttribute("data-month") === f.month, any = 0;
        tb.querySelectorAll(".rc-row").forEach(function (r) { var m = on && match(r); r.hidden = !m; if (m) any++; });
        tb.hidden = !on || !any;
        n += any;
      });
      var tab = document.querySelector('[data-month="' + f.month + '"]');
      label = tab ? (f.month === "now" ? " open now" : " in " + tab.textContent) : "";
      if (byDate) byDate.querySelector(".cl__empty").hidden = n > 0;
      status.textContent = "Showing " + n + " date" + (n === 1 ? "" : "s") + label;
    } else {
      document.querySelectorAll(".rc-byfirm .rc-row").forEach(function (r) { var m = match(r); r.hidden = !m; if (m) n++; });
      status.textContent = "Showing " + n + " programme" + (n === 1 ? "" : "s");
    }
  }
  ["view", "month", "kind", "group", "div", "status"].forEach(function (k) {
    var bs = Array.prototype.slice.call(document.querySelectorAll("[data-" + k + "]")).filter(function (b) { return b.tagName === "BUTTON"; });
    bs.forEach(function (b) {
      b.addEventListener("click", function () {
        bs.forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        f[k] = b.getAttribute("data-" + k);
        apply();
      });
    });
  });
  apply();
})();
