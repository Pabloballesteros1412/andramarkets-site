#!/usr/bin/env python3
"""Fetch the figures behind Hedge Fund Data: Attention.

Run by .github/workflows/hedgefund-data.yml: Wikipedia once a day, GDELT a
few subjects every run. Writes .cache/hf/attention.json (schema "andra.attention/1",
Actions cache, never committed or published):

    wikipedia  daily views of the English Wikipedia article on each of the
               companies and market subjects in WIKI_GROUPS, for 400 days (Wikimedia
               pageviews API, people only, no bots; no key). A day's views
               against the article's own 90-day average is the attention
               spike the page shows.
    news       for each subject in NEWS, the share of all the world's online
               news coverage in English that mentions it, and that coverage's
               average tone, each day for three months (GDELT DOC 2.0, no key).
               GDELT limits cloud addresses hard, so each run renews only the
               three subjects fetched longest ago, twelve seconds apart.

A failed source keeps its last good copy with its own date.

    python3 tools/attention_data.py [--force]
"""
import argparse
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dashboard_data import get, log  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "hf" / "attention.json"
SCHEMA = "andra.attention/1"
WIKI_RULE = 2  # raise when the way views are counted changes, so the day's copy is fetched again
# Wikimedia asks automated clients to name themselves and a way to reach them.
WIKI_UA = {"User-Agent": "AndraMarketsSite/1.0 (https://github.com/Pabloballesteros1412/andramarkets-site)"}
WIKI = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{}/daily/{}/{}"
WIKI_DAYS = 400
# group -> (key, the page's name, Wikipedia article). Companies, markets and subjects only: no people.
# A title that Wikipedia has since moved is followed to its article by canonical().
WIKI_GROUPS = {
    "Technology": [
        ("AAPL", "Apple", "Apple_Inc."), ("MSFT", "Microsoft", "Microsoft"), ("AMZN", "Amazon", "Amazon_(company)"),
        ("GOOGL", "Alphabet", "Google"), ("META", "Meta", "Meta_Platforms"), ("TSLA", "Tesla", "Tesla,_Inc."),
        ("NFLX", "Netflix", "Netflix"), ("PLTR", "Palantir", "Palantir_Technologies"), ("ORCL", "Oracle", "Oracle_Corporation"),
        ("CRM", "Salesforce", "Salesforce"), ("ADBE", "Adobe", "Adobe_Inc."), ("IBM", "IBM", "IBM"), ("CSCO", "Cisco", "Cisco"),
        ("SAP", "SAP", "SAP"), ("SHOP", "Shopify", "Shopify"), ("UBER", "Uber", "Uber"), ("ABNB", "Airbnb", "Airbnb"),
        ("SPOT", "Spotify", "Spotify"), ("SNOW", "Snowflake", "Snowflake_Inc."), ("CRWD", "CrowdStrike", "CrowdStrike"),
        ("PANW", "Palo Alto Networks", "Palo_Alto_Networks"), ("NOW", "ServiceNow", "ServiceNow"), ("DELL", "Dell", "Dell_Technologies"),
        ("SMCI", "Supermicro", "Supermicro"), ("CRWV", "CoreWeave", "CoreWeave"), ("RDDT", "Reddit", "Reddit"),
        ("SNAP", "Snap", "Snap_Inc."), ("PINS", "Pinterest", "Pinterest"), ("RBLX", "Roblox", "Roblox_Corporation"),
        ("HOOD", "Robinhood", "Robinhood_Markets"), ("XYZ", "Block", "Block,_Inc."), ("PYPL", "PayPal", "PayPal"),
        ("SSNLF", "Samsung Electronics", "Samsung_Electronics"), ("SONY", "Sony", "Sony"), ("NTDOY", "Nintendo", "Nintendo"),
        ("TCEHY", "Tencent", "Tencent"), ("BABA", "Alibaba", "Alibaba_Group"), ("BIDU", "Baidu", "Baidu"),
        ("XIACY", "Xiaomi", "Xiaomi"), ("SFTBY", "SoftBank", "SoftBank_Group"), ("HNHPF", "Foxconn", "Foxconn"),
    ],
    "Semiconductors": [
        ("NVDA", "Nvidia", "Nvidia"), ("AMD", "AMD", "AMD"), ("INTC", "Intel", "Intel"), ("TSM", "TSMC", "TSMC"),
        ("AVGO", "Broadcom", "Broadcom"), ("ASML", "ASML", "ASML_Holding"), ("QCOM", "Qualcomm", "Qualcomm"),
        ("MU", "Micron", "Micron_Technology"), ("ARM", "Arm", "Arm_Holdings"), ("TXN", "Texas Instruments", "Texas_Instruments"),
        ("AMAT", "Applied Materials", "Applied_Materials"), ("LRCX", "Lam Research", "Lam_Research"), ("HXSCL", "SK Hynix", "SK_Hynix"),
        ("MRVL", "Marvell", "Marvell_Technology"), ("SMIC", "SMIC", "Semiconductor_Manufacturing_International_Corporation"),
    ],
    "Finance": [
        ("BRK", "Berkshire Hathaway", "Berkshire_Hathaway"), ("JPM", "JPMorgan Chase", "JPMorgan_Chase"), ("GS", "Goldman Sachs", "Goldman_Sachs"),
        ("MS", "Morgan Stanley", "Morgan_Stanley"), ("BAC", "Bank of America", "Bank_of_America"), ("C", "Citigroup", "Citigroup"),
        ("WFC", "Wells Fargo", "Wells_Fargo"), ("BLK", "BlackRock", "BlackRock"), ("BX", "Blackstone", "Blackstone_Inc."),
        ("KKR", "KKR", "KKR_%26_Co."), ("APO", "Apollo", "Apollo_Global_Management"), ("V", "Visa", "Visa_Inc."),
        ("MA", "Mastercard", "Mastercard"), ("AXP", "American Express", "American_Express"), ("SCHW", "Charles Schwab", "Charles_Schwab_Corporation"),
        ("HSBC", "HSBC", "HSBC"), ("UBS", "UBS", "UBS"), ("DB", "Deutsche Bank", "Deutsche_Bank"), ("COIN", "Coinbase", "Coinbase"),
        ("MSTR", "Strategy", "Strategy_Inc."),
    ],
    "Health": [
        ("LLY", "Eli Lilly", "Eli_Lilly_and_Company"), ("NVO", "Novo Nordisk", "Novo_Nordisk"), ("PFE", "Pfizer", "Pfizer"),
        ("MRNA", "Moderna", "Moderna"), ("JNJ", "Johnson & Johnson", "Johnson_%26_Johnson"), ("MRK", "Merck", "Merck_%26_Co."),
        ("ABBV", "AbbVie", "AbbVie"), ("UNH", "UnitedHealth", "UnitedHealth_Group"), ("AZN", "AstraZeneca", "AstraZeneca"),
        ("NVS", "Novartis", "Novartis"), ("RHHBY", "Roche", "Roche"), ("CVS", "CVS Health", "CVS_Health"),
    ],
    "Energy": [
        ("XOM", "ExxonMobil", "ExxonMobil"), ("CVX", "Chevron", "Chevron_Corporation"), ("SHEL", "Shell", "Shell_plc"), ("BP", "BP", "BP"),
        ("TTE", "TotalEnergies", "TotalEnergies"), ("ARAMCO", "Saudi Aramco", "Saudi_Aramco"), ("COP", "ConocoPhillips", "ConocoPhillips"),
        ("OXY", "Occidental", "Occidental_Petroleum"), ("NEE", "NextEra Energy", "NextEra_Energy"), ("CEG", "Constellation Energy", "Constellation_Energy"),
        ("VST", "Vistra", "Vistra_Corp."), ("CCJ", "Cameco", "Cameco"), ("FSLR", "First Solar", "First_Solar"), ("GEV", "GE Vernova", "GE_Vernova"),
    ],
    "Consumer": [
        ("WMT", "Walmart", "Walmart"), ("COST", "Costco", "Costco"), ("TGT", "Target", "Target_Corporation"), ("HD", "Home Depot", "Home_Depot"),
        ("NKE", "Nike", "Nike,_Inc."), ("MCD", "McDonald's", "McDonald%27s"), ("SBUX", "Starbucks", "Starbucks"),
        ("KO", "Coca-Cola", "The_Coca-Cola_Company"), ("PEP", "PepsiCo", "PepsiCo"), ("PG", "Procter & Gamble", "Procter_%26_Gamble"),
        ("DIS", "Disney", "The_Walt_Disney_Company"), ("LVMH", "LVMH", "LVMH"), ("RMS", "Hermes", "Herm%C3%A8s"), ("RACE", "Ferrari", "Ferrari"),
        ("TM", "Toyota", "Toyota"), ("VOW", "Volkswagen", "Volkswagen_Group"), ("F", "Ford", "Ford_Motor_Company"), ("GM", "General Motors", "General_Motors"),
        ("BYD", "BYD", "BYD_Company"), ("RIVN", "Rivian", "Rivian"), ("GME", "GameStop", "GameStop"), ("AMC", "AMC Theatres", "AMC_Theatres"),
        ("NESN", "Nestle", "Nestl%C3%A9"),
    ],
    "Industry and defence": [
        ("BA", "Boeing", "Boeing"), ("AIR", "Airbus", "Airbus"), ("LMT", "Lockheed Martin", "Lockheed_Martin"), ("RTX", "RTX", "RTX_Corporation"),
        ("NOC", "Northrop Grumman", "Northrop_Grumman"), ("GD", "General Dynamics", "General_Dynamics"), ("RHM", "Rheinmetall", "Rheinmetall"),
        ("BAE", "BAE Systems", "BAE_Systems"), ("CAT", "Caterpillar", "Caterpillar_Inc."), ("DE", "John Deere", "John_Deere"),
        ("GE", "GE Aerospace", "GE_Aerospace"), ("HON", "Honeywell", "Honeywell"), ("SIE", "Siemens", "Siemens"),
        ("UPS", "UPS", "United_Parcel_Service"), ("FDX", "FedEx", "FedEx"), ("MAERSK", "Maersk", "Maersk"),
        ("DAL", "Delta Air Lines", "Delta_Air_Lines"), ("UAL", "United Airlines", "United_Airlines"),
    ],
    "Private": [
        ("OPENAI", "OpenAI", "OpenAI"), ("ANTH", "Anthropic", "Anthropic"), ("SPACEX", "SpaceX", "SpaceX"), ("XAI", "xAI", "XAI_(company)"),
        ("STRIPE", "Stripe", "Stripe,_Inc."), ("DBX", "Databricks", "Databricks"), ("BYTED", "ByteDance", "ByteDance"), ("HUAWEI", "Huawei", "Huawei"),
        ("SHEIN", "Shein", "Shein"), ("ANDURIL", "Anduril", "Anduril_Industries"), ("MISTRAL", "Mistral AI", "Mistral_AI"),
        ("DEEPSEEK", "DeepSeek", "DeepSeek"), ("PPLX", "Perplexity", "Perplexity_AI"), ("SCALE", "Scale AI", "Scale_AI"), ("WAYMO", "Waymo", "Waymo"),
        ("STARLINK", "Starlink", "Starlink"), ("NEURALINK", "Neuralink", "Neuralink"), ("CITADEL", "Citadel", "Citadel_LLC"),
        ("BWATER", "Bridgewater", "Bridgewater_Associates"), ("RENTEC", "Renaissance Technologies", "Renaissance_Technologies"),
    ],
    "Themes": [
        ("T_AI", "Artificial intelligence", "Artificial_intelligence"), ("T_CHATGPT", "ChatGPT", "ChatGPT"), ("T_CLAUDE", "Claude", "Claude_(language_model)"),
        ("T_GEMINI", "Gemini", "Gemini_(chatbot)"), ("T_LLM", "Large language model", "Large_language_model"),
        ("T_AGI", "Artificial general intelligence", "Artificial_general_intelligence"), ("T_AIBUB", "AI bubble", "AI_bubble"),
        ("T_DC", "Data center", "Data_center"), ("T_GPU", "Graphics processing unit", "Graphics_processing_unit"),
        ("T_QUANT", "Quantum computing", "Quantum_computing"), ("T_ROBOT", "Humanoid robot", "Humanoid_robot"), ("T_FUSION", "Fusion power", "Fusion_power"),
        ("T_SMR", "Small modular reactor", "Small_modular_reactor"), ("T_GLP1", "GLP-1 drugs", "GLP-1_receptor_agonist"), ("T_SEMA", "Semaglutide", "Semaglutide"),
        ("T_SDC", "Self-driving car", "Self-driving_car"), ("T_EV", "Electric vehicle", "Electric_vehicle"), ("T_RARE", "Rare-earth element", "Rare-earth_element"),
        ("T_LITH", "Lithium", "Lithium"), ("T_URAN", "Uranium", "Uranium"),
    ],
    "Crypto": [
        ("BTC", "Bitcoin", "Bitcoin"), ("ETH", "Ethereum", "Ethereum"), ("SOL", "Solana", "Solana_(blockchain_platform)"), ("DOGE", "Dogecoin", "Dogecoin"),
        ("USDT", "Tether", "Tether_(cryptocurrency)"), ("BNB", "Binance", "Binance"), ("CRYPTO", "Cryptocurrency", "Cryptocurrency"),
        ("STABLE", "Stablecoin", "Stablecoin"),
    ],
    "Assets": [
        ("GOLD", "Gold", "Gold_as_an_investment"), ("SILVER", "Silver", "Silver_as_an_investment"), ("OIL", "Oil price", "Price_of_oil"),
        ("BRENT", "Brent crude", "Brent_Crude"), ("NATGAS", "Natural gas", "Natural_gas"), ("COPPER", "Copper", "Copper"), ("SPX", "S&P 500", "S%26P_500"),
        ("NDX", "Nasdaq-100", "Nasdaq-100"), ("DJIA", "Dow Jones", "Dow_Jones_Industrial_Average"), ("RUT", "Russell 2000", "Russell_2000_Index"),
        ("VIX", "VIX", "VIX"), ("N225", "Nikkei 225", "Nikkei_225"), ("DXY", "US dollar index", "U.S._Dollar_Index"), ("USD", "US dollar", "United_States_dollar"),
        ("JPY", "Japanese yen", "Japanese_yen"), ("EUR", "Euro", "Euro"), ("CNY", "Renminbi", "Renminbi"), ("UST", "US Treasuries", "United_States_Treasury_security"),
        ("CURVE", "Yield curve", "Yield_curve"), ("ETF", "Exchange-traded fund", "Exchange-traded_fund"), ("SHORT", "Short selling", "Short_(finance)"),
        ("MARGIN", "Margin", "Margin_(finance)"), ("OPTION", "Options", "Option_(finance)"), ("HF", "Hedge fund", "Hedge_fund"),
        ("PCREDIT", "Private credit", "Private_credit"), ("PE", "Private equity", "Private_equity"),
    ],
    "Macro": [
        ("REC", "Recession", "Recession"), ("INFL", "Inflation", "Inflation"), ("TARIFF", "Tariff", "Tariff"), ("FED", "Federal Reserve", "Federal_Reserve"),
        ("BUBBLE", "Stock market bubble", "Stock_market_bubble"), ("CRASH", "Stock market crash", "Stock_market_crash"), ("LAYOFF", "Layoff", "Layoff"),
        ("STAG", "Stagflation", "Stagflation"), ("DEFL", "Deflation", "Deflation"), ("UNEMP", "Unemployment", "Unemployment"),
        ("RATE", "Interest rate", "Interest_rate"), ("QE", "Quantitative easing", "Quantitative_easing"),
        ("USDEBT", "US national debt", "National_debt_of_the_United_States"), ("CEILING", "US debt ceiling", "United_States_debt_ceiling"),
        ("SHUTDOWN", "US government shutdown", "Government_shutdowns_in_the_United_States"), ("BANKRUN", "Bank run", "Bank_run"),
        ("FINCRISIS", "Financial crisis", "Financial_crisis"), ("GFC", "2008 financial crisis", "2008_financial_crisis"),
        ("DEPRESSION", "Great Depression", "Great_Depression"), ("DOTCOM", "Dot-com bubble", "Dot-com_bubble"), ("HYPER", "Hyperinflation", "Hyperinflation"),
        ("SQUEEZE", "Short squeeze", "Short_squeeze"), ("INSIDER", "Insider trading", "Insider_trading"), ("BANKRUPT", "Bankruptcy", "Bankruptcy"),
        ("SOVDEF", "Sovereign default", "Sovereign_default"), ("FXCRISIS", "Currency crisis", "Currency_crisis"), ("TRADEWAR", "Trade war", "Trade_war"),
        ("HOUSING", "Housing bubble", "Housing_bubble"), ("MORTGAGE", "Mortgage", "Mortgage"), ("CDS", "Credit default swap", "Credit_default_swap"),
        ("UBI", "Universal basic income", "Universal_basic_income"), ("CPI", "Consumer price index", "Consumer_price_index"),
        ("GDP", "Gross domestic product", "Gross_domestic_product"), ("FOMC", "FOMC", "Federal_Open_Market_Committee"),
        ("ECB", "European Central Bank", "European_Central_Bank"), ("BOJ", "Bank of Japan", "Bank_of_Japan"),
        ("PBOC", "People's Bank of China", "People%27s_Bank_of_China"), ("IMF", "IMF", "International_Monetary_Fund"), ("OPEC", "OPEC", "OPEC"),
        ("BRICS", "BRICS", "BRICS"), ("DEDOLLAR", "Dedollarisation", "Dedollarisation"),
    ],
    "Geopolitics": [
        ("HORMUZ", "Strait of Hormuz", "Strait_of_Hormuz"), ("SUEZ", "Suez Canal", "Suez_Canal"), ("PANAMA", "Panama Canal", "Panama_Canal"),
        ("TWSTRAIT", "Taiwan Strait", "Taiwan_Strait"), ("REDSEA", "Red Sea crisis", "Red_Sea_crisis"), ("BABEL", "Bab-el-Mandeb", "Bab-el-Mandeb"),
        ("MALACCA", "Strait of Malacca", "Strait_of_Malacca"), ("SCS", "South China Sea", "South_China_Sea"),
        ("UKRAINE", "Russian invasion of Ukraine", "Russian_invasion_of_Ukraine"), ("SANCTIONS", "Economic sanctions", "Economic_sanctions"),
        ("TAIWAN", "Taiwan", "Taiwan"), ("NATO", "NATO", "NATO"), ("NUKE", "Nuclear weapon", "Nuclear_weapon"), ("MARTIAL", "Martial law", "Martial_law"),
        ("COUP", "Coup d'etat", "Coup_d%27%C3%A9tat"), ("EMBARGO", "Embargo", "Embargo"), ("BLOCKADE", "Blockade", "Blockade"),
        ("SPR", "Strategic Petroleum Reserve", "Strategic_Petroleum_Reserve_(United_States)"), ("NORDSTREAM", "Nord Stream", "Nord_Stream"),
        ("CHIPS", "CHIPS Act", "CHIPS_and_Science_Act"), ("GREENLAND", "Greenland", "Greenland"), ("IRAN", "Iran", "Iran"),
        ("NKOREA", "North Korea", "North_Korea"), ("VENEZUELA", "Venezuela", "Venezuela"), ("WW3", "World War III", "World_War_III"),
        ("PANDEMIC", "Pandemic", "Pandemic"), ("H5N1", "Avian influenza", "Avian_influenza"), ("CYBER", "Cyberattack", "Cyberattack"),
        ("BLACKOUT", "Power outage", "Power_outage"),
    ],
}
# (key, the page's name, Wikipedia article, group)
WIKI_ARTICLES = [(k, n, a, g) for g, rows in WIKI_GROUPS.items() for k, n, a in rows]
GDELT = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_GAP = 12.0  # seconds between requests: GDELT asks for at least five, and is stricter with cloud addresses
GDELT_PER_RUN = 3  # subjects asked for in one run, the stalest first; over a day's runs every subject is renewed
# (key, the page's name, GDELT query)
NEWS = [
    ("recession", "Recession", '(recession OR "economic downturn")'),
    ("inflation", "Inflation", "inflation"),
    ("tariffs", "Tariffs", "(tariff OR tariffs)"),
    ("fed", "The Fed", '("Federal Reserve" OR "the Fed")'),
    ("layoffs", "Layoffs", "(layoffs OR \"job cuts\")"),
    ("ai_bubble", "AI bubble", '"AI bubble"'),
    ("oil", "Oil supply", '("oil supply" OR "oil prices")'),
    ("hormuz", "Strait of Hormuz", '"Strait of Hormuz"'),
    ("taiwan", "Taiwan Strait", '("Taiwan Strait" OR "blockade of Taiwan")'),
    ("shipping", "Shipping disruption", '("shipping disruption" OR "supply chain disruption")'),
    ("default", "Default and debt", '("debt ceiling" OR "sovereign default" OR "bond market")'),
    ("bank", "Bank stress", '("bank run" OR "bank failure" OR "banking crisis")'),
]


