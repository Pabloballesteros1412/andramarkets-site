/* Chart of the day (chart-of-the-day/): "Share this chart", the close note's share
   button (assets/site.js) with one difference: it always shares the session's own
   page, so a link shared from chart-of-the-day/ keeps showing that day's chart once
   newer ones arrive. The system share sheet where there is one, else the link is
   copied and the label swaps to "Link copied"; if copying fails the link shows to
   copy by hand. Hidden without JS, since it cannot work without it. */
(function () {
  "use strict";
  var box = document.querySelector(".cotd__share");
  if (!box) return;
  var btn = box.querySelector("[data-cotd-share]");
  var swap = btn.querySelector(".swap");
  var msg = box.querySelector(".report__share-status");
  var url = new URL(box.getAttribute("data-url"), location.href).href;
  var title = box.getAttribute("data-title") || document.title;
  var timer;
  function say(text, quiet) {
    msg.textContent = text;
    msg.classList.toggle("visually-hidden", !!quiet);
  }
  function copied() {
    say("Link copied.", true);
    swap.classList.add("is-on");
    clearTimeout(timer);
    timer = setTimeout(function () {
      swap.classList.remove("is-on");
      say("");
    }, 2400);
  }
  box.hidden = false;
  btn.addEventListener("click", function () {
    say("");
    if (navigator.share) {
      navigator.share({ title: title, url: url }).catch(function () {});
    } else if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(url).then(copied, function () {
        say("Copy this link: " + url);
      });
    } else {
      say("Copy this link: " + url);
    }
  });
})();
