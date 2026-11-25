// companies/go/?x=EXCHANGE&s=SYMBOL: where a company clicked in a Live Markets
// heatmap lands. TradingView names a company by exchange and symbol ("BME",
// "SAN"); the site's company pages are named by ticker ("SAN.MC", at
// companies/san-mc/). A company the site follows opens its page; any other US
// company opens its live profile; anything else opens the Companies index.
(function () {
  "use strict";
  var q = new URLSearchParams(location.search);
  var x = (q.get("x") || "").toUpperCase(), s = (q.get("s") || "").toUpperCase();
  var home = "../../", index = home + "companies/";
  // TradingView's exchange -> the suffix of the site's tickers. "" is a US listing.
  var SUFFIX = { NASDAQ: "", NYSE: "", AMEX: "", CBOE: "", BME: ".MC", XETR: ".DE", LSE: ".L", MIL: ".MI",
                 SIX: ".SW", EURONEXT: [".PA", ".AS", ".BR", ".LS"], OMXSTO: ".ST", OMXCOP: ".CO", OMXHEX: ".HE" };
  if (!/^[A-Z0-9._-]{1,12}$/.test(s) || !(x in SUFFIX)) { location.replace(index); return; }
  var us = SUFFIX[x] === "";
  // A US share class is "BRK.B" at TradingView and "BRK-B" on the site.
  var wanted = [].concat(SUFFIX[x]).map(function (suffix) { return (us ? s.replace(/\./g, "-") : s) + suffix; });
  var found = (window.ANDRA_SEARCH || []).filter(function (r) {
    return r.g === "Companies" && wanted.indexOf(String(r.m).toUpperCase()) >= 0;
  })[0];
  location.replace(found ? home + found.u : us ? index + "live/?t=" + encodeURIComponent(s) : index);
})();
