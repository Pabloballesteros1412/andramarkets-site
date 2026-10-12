// Andra Markets prototypes: header state, mobile menu, reveals, signup states.
(function () {
  var root = document.documentElement;
  root.classList.add("js");

  // Header turns solid once the hero has scrolled under it.
  var header = document.querySelector(".site-header");
  var hero = document.querySelector(".hero");
  if (header && hero && "IntersectionObserver" in window) {
    new IntersectionObserver(
      function (entries) {
        header.classList.toggle("is-solid", !entries[0].isIntersecting);
      },
      { rootMargin: "-64px 0px 0px 0px", threshold: 0 }
    ).observe(hero);
  }

  // Mobile menu.
  var menuBtn = document.querySelector(".menu-btn");
  var nav = document.getElementById("site-nav");
  function setMenu(open) {
    header.classList.toggle("is-open", open);
    menuBtn.setAttribute("aria-expanded", String(open));
    menuBtn.querySelector("span").textContent = open ? "Close" : "Menu";
    menuBtn.querySelector("use").setAttribute("href", open ? "#i-x" : "#i-list");
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

  // Signup: prototype only, nothing is sent.
  var form = document.querySelector(".signup form");
  if (form) {
    var input = form.querySelector("input");
    var status = form.querySelector(".field__status");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var value = input.value.trim();
      var ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
      input.setAttribute("aria-invalid", String(!ok));
      status.classList.toggle("is-error", !ok);
      if (!ok) {
        status.textContent = value
          ? "That email address looks incomplete. Check it and try again."
          : "Enter your email address to subscribe.";
        input.focus();
        return;
      }
      status.textContent = "Subscribed. The next close note goes to " + value + ".";
      form.closest(".signup").classList.add("is-done");
    });
    input.addEventListener("input", function () {
      if (input.getAttribute("aria-invalid") === "true") {
        input.removeAttribute("aria-invalid");
        status.textContent = "";
        status.classList.remove("is-error");
      }
    });
  }
})();
