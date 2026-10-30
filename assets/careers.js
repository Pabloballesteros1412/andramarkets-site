// Break into Wall Street (break-into-wall-street/): the cold email
// templates, one at a time, with a copy button. Without JavaScript every
// template shows.
(function () {
  "use strict";
  var bodies = document.querySelectorAll("[data-tpl-body]");
  if (!bodies.length) return;
  bodies.forEach(function (x, i) { x.hidden = i > 0; });
  var cur = bodies[0];
  document.querySelectorAll("[data-tpl]").forEach(function (b) {
    b.addEventListener("click", function () {
      document.querySelectorAll("[data-tpl]").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      bodies.forEach(function (x) {
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
