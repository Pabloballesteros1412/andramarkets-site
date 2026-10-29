// Tests for the profile API with the vendors stubbed: no network, no keys.
// Run: cd worker && npm test
import { test, beforeEach } from "node:test";
import assert from "node:assert/strict";
import worker, { _test } from "../src/index.js";

const ORIGIN = "https://pabloballesteros1412.github.io";
const FAKE_FINNHUB = "finnhub-test-key";
const FAKE_FMP = "fmp-test-key";
let calls, routes, store;

function env(extra) {
  return { FINNHUB_API_KEY: FAKE_FINNHUB, FMP_API_KEY: FAKE_FMP, ALLOWED_ORIGINS: ORIGIN, ...extra };
}
function ctx() {
  const waits = [];
  return { waitUntil: (p) => waits.push(p), done: () => Promise.all(waits) };
}
async function call(path, opts = {}) {
  const c = ctx();
  const res = await worker.fetch(new Request("https://api.test" + path, { headers: opts.origin === null ? {} : { Origin: opts.origin || ORIGIN } }), opts.env || env(), c);
  await c.done();
  return { res, body: await res.json() };
}

beforeEach(() => {
  calls = [];
  routes = {};
  store = new Map();
  globalThis.caches = {
    default: {
      match: async (req) => (store.has(req.url) ? store.get(req.url).clone() : undefined),
      put: async (req, res) => { store.set(req.url, res); },
    },
  };
  globalThis.fetch = async (url) => {
    calls.push(String(url));
    const u = new URL(url);
    const key = u.host.includes("finnhub") ? "fh:" + u.pathname.replace("/api/v1", "") : "fmp:" + u.pathname.replace("/stable", "");
    const r = routes[key];
    if (!r) return new Response("[]", { status: 200 });
    const out = typeof r === "function" ? r(u) : r;
    if (out instanceof Response) return out;
    return new Response(JSON.stringify(out), { status: 200 });
  };
});

test("quote: shapes the answer, caches it for 60 seconds, sends no key back", async () => {
  routes["fh:/quote"] = { c: 184.62, d: 2.31, dp: 1.27, pc: 182.31, t: 1793299320 };
  const a = await call("/quote?t=aapl");
  assert.equal(a.res.status, 200);
  assert.equal(a.body.t, "AAPL");
  assert.equal(a.body.price, 184.62);
  assert.equal(a.body.changePct, 1.27);
  assert.equal(a.res.headers.get("Access-Control-Allow-Origin"), ORIGIN);
  assert.match(a.res.headers.get("Cache-Control"), /s-maxage=60\b/);
  assert.ok(!JSON.stringify(a.body).includes(FAKE_FINNHUB));
  const b = await call("/api/quote?t=AAPL");
  assert.equal(b.res.headers.get("X-Cache"), "HIT");
  assert.equal(calls.length, 1, "second call served from cache");
  // The key travels in a header, never in the URL Finnhub logs.
  assert.ok(!calls[0].includes(FAKE_FINNHUB));
});

test("quote: an unknown ticker is a 404", async () => {
  routes["fh:/quote"] = { c: 0, d: null, dp: null, pc: 0, t: 0 };
  const a = await call("/quote?t=XQZT");
  assert.equal(a.res.status, 404);
  assert.equal(a.body.error.code, "not_found");
});

test("bad input and foreign origins are refused", async () => {
  assert.equal((await call("/quote?t=<script>")).res.status, 400);
  assert.equal((await call("/search?q=" + "a".repeat(41))).res.status, 400);
  assert.equal((await call("/quote?t=AAPL", { origin: "https://evil.example" })).res.status, 403);
  assert.equal((await call("/quote?t=AAPL", { origin: null })).res.status, 403);
  assert.equal((await call("/nope?t=AAPL")).res.status, 404);
  assert.equal(calls.length, 0);
});

