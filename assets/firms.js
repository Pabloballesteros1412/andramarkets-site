// Firms (firms/): the type and division chips, and "Closes in n days" from today's
// New York date, as on the Recruiting calendar. Without JavaScript every firm and
// programme shows and the chips stay hidden.
(function () {
  "use strict";
  var today = new Date(new Date().toLocaleString("en-US", { timeZone: "America/New_York" }));
  today = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
  document.querySelectorAll("[data-close]").forEach(function (el) {
    var days = Math.round((Date.parse(el.getAttribute("data-close")) - today) / 864e5);
    if (days >= 0 && days <= 14) el.textContent = days === 0 ? "Closes today" : "Closes in " + days + " day" + (days > 1 ? "s" : "");
    else if (days < 0) el.textContent = "Closed";
  });

  var ctl = document.querySelector(".fm-ctl");
  if (!ctl) return;
  ctl.hidden = false;
  var firms = Array.prototype.slice.call(document.querySelectorAll(".fm-firm"));
  var status = document.querySelector(".fm-status");
  var empty = document.querySelector(".fm-empty");
  var f = { group: "all", div: "all" };
  var label = { group: "", div: "" };

  function apply() {
    var shown = 0, progs = 0, total = 0;
    firms.forEach(function (el) {
      var typeOk = f.group === "all" || el.getAttribute("data-group") === f.group;
      var any = 0;
      el.querySelectorAll(".fm-prog").forEach(function (p) {
        total++;
        var on = typeOk && (f.div === "all" || (" " + p.getAttribute("data-div") + " ").indexOf(" " + f.div + " ") > -1);
        p.hidden = !on;
        if (on) any++;
      });
      el.hidden = !any;
      if (any) { shown++; progs += any; }
    });
    empty.hidden = shown > 0;
    var what = [label.group, f.div === "all" ? "" : label.div + " programmes"].filter(Boolean).join(", ");
    status.textContent = f.group === "all" && f.div === "all"
      ? "Showing all " + firms.length + " firms and " + total + " programmes"
      : "Showing " + shown + " of " + firms.length + " firms, " + progs + " programme" + (progs === 1 ? "" : "s") + ": " + what;
  }

  ["group", "div"].forEach(function (k) {
    var bs = Array.prototype.slice.call(ctl.querySelectorAll("button[data-" + k + "]"));
    bs.forEach(function (b) {
      b.addEventListener("click", function () {
        bs.forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        f[k] = b.getAttribute("data-" + k);
        label[k] = f[k] === "all" ? "" : b.getAttribute("data-label");
        apply();
      });
    });
  });
  apply();
})();
