// Andra Markets: theme, header state, menu, filters, reveals, signup, share.
(function () {
  var root = document.documentElement;
  root.classList.add("js");

  // Header turns solid once the hero has scrolled under it.
  var header = document.querySelector(".site-header");
  var hero = document.querySelector(".hero__sentinel");
  if (header && hero && "IntersectionObserver" in window) {
    new IntersectionObserver(
      function (entries) {
        header.classList.toggle("is-solid", !entries[0].isIntersecting);
      },
      { threshold: 0 }
    ).observe(hero);
  } else if (header) {
    header.classList.add("is-solid");
  }

  // Theme: light by default, the visitor's choice is remembered.
  var themeBtn = document.querySelector(".theme-btn");
  function syncThemeBtn() {
    var dark = root.getAttribute("data-theme") === "dark";
    themeBtn.setAttribute("aria-label", dark ? "Switch to light theme" : "Switch to dark theme");
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", dark ? "#0a0c0d" : "#f4f6f6");
  }
  if (themeBtn) {
    syncThemeBtn();
    themeBtn.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      var apply = function () {
        root.setAttribute("data-theme", next);
        syncThemeBtn();
      };
      try {
        localStorage.setItem("andra-theme", next);
      } catch (e) {}
      if (document.startViewTransition) document.startViewTransition(apply);
      else apply();
    });
  }

  // Dashboard filters.
  var chips = document.querySelectorAll(".chip");
  var tiles = document.querySelectorAll(".dash-tile");
  var filterStatus = document.querySelector(".filters__status");
  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      var cat = chip.getAttribute("data-filter");
      var shown = 0;
      chips.forEach(function (c) {
        c.setAttribute("aria-pressed", String(c === chip));
      });
      tiles.forEach(function (tile) {
        var match = cat === "all" || tile.getAttribute("data-cat") === cat;
        tile.hidden = !match;
        tile.classList.remove("is-entering");
        if (match) {
          shown++;
          tile.classList.add("is-in");
          void tile.offsetWidth;
          tile.classList.add("is-entering");
        }
      });
      filterStatus.textContent =
        cat === "all"
          ? "Showing all " + tiles.length + " dashboards"
          : "Showing " + shown + " of " + tiles.length + " dashboards: " + chip.getAttribute("data-label");
    });
  });

  // Mobile menu.
  var menuBtn = document.querySelector(".menu-btn");
  var nav = document.getElementById("site-nav");
  function setMenu(open) {
    header.classList.toggle("is-open", open);
    menuBtn.setAttribute("aria-expanded", String(open));
    menuBtn.querySelector("span").textContent = open ? "Close" : "Menu";
    menuBtn.querySelector("use").setAttribute("href", open ? "#i-x" : "#i-list");
    if (open) nav.querySelector("a").focus();
  }
  if (menuBtn && nav) {
    menuBtn.addEventListener("click", function () {
      setMenu(menuBtn.getAttribute("aria-expanded") !== "true");
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) setMenu(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && menuBtn.getAttribute("aria-expanded") === "true") {
        setMenu(false);
        menuBtn.focus();
      }
    });
  }

  // Reveal on enter, once.
  var targets = document.querySelectorAll(".reveal, .draw");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-in");
            io.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -12% 0px", threshold: 0.05 }
    );
    targets.forEach(function (el) {
      io.observe(el);
    });
  } else {
    targets.forEach(function (el) {
      el.classList.add("is-in");
    });
  }

  // Signup: front-end only until an email provider is connected.
  var form = document.querySelector(".signup form");
  if (form) {
    var input = form.querySelector("input");
    var status = form.querySelector(".field__status");
    var msg = form.querySelector(".field__msg");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var value = input.value.trim();
      var ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
      input.setAttribute("aria-invalid", String(!ok));
      status.classList.toggle("is-error", !ok);
      if (!ok) {
        msg.textContent = value
          ? "That email address looks incomplete. Check it and try again."
          : "Enter your email address to subscribe.";
        input.focus();
        return;
      }
      msg.textContent = "Subscribed. The next close note goes to " + value + ".";
      form.closest(".signup").classList.add("is-done");
    });
    input.addEventListener("input", function () {
      if (input.getAttribute("aria-invalid") === "true") {
        input.removeAttribute("aria-invalid");
        msg.textContent = "";
        status.classList.remove("is-error");
      }
    });
  }

  // Share a close note: the system share sheet where there is one, else copy
  // the link. Hidden without JS, since it cannot work without it.
  var share = document.querySelector(".report__share");
  if (share) {
    var shareBtn = share.querySelector("[data-share]");
    var shareMsg = share.querySelector(".report__share-status");
    var url = location.origin + location.pathname;
    var title = document.querySelector("h1").textContent;
    var say = function (text) {
      shareMsg.textContent = text;
    };
    share.hidden = false;
    shareBtn.addEventListener("click", function () {
      say("");
      if (navigator.share) {
        navigator.share({ title: title, url: url }).catch(function () {});
      } else if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(url).then(
          function () {
            say("Link copied.");
          },
          function () {
            say("Copy this link: " + url);
          }
        );
      } else {
        say("Copy this link: " + url);
      }
    });
  }
})();