def now_utc():
    return dt.datetime.now(dt.timezone.utc)


def canonical(titles):
    """Each title as Wikipedia files its article today. A page that has been moved leaves a redirect,
    and the pageviews API counts the redirect's own few views, not the article's: Strategy Inc. read
    7 times a day under its old title. Titles that cannot be resolved are kept as they are."""
    out = {t: t for t in titles}
    try:
        step = {}
        for i in range(0, len(titles), 50):  # the API takes 50 titles a request
            q = urllib.parse.urlencode({"action": "query", "format": "json", "redirects": 1,
                                        "titles": "|".join(urllib.parse.unquote(t) for t in titles[i:i + 50])})
            d = json.loads(get("https://en.wikipedia.org/w/api.php?" + q, headers=WIKI_UA))["query"]
            step.update({x["from"].replace(" ", "_"): x["to"].replace(" ", "_") for x in d.get("normalized", []) + d.get("redirects", [])})
        for t in titles:
            cur = urllib.parse.unquote(t)
            for _ in range(3):  # normalised, then redirected
                if cur not in step:
                    break
                cur = step[cur]
            if cur != urllib.parse.unquote(t):
                out[t] = urllib.parse.quote(cur, safe="_(),.")
                log(f"Wikipedia: {t} is now {cur}")
    except Exception as e:  # noqa: BLE001
        log(f"Wikipedia: titles not resolved, using them as written: {type(e).__name__}: {e}", "warning")
    return out


