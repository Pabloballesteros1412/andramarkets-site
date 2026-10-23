// Watch page: TikTok's official creator embed. Its script (tiktok.com/embed.js)
// loads only once the feed nears the viewport, so nothing is fetched from
// TikTok before the visitor reaches the videos. See tools/build_site.py, watch_page().
(function () {
  var feed = document.querySelector(".wfeed");
  if (!feed) return;
  var status = feed.querySelector(".wfeed__status");
  var loaded = false;
  function load() {
    if (loaded) return;
    loaded = true;
    var s = document.createElement("script");
    s.src = "https://www.tiktok.com/embed.js";
    s.async = true;
    s.onerror = function () {
      feed.classList.add("is-failed");
      if (status) status.textContent = "TikTok did not load. The videos are on the TikTok profile linked below.";
    };
    s.onload = function () {
      if (status) status.textContent = "";
    };
    document.body.appendChild(s);
  }
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      if (entries[0].isIntersecting) {
        io.disconnect();
        load();
      }
    }, { rootMargin: "400px 0px" });
    io.observe(feed);
  } else {
    load();
  }
})();