test("news: newest first, deduplicated, cached 15 minutes", async () => {
  routes["fh:/company-news"] = [
    { headline: "Old", source: "A", url: "https://a.example/1", datetime: 100 },
    { headline: "New", source: "B", url: "https://b.example/2", datetime: 300 },
    { headline: "New", source: "C", url: "https://c.example/3", datetime: 200 },
    { headline: "Bad link", source: "D", url: "javascript:alert(1)", datetime: 400 },
  ];
  const a = await call("/news?t=AAPL");
  assert.deepEqual(a.body.items.map((n) => n.title), ["New", "Old"]);
  assert.match(a.res.headers.get("Cache-Control"), /s-maxage=900\b/);
});

test("search: US common stock only, names out of capitals", async () => {
  routes["fh:/search"] = { result: [
    { symbol: "AAPL", description: "APPLE INC", type: "Common Stock" },
    { symbol: "AAPL.MX", description: "APPLE INC", type: "Common Stock" },
    { symbol: "APLE", description: "APPLE HOSPITALITY REIT INC", type: "REIT" },
    { symbol: "T", description: "AT&T INC", type: "Common Stock" },
  ] };
  const a = await call("/search?q=Apple");
  assert.deepEqual(a.body.results, [{ t: "AAPL", name: "Apple Inc" }, { t: "T", name: "AT&T Inc" }]);
});

test("rate limit from a vendor is a 503 busy with retryAfter, and not cached", async () => {
  routes["fh:/quote"] = new Response("{}", { status: 429 });
  const a = await call("/quote?t=AAPL");
  assert.equal(a.res.status, 503);
  assert.equal(a.body.error.code, "busy");
  assert.equal(a.body.error.retryAfter, 60);
  assert.equal(store.size, 0);
});

test("a missing secret says the service is not configured", async () => {
  const a = await call("/quote?t=AAPL", { env: env({ FINNHUB_API_KEY: "" }) });
  assert.equal(a.res.status, 500);
  assert.equal(a.body.error.code, "config");
  assert.equal(calls.length, 0);
});

test("fundamentals: joins the statements by fiscal year, oldest first", async () => {
  routes["fmp:/profile"] = [{ companyName: "Example Corp", exchange: "NASDAQ", sector: "Technology", industry: "Software", ceo: "A. Person",
    fullTimeEmployees: "61400", city: "AUSTIN", state: "TX", ipoDate: "1990-01-02", website: "https://example.com",
    description: "One. Two. Three. Four.", marketCap: 4.12e11, beta: 1.08, lastDividend: 2.99 }];
  routes["fmp:/income-statement"] = [
    { date: "2025-09-30", fiscalYear: "2025", revenue: 96.4e9, grossProfit: 44e9, operatingIncome: 28.7e9, netIncome: 27e9, epsDiluted: 11.7 },
    { date: "2024-09-30", fiscalYear: "2024", revenue: 90.8e9, grossProfit: 41e9, operatingIncome: 26e9, netIncome: 25e9, epsDiluted: 10.9 },
  ];
  routes["fmp:/balance-sheet-statement"] = [{ date: "2025-09-30", fiscalYear: "2025", totalDebt: 40e9, netDebt: 31e9, totalStockholdersEquity: 50e9 }];
  routes["fmp:/cash-flow-statement"] = [{ date: "2025-09-30", fiscalYear: "2025", freeCashFlow: 16.9e9, capitalExpenditure: -3e9 }];
  routes["fmp:/ratios"] = [{ date: "2025-09-30", fiscalYear: "2025", priceToEarningsRatio: 24.6 }];
  routes["fh:/stock/metric"] = { metric: { peTTM: 24.6, "52WeekHigh": 197, "52WeekLow": 141, revenueGrowthTTMYoy: 6.1 } };
  const a = await call("/fundamentals?t=EXMP");
  assert.equal(a.res.status, 200);
  assert.equal(a.body.profile.name, "Example Corp");
  assert.equal(a.body.profile.city, "Austin, TX");
  assert.equal(a.body.profile.employees, 61400);
  assert.equal(a.body.profile.description, "One. Two. Three.");
  assert.deepEqual(a.body.years.map((y) => y.fy), ["2024", "2025"]);
  assert.equal(a.body.years[1].netDebt, 31e9);
  assert.equal(a.body.years[1].pe, 24.6);
  assert.equal(a.body.years[0].pe, null);
  assert.equal(a.body.metrics.high52, 197);
  assert.deepEqual(a.body.missing, []);
  assert.match(a.res.headers.get("Cache-Control"), /s-maxage=86400\b/);
  const fmpCalls = calls.filter((c) => c.includes("financialmodelingprep"));
  assert.equal(fmpCalls.length, 5);
  assert.ok(!JSON.stringify(a.body).includes(FAKE_FMP));
});