def views_of(art, start, end):
    """{YYYYMMDD: views} for one title, or {} if Wikipedia has none."""
    url = WIKI.format(art, start.strftime("%Y%m%d00"), end.strftime("%Y%m%d00"))
    for i in range(4):
        try:
            items = json.loads(get(url, headers=WIKI_UA)).get("items", [])
            return {it["timestamp"][:8]: it["views"] for it in items}
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {}
            if e.code != 429 or i == 3:
                raise
            time.sleep(5 * (i + 1))
    return {}


def wikipedia(old):
    titles = canonical([a[2] for a in WIKI_ARTICLES])
    end = now_utc().date() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=WIKI_DAYS)
    out = []
    for key, name, written, group in WIKI_ARTICLES:
        art = titles[written]
        views = views_of(art, start, end)
        time.sleep(0.15)
        if art != written:
            # Views are counted under the title asked for: before the article was moved they are under
            # the old title, and after it the old title keeps the readers who still follow old links.
            for day, n in views_of(written, start, end).items():
                views[day] = views.get(day, 0) + n
            time.sleep(0.15)
        if not views:
            log(f"Wikipedia: no views for {art}", "warning")
            continue
        first = dt.datetime.strptime(min(views), "%Y%m%d").date()
        n = (end - first).days + 1
        series = [views.get((first + dt.timedelta(days=i)).strftime("%Y%m%d")) for i in range(n)]
        out.append({"key": key, "name": name, "article": art, "group": group, "first": first.isoformat(), "views": series})
    if not out:
        raise ValueError("Wikipedia returned no views")
    # Yesterday's count is published some hours into the day: a last day nobody has yet is dropped.
    while all(a["views"] and a["views"][-1] is None for a in out):
        for a in out:
            a["views"].pop()
        end -= dt.timedelta(days=1)
    return {"fetched": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"), "last": end.isoformat(), "asked": len(WIKI_ARTICLES), "rule": WIKI_RULE, "articles": out,
            "source": "Wikimedia pageviews (English Wikipedia, users only)"}


