/* Andra Markets profile API: the proxy behind /profile/.

   A Cloudflare Worker between the static site and two data vendors, so their
   keys stay here (Worker secrets FINNHUB_API_KEY and FMP_API_KEY) and never
   reach the browser. Every answer is cut down to the fields the page draws
   and cached at the edge: fundamentals, peers, analysts and search for 24
   hours, news for 15 minutes, the price for 60 seconds. With the optional KV
   namespace STALE bound, the last good answer for each request is kept, and
   served (marked stale, with its date) when a vendor fails or the free
   plan's quota runs out.

   Routes (GET, JSON; an /api prefix is accepted too):
     /search?q=apple      Finnhub symbol search, US common stock only
     /quote?t=AAPL        Finnhub quote
     /news?t=AAPL         Finnhub company news, last 7 days
     /analysts?t=AAPL     Finnhub recommendation trends
     /peers?t=AAPL        Finnhub peers, each with its profile and metrics
     /fundamentals?t=AAPL FMP profile, statements and ratios (up to 10
                          years) with the company's Finnhub metrics

   Errors are JSON { error: { code, message, retryAfter? } } with code
   bad_request, not_found, busy (rate limit: retry later), plan (not in the
   vendor plan), upstream (vendor down) or config (a secret is missing). */

const FINNHUB = "https://finnhub.io/api/v1";
const FMP = "https://financialmodelingprep.com/stable";
const TTL = { search: 86400, quote: 60, news: 900, analysts: 86400, peers: 86400, fundamentals: 86400 };
const TICKER = /^[A-Z][A-Z0-9.-]{0,9}$/;
const MAX_PEERS = 5;

