/* The space behind every page, in three depths (owner, 13 Nov 2026): the cloud far off, then
   two fields of stars. They slide a little against each other with the pointer and as the
   page scrolls, so the ground has depth. Not under reduced motion: theme.css and home.css then
   keep the still picture. Loaded by every page, the homepage included. */
(function () {
  if (!window.matchMedia || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (!document.body || !window.requestAnimationFrame) return;
  var box = document.createElement("div");
  box.className = "space";
  box.setAttribute("aria-hidden", "true");
  box.innerHTML = '<i class="space__cloud"></i><i class="space__far"></i><i class="space__near"></i>';
  document.body.insertBefore(box, document.body.firstChild);
  document.documentElement.classList.add("has-space");
  var cloud = box.children[0], far = box.children[1], near = box.children[2];
  var px = 0, py = 0, tx = 0, ty = 0, queued = false;

  function tileOf(el, name) {
    return parseFloat(getComputedStyle(box).getPropertyValue(name)) || 1000;
  }
  var tFar = tileOf(far, "--t-far"), tNear = tileOf(near, "--t-near");

  function wrap(v, t) { return ((v % t) + t) % t; }

  function draw() {
    queued = false;
    px += (tx - px) * 0.06;
    py += (ty - py) * 0.06;
    var sy = window.scrollY || 0;
    cloud.style.transform = "translate3d(" + (-px * 12).toFixed(2) + "px," + (-py * 10 - Math.min(sy * 0.02, 40)).toFixed(2) + "px,0)";
    far.style.transform = "translate3d(" + (-px * 24).toFixed(2) + "px," + wrap(-py * 18 - sy * 0.05, tFar).toFixed(2) + "px,0)";
    near.style.transform = "translate3d(" + (-px * 46).toFixed(2) + "px," + wrap(-py * 34 - sy * 0.11, tNear).toFixed(2) + "px,0)";
    if (Math.abs(tx - px) > 0.001 || Math.abs(ty - py) > 0.001) ask();
  }
  function ask() {
    if (!queued) { queued = true; requestAnimationFrame(draw); }
  }
  window.addEventListener("pointermove", function (e) {
    if (e.pointerType === "touch") return;
    tx = e.clientX / window.innerWidth * 2 - 1;
    ty = e.clientY / window.innerHeight * 2 - 1;
    ask();
  }, { passive: true });
  window.addEventListener("scroll", ask, { passive: true });
  window.addEventListener("resize", function () {
    tFar = tileOf(far, "--t-far"); tNear = tileOf(near, "--t-near"); ask();
  });
  draw();
})();