def gdelt(mode, query):
    q = urllib.parse.urlencode({"query": f"{query} sourcelang:english", "mode": mode, "format": "json", "timespan": "3months"})
    try:
        return json.loads(get(f"{GDELT}?{q}"))
    finally:
        time.sleep(GDELT_GAP)


def news(old):
    """Renews the GDELT_PER_RUN subjects fetched longest ago; the others keep their last copy."""
    kept = {s["key"]: s for s in (old or {}).get("subjects", [])}
    order = sorted(NEWS, key=lambda n: (kept.get(n[0]) or {}).get("fetched", ""))
    renewed = 0
    for key, name, query in order[:GDELT_PER_RUN]:
        try:
            vol = gdelt("timelinevol", query)
            tone = gdelt("timelinetone", query)
        except Exception as e:  # noqa: BLE001
            log(f"GDELT {name}: {type(e).__name__}: {e}", "warning")
            continue
        v = {d["date"][:8]: d["value"] for d in (vol.get("timeline") or [{}])[0].get("data", [])}
        t = {d["date"][:8]: d["value"] for d in (tone.get("timeline") or [{}])[0].get("data", [])}
        days = sorted(v)
        if not days:
            continue
        kept[key] = {"key": key, "name": name, "query": query, "fetched": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "first": f"{days[0][:4]}-{days[0][4:6]}-{days[0][6:]}",
                     # share of all monitored English coverage, in percent; tone runs about -10 (negative) to +10
                     "share": [round(v[d], 4) for d in days], "tone": [None if d not in t else round(t[d], 2) for d in days]}
        renewed += 1
    if not kept:
        raise ValueError("GDELT returned nothing")
    log(f"GDELT: renewed {renewed} of {GDELT_PER_RUN} subjects; {len(kept)} of {len(NEWS)} held")
    return {"fetched": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"), "subjects": [kept[k] for k, _, _ in NEWS if k in kept],
            "source": "The GDELT Project, DOC 2.0 (English-language online news)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    try:
        old = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = {}
    today = now_utc().date().isoformat()
    out = {"schema": SCHEMA, "wikipedia": old.get("wikipedia"), "news": old.get("news")}
    did = False
    for part, fn in (("wikipedia", lambda: wikipedia(old.get("wikipedia"))), ("news", lambda: news(old.get("news")))):
        if (part == "wikipedia" and not a.force and (out[part] or {}).get("fetched", "")[:10] == today
                and (out[part] or {}).get("asked") == len(WIKI_ARTICLES) and (out[part] or {}).get("rule") == WIKI_RULE):  # a longer list is fetched at once
            continue
        try:
            out[part] = fn()
            did = True
            log(f"Attention, {part}: {len(out[part].get('articles') or out[part].get('subjects'))} series")
        except Exception as e:  # noqa: BLE001
            log(f"Attention, {part} failed, keeping the last copy: {type(e).__name__}: {e}", "warning")
    if not did:
        log("Attention: already fetched today")
        return 0
    if not out["wikipedia"] and not out["news"]:
        return 1
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    log(f"Wrote {CACHE.relative_to(ROOT)} ({CACHE.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