export default {
  async fetch(request, env, ctx) {
    const origin = request.headers.get("Origin") || "";
    const cors = corsHeaders(origin, env);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    if (request.method !== "GET") return json({ error: { code: "bad_request", message: "GET only." } }, 405, cors);
    // Browsers send Origin on every cross-site fetch: only the site's own pages are served.
    if (!cors["Access-Control-Allow-Origin"] && !(env.ALLOW_NO_ORIGIN === "1" && !origin)) {
      return json({ error: { code: "bad_request", message: "Origin not allowed." } }, 403, {});
    }
    const url = new URL(request.url);
    const route = url.pathname.replace(/^\/api/, "").replace(/\/+$/, "") || "/";
    const handler = ROUTES[route];
    if (!handler) return json({ error: { code: "not_found", message: "No such route." } }, 404, cors);

    let arg;
    try {
      arg = route === "/search" ? cleanQuery(url.searchParams.get("q")) : cleanTicker(url.searchParams.get("t"));
    } catch (e) {
      return json({ error: { code: "bad_request", message: e.message } }, 400, cors);
    }
    if (env.LIMITER) {
      const ip = request.headers.get("CF-Connecting-IP") || "anon";
      const { success } = await env.LIMITER.limit({ key: ip });
      if (!success) return json({ error: { code: "busy", message: "Too many requests. Try again in a minute.", retryAfter: 60 } }, 429, { ...cors, "Retry-After": "60" });
    }

    const name = route.slice(1);
    const key = `${name}:${arg}`;
    const cache = typeof caches !== "undefined" ? caches.default : null;
    const cacheReq = new Request(`https://profile-api.cache/${name}?k=${encodeURIComponent(arg)}`);
    if (cache) {
      const hit = await cache.match(cacheReq);
      if (hit) return withHeaders(hit, { ...cors, "X-Cache": "HIT" });
    }

    try {
      const data = await handler(arg, env);
      const body = JSON.stringify({ ...data, asOf: new Date().toISOString() });
      const res = new Response(body, {
        status: 200,
        headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": `public, max-age=${Math.min(TTL[name], 300)}, s-maxage=${TTL[name]}` },
      });
      if (cache) ctx.waitUntil(cache.put(cacheReq, res.clone()));
      if (env.STALE) ctx.waitUntil(env.STALE.put(key, body));
      return withHeaders(res, { ...cors, "X-Cache": "MISS" });
    } catch (e) {
      const err = e instanceof ApiError ? e : new ApiError(502, "upstream", "The data source did not answer.");
      // A vendor failure (not a bad ticker) falls back to the last good answer.
      if (env.STALE && err.code !== "not_found" && err.code !== "bad_request") {
        const old = await env.STALE.get(key);
        if (old) {
          return new Response(old.replace(/^\{/, `{"stale":true,"staleReason":${JSON.stringify(err.code)},`), {
            status: 200, headers: { ...cors, "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", "X-Cache": "STALE" },
          });
        }
      }
      const extra = err.retryAfter ? { "Retry-After": String(err.retryAfter) } : {};
      return json({ error: { code: err.code, message: err.message, ...(err.retryAfter ? { retryAfter: err.retryAfter } : {}) } }, err.status, { ...cors, ...extra, "Cache-Control": "no-store" });
    }
  },
};

const ROUTES = {
  "/search": search,
  "/quote": quote,
  "/news": news,
  "/analysts": analysts,
  "/peers": peers,
  "/fundamentals": fundamentals,
};

/* ---- Routes ---- */

async function search(q, env) {
  const d = await finnhub("/search", { q, exchange: "US" }, env);
  const seen = new Set();
  const results = (d.result || [])
    .filter((r) => r.type === "Common Stock" && TICKER.test(r.symbol || "") && !r.symbol.includes("."))
    .filter((r) => !seen.has(r.symbol) && seen.add(r.symbol))
    .slice(0, 8)
    .map((r) => ({ t: r.symbol, name: titleCase(r.description || r.symbol) }));
  return { q, results };
}

async function quote(t, env) {
  const d = await finnhub("/quote", { symbol: t }, env);
  // Finnhub answers an unknown symbol with zeros rather than an error.
  if (!d || !num(d.c) || !d.t) throw new ApiError(404, "not_found", `No US-listed company trades as ${t}.`);
  return { t, price: d.c, change: num(d.d), changePct: num(d.dp), prevClose: num(d.pc), time: d.t };
}

async function news(t, env) {
  const to = new Date();
  const from = new Date(to.getTime() - 7 * 864e5);
  const d = await finnhub("/company-news", { symbol: t, from: ymd(from), to: ymd(to) }, env);
  const seen = new Set();
  const items = (Array.isArray(d) ? d : [])
    .filter((n) => n.headline && /^https?:\/\//.test(n.url || ""))
    .filter((n) => !seen.has(n.headline) && seen.add(n.headline))
    .sort((a, b) => b.datetime - a.datetime)
    .slice(0, 8)
    .map((n) => ({ title: n.headline, source: n.source || "", url: n.url, time: n.datetime }));
  return { t, items };
}

async function analysts(t, env) {
  const d = await finnhub("/stock/recommendation", { symbol: t }, env);
  const rows = (Array.isArray(d) ? d : []).sort((a, b) => (a.period < b.period ? 1 : -1)).slice(0, 4)
    .map((r) => ({ period: r.period, strongBuy: r.strongBuy || 0, buy: r.buy || 0, hold: r.hold || 0, sell: r.sell || 0, strongSell: r.strongSell || 0 }));
  return { t, months: rows };
}

async function peers(t, env) {
  const list = await finnhub("/stock/peers", { symbol: t }, env);
  const others = (Array.isArray(list) ? list : []).filter((p) => p !== t && TICKER.test(p) && !p.includes(".")).slice(0, MAX_PEERS);
  const rows = await Promise.all([t, ...others].map(async (p) => {
    try {
      const [prof, met] = await Promise.all([finnhub("/stock/profile2", { symbol: p }, env), finnhub("/stock/metric", { symbol: p, metric: "all" }, env)]);
      return { t: p, name: prof && prof.name ? prof.name : p, ...peerMetrics(met && met.metric) };
    } catch (e) {
      if (e instanceof ApiError && e.code === "busy") throw e;
      return null;
    }
  }));
  return { t, peers: rows.filter(Boolean) };
}

async function fundamentals(t, env) {
  const fmpCall = (path, extra) => fmp(path, { symbol: t, ...extra }, env).catch((e) => e);
  const [profile, income, balance, cash, ratios, metric] = await Promise.all([
    fmpCall("/profile"),
    fmpCall("/income-statement", { period: "annual", limit: 10 }),
    fmpCall("/balance-sheet-statement", { period: "annual", limit: 10 }),
    fmpCall("/cash-flow-statement", { period: "annual", limit: 10 }),
    fmpCall("/ratios", { period: "annual", limit: 10 }),
    finnhub("/stock/metric", { symbol: t, metric: "all" }, env).catch((e) => e),
  ]);
  const p = Array.isArray(profile) ? profile[0] : null;
  if (!p) {
    // No profile: a bad ticker, or the vendor failed. Pass the vendor's error on.
    if (profile instanceof ApiError && profile.code !== "not_found") throw profile;
    throw new ApiError(404, "not_found", `No US-listed company trades as ${t}.`);
  }
  const years = mergeYears(list(income), list(balance), list(cash), list(ratios));
  const missing = [["income", income], ["balance", balance], ["cash", cash], ["ratios", ratios], ["metrics", metric]]
    .filter(([, v]) => v instanceof Error || (Array.isArray(v) && !v.length)).map(([k]) => k);
  return {
    t,
    profile: {
      name: p.companyName || t,
      exchange: p.exchange || p.exchangeShortName || "",
      currency: p.currency || "USD",
      sector: p.sector || "",
      industry: p.industry || "",
      ceo: p.ceo || "",
      employees: num(p.fullTimeEmployees),
      city: [p.city, p.state].filter(Boolean).map(titleCase).join(", "),
      ipoDate: p.ipoDate || "",
      website: /^https?:\/\//.test(p.website || "") ? p.website : "",
      description: firstSentences(p.description || "", 3),
      marketCap: num(p.marketCap ?? p.mktCap),
      beta: num(p.beta),
      lastDividend: num(p.lastDividend ?? p.lastDiv),
    },
    metrics: metric instanceof Error ? null : selfMetrics(metric && metric.metric),
    years,
    missing,
  };
}

/* ---- Shaping ---- */

function list(v) {
  return Array.isArray(v) ? v : [];
}

// One row per fiscal year, oldest first, joining the statements on the year.
function mergeYears(income, balance, cash, ratios) {
  const fy = (r) => String(r.fiscalYear || r.calendarYear || (r.date || "").slice(0, 4));
  const by = (rows) => Object.fromEntries(rows.map((r) => [fy(r), r]));
  const B = by(balance), C = by(cash), R = by(ratios);
  return income.map((i) => {
    const y = fy(i), b = B[y] || {}, c = C[y] || {}, r = R[y] || {};
    return {
      fy: y,
      end: i.date || "",
      revenue: num(i.revenue),
      grossProfit: num(i.grossProfit),
      operatingIncome: num(i.operatingIncome),
      netIncome: num(i.netIncome),
      ebitda: num(i.ebitda),
      eps: num(i.epsDiluted ?? i.epsdiluted),
      cash: num(b.cashAndShortTermInvestments ?? b.cashAndCashEquivalents),
      debt: num(b.totalDebt),
      netDebt: num(b.netDebt),
      equity: num(b.totalStockholdersEquity),
      assets: num(b.totalAssets),
      operatingCashFlow: num(c.operatingCashFlow ?? c.netCashProvidedByOperatingActivities),
      capex: num(c.capitalExpenditure),
      freeCashFlow: num(c.freeCashFlow),
      dividends: num(c.commonDividendsPaid ?? c.dividendsPaid),
      buybacks: num(c.commonStockRepurchased),
      pe: num(r.priceToEarningsRatio ?? r.priceEarningsRatio),
      ps: num(r.priceToSalesRatio),
      pb: num(r.priceToBookRatio),
      evEbitda: num(r.enterpriseValueMultiple),
      pfcf: num(r.priceToFreeCashFlowRatio ?? r.priceToFreeCashFlowsRatio),
    };
  }).filter((y) => y.revenue != null).sort((a, b) => (a.fy < b.fy ? -1 : 1));
}

// Finnhub's metric names vary between companies; take the first present.
function pick(m, keys) {
  if (!m) return null;
  for (const k of keys) if (m[k] != null && Number.isFinite(+m[k])) return +m[k];
  return null;
}

function peerMetrics(m) {
  return {
    marketCap: mul(pick(m, ["marketCapitalization"]), 1e6),
    revenueGrowth: pick(m, ["revenueGrowthTTMYoy", "revenueGrowthQuarterlyYoy"]),
    operatingMargin: pick(m, ["operatingMarginTTM", "operatingMarginAnnual"]),
    pe: pick(m, ["peTTM", "peExclExtraTTM", "peBasicExclExtraTTM", "peInclExtraTTM"]),
    evEbitda: pick(m, ["evEbitdaTTM", "enterpriseValueEbitdaTTM", "currentEv/ebitdaTTM"]),
    ps: pick(m, ["psTTM", "priceToSalesTTM"]),
    pb: pick(m, ["pbQuarterly", "pbAnnual", "ptbvQuarterly"]),
    fcfYield: inv(pick(m, ["pfcfShareTTM", "pfcfShareAnnual"])),
  };
}

function selfMetrics(m) {
  if (!m) return null;
  return {
    ...peerMetrics(m),
    eps: pick(m, ["epsTTM", "epsInclExtraItemsTTM", "epsExclExtraItemsTTM", "epsBasicExclExtraItemsTTM"]),
    high52: pick(m, ["52WeekHigh"]),
    low52: pick(m, ["52WeekLow"]),
    beta: pick(m, ["beta"]),
    dividendYield: pick(m, ["currentDividendYieldTTM", "dividendYieldIndicatedAnnual"]),
    dividendPerShare: pick(m, ["dividendPerShareTTM", "dividendsPerShareTTM", "dividendPerShareAnnual"]),
  };
}

/* ---- Vendors ---- */

async function finnhub(path, params, env) {
  if (!env.FINNHUB_API_KEY) throw new ApiError(500, "config", "The price service is not configured.");
  return vendor(`${FINNHUB}${path}?${qs(params)}`, { "X-Finnhub-Token": env.FINNHUB_API_KEY });
}

async function fmp(path, params, env) {
  if (!env.FMP_API_KEY) throw new ApiError(500, "config", "The fundamentals service is not configured.");
  const d = await vendor(`${FMP}${path}?${qs({ ...params, apikey: env.FMP_API_KEY })}`, {});
  // FMP reports plan limits and bad keys as a 200 with an error message.
  if (d && !Array.isArray(d) && (d["Error Message"] || d.error || d.message)) {
    const msg = String(d["Error Message"] || d.error || d.message);
    if (/limit/i.test(msg)) throw new ApiError(503, "busy", "Today's free data allowance is used up. Try again tomorrow.", 3600);
    throw new ApiError(502, "plan", "This figure is not in the current data plan.");
  }
  return d;
}

async function vendor(url, headers) {
  let res;
  try {
    res = await fetch(url, { headers: { Accept: "application/json", ...headers }, cf: { cacheTtl: 0 } });
  } catch (e) {
    throw new ApiError(502, "upstream", "The data source did not answer.");
  }
  if (res.status === 429) throw new ApiError(503, "busy", "The data source is busy. Try again in a minute.", 60);
  if (res.status === 401 || res.status === 402 || res.status === 403) throw new ApiError(502, "plan", "This figure is not in the current data plan.");
  if (res.status === 404) throw new ApiError(404, "not_found", "Not found.");
  if (!res.ok) throw new ApiError(502, "upstream", "The data source did not answer.");
  try {
    return await res.json();
  } catch (e) {
    throw new ApiError(502, "upstream", "The data source sent an unreadable answer.");
  }
}

/* ---- Helpers ---- */

class ApiError extends Error {
  constructor(status, code, message, retryAfter) {
    super(message);
    this.status = status;
    this.code = code;
    this.retryAfter = retryAfter;
  }
}

function corsHeaders(origin, env) {
  const allowed = String(env.ALLOWED_ORIGINS || "").split(",").map((s) => s.trim()).filter(Boolean);
  const base = { "Access-Control-Allow-Methods": "GET, OPTIONS", "Access-Control-Max-Age": "86400", Vary: "Origin" };
  if (origin && allowed.includes(origin)) return { ...base, "Access-Control-Allow-Origin": origin };
  return base;
}

function cleanTicker(t) {
  const s = String(t || "").trim().toUpperCase();
  if (!TICKER.test(s)) throw new Error("Give a ticker such as AAPL.");
  return s;
}

function cleanQuery(q) {
  const s = String(q || "").trim().replace(/\s+/g, " ");
  if (!s || s.length > 40 || !/^[\p{L}\p{N} .&'-]+$/u.test(s)) throw new Error("Search with a ticker or a company name.");
  return s.toLowerCase();
}

function json(obj, status, headers) {
  return new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json; charset=utf-8", ...headers } });
}

function withHeaders(res, headers) {
  const out = new Response(res.body, res);
  for (const [k, v] of Object.entries(headers)) out.headers.set(k, v);
  return out;
}

function qs(params) {
  return Object.entries(params).map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join("&");
}

function num(v) {
  if (v === null || v === undefined || v === "") return null;
  const n = +v;
  return Number.isFinite(n) ? n : null;
}

function mul(v, k) {
  return v == null ? null : v * k;
}

function inv(v) {
  return v ? 100 / v : null;
}

function ymd(d) {
  return d.toISOString().slice(0, 10);
}

function titleCase(s) {
  // Vendors send names in capitals ("APPLE INC"). Words with no vowel or with
  // an ampersand stay in capitals (AT&T, NVR); the rest take a capital first letter.
  if (s !== s.toUpperCase()) return s;
  return s.split(" ").map((w) => (/&/.test(w) || !/[AEIOUY]/.test(w) ? w : w.charAt(0) + w.slice(1).toLowerCase())).join(" ");
}

function firstSentences(text, n) {
  const parts = text.replace(/\s+/g, " ").trim().match(/[^.!?]+[.!?]+(\s|$)/g);
  if (!parts) return text.slice(0, 600);
  return parts.slice(0, n).join("").trim();
}

export const _test = { mergeYears, peerMetrics, selfMetrics, cleanTicker, cleanQuery, titleCase, firstSentences, corsHeaders, TTL };