test("fundamentals: a statement outside the plan is listed as missing, the rest still answer", async () => {
  routes["fmp:/profile"] = [{ companyName: "Example Corp" }];
  routes["fmp:/income-statement"] = [{ date: "2025-09-30", fiscalYear: "2025", revenue: 1e9 }];
  routes["fmp:/ratios"] = { "Error Message": "Premium endpoint" };
  const a = await call("/fundamentals?t=EXMP");
  assert.equal(a.res.status, 200);
  assert.ok(a.body.missing.includes("ratios"));
  assert.equal(a.body.years.length, 1);
});

test("fundamentals: FMP's daily limit is busy; an unknown ticker is not_found", async () => {
  routes["fmp:/profile"] = { "Error Message": "Limit Reach . Please upgrade your plan" };
  let a = await call("/fundamentals?t=EXMP");
  assert.equal(a.body.error.code, "busy");
  routes["fmp:/profile"] = [];
  a = await call("/fundamentals?t=XQZT");
  assert.equal(a.res.status, 404);
});

test("with the STALE namespace, a failure serves the last good answer, marked stale", async () => {
  const kv = new Map();
  const STALE = { get: async (k) => kv.get(k) ?? null, put: async (k, v) => { kv.set(k, v); } };
  routes["fh:/company-news"] = [{ headline: "Kept", source: "A", url: "https://a.example/1", datetime: 1 }];
  await call("/news?t=AAPL", { env: env({ STALE }) });
  store.clear();
  routes["fh:/company-news"] = new Response("{}", { status: 500 });
  const a = await call("/news?t=AAPL", { env: env({ STALE }) });
  assert.equal(a.res.status, 200);
  assert.equal(a.body.stale, true);
  assert.equal(a.body.items[0].title, "Kept");
  assert.ok(a.body.asOf);
});

test("peers: the company first, then up to five, each with name and metrics", async () => {
  routes["fh:/stock/peers"] = ["AAPL", "MSFT", "GOOGL", "BRK.B", "META", "AMZN", "NVDA", "ORCL"];
  routes["fh:/stock/profile2"] = (u) => ({ name: "Name " + u.searchParams.get("symbol") });
  routes["fh:/stock/metric"] = { metric: { marketCapitalization: 1000, peTTM: 20, operatingMarginTTM: 30 } };
  const a = await call("/peers?t=AAPL");
  assert.deepEqual(a.body.peers.map((p) => p.t), ["AAPL", "MSFT", "GOOGL", "META", "AMZN", "NVDA"]);
  assert.equal(a.body.peers[0].marketCap, 1e9);
  assert.equal(a.body.peers[1].name, "Name MSFT");
});

test("helpers", () => {
  assert.equal(_test.cleanTicker(" brk-b "), "BRK-B");
  assert.throws(() => _test.cleanTicker("1ABC"));
  assert.equal(_test.titleCase("NVR INC"), "NVR Inc");
  assert.equal(_test.titleCase("Already Mixed"), "Already Mixed");
});
