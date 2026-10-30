"""The Learn explainers: evergreen, neutral, sourced to official or academic
references, each linked to the dashboard that shows it live. Rendered by
tools/build_site.py as learn/ and learn/<slug>/.

Each entry: slug, title, description, (dashboard path, dashboard label),
sections as (heading, [paragraphs]), sources as (label, url). Paragraphs are
plain text (escaped when rendered). No personal names (PRODUCT.md): sources
are cited by title and publisher. No current figures: anything that changes
lives on the dashboards, dated.
"""

ARTICLES = [
    {
        "slug": "yield-curve",
        "title": "How to read the yield curve",
        "desc": "What the curve is, why it usually slopes up, and what it means when it turns upside down.",
        "dash": ("fed-rates/#fr-curve", "the Treasury curve in Fed & Rates"),
        "sections": [
            ("What the curve is", [
                "The US government borrows for many lengths of time, from a few weeks to thirty years. Each of "
                "those loans, a Treasury bill, note or bond, pays a yield: the return a buyer locks in by holding "
                "it to maturity. Plot those yields against their maturities, shortest on the left and longest on "
                "the right, and the line that joins them is the yield curve.",
                "The US Treasury publishes the curve every business day as par yields for maturities from one month "
                "to thirty years. Because the borrower is the same in every case, the differences between points "
                "on the curve are not about credit risk. They are about time: what investors expect short-term "
                "rates to do, and how much extra they want for tying their money up for longer.",
            ]),
            ("Why it usually slopes up", [
                "Most of the time the curve rises from left to right. A ten-year note usually yields more than a "
                "three-month bill, for two reasons.",
                "The first is expectations. A ten-year yield is roughly the average of the short-term rates investors "
                "expect over the next ten years. If they expect rates to stay where they are or rise, the long yield "
                "sits above the short one.",
                "The second is the term premium. A long bond's price swings more when rates change, and inflation "
                "over a decade is harder to predict than inflation over three months. Investors ask to be paid for "
                "carrying that risk, so long yields usually include a premium on top of expected short rates. The "
                "premium is not observed directly; economists estimate it with models, and the estimates differ.",
            ]),
            ("What moves each end", [
                "The short end, from one month to about two years, follows the Federal Reserve. The Fed sets a target "
                "range for the overnight federal funds rate, and bill yields track where investors think that rate "
                "will be over the life of the bill. A change in the expected path of policy moves the two-year yield "
                "more than almost anything else.",
                "The long end, ten to thirty years, depends on more: expected growth and inflation over many years, "
                "the term premium, the amount of debt the Treasury issues and the demand for safe assets at home and "
                "abroad. The long end can move a lot on days when the Fed does nothing.",
            ]),
            ("Steeper, flatter, inverted", [
                "The shape is often summarised by a spread between two points, most commonly the ten-year yield less "
                "the two-year, or the ten-year less the three-month. When the spread widens, the curve steepens; when "
                "it narrows, the curve flattens. A bull steepener is a steepening driven by falling short yields, "
                "often when markets expect rate cuts. A bear flattener is a flattening driven by rising short "
                "yields, often when the Fed is raising rates.",
                "When short yields rise above long ones, the curve is inverted. Investors are then accepting less to "
                "lend for ten years than for three months, which usually means they expect short rates to fall in "
                "the future, most often because they expect the economy to weaken and the Fed to cut.",
            ]),
            ("Why inversions get attention", [
                "Research at the Federal Reserve Bank of New York found that the spread between the ten-year and "
                "three-month Treasury yields has been a useful predictor of US recessions, and that an inverted curve "
                "has come before each US recession since the late 1960s. Academic work using decades of data reached "
                "a similar conclusion: the slope of the curve has been one of the more reliable financial indicators "
                "of a recession a year or so ahead.",
                "There are good reasons to hold that finding lightly. The lead time has varied from a few months to "
                "about two years. A low term premium, for example when central banks hold large amounts of long-term "
                "bonds, can flatten or invert the curve without any change in the growth outlook. And a signal that "
                "has worked over a handful of recessions is a small sample. An inversion is a statement about market "
                "expectations, not a forecast with a date attached.",
            ]),
            ("Reading it on the dashboard", [
                "The yield curve dashboard plots the latest curve as a solid line against the curve at the start of "
                "the chosen range as a dashed line. Maturities are spaced by the square root of their length, so the "
                "short end is not squeezed into a corner. Three questions get you most of the way: is the curve "
                "sloping up or down, has it moved up or down as a whole, and has the short end or the long end moved "
                "more? The panel beside the chart gives the ten-year less two-year spread and its change over the "
                "range, so a steepening or flattening is in numbers as well as shape.",
            ]),
        ],
        "sources": [
            ("US Department of the Treasury, Interest Rate Statistics: daily Treasury par yield curve rates",
             "https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics"),
            ("Federal Reserve Bank of New York, The Yield Curve as a Leading Indicator",
             "https://www.newyorkfed.org/research/capital_markets/ycfaq.html"),
            ("Predicting U.S. Recessions: Financial Variables as Leading Indicators, The Review of Economics and "
             "Statistics, 1998", "https://doi.org/10.1162/003465398557320"),
            ("FRED, 10-Year Treasury Constant Maturity Minus 3-Month Treasury Constant Maturity (T10Y3M)",
             "https://fred.stlouisfed.org/series/T10Y3M"),
        ],
    },
    {
        "slug": "vix",
        "title": "What moves the VIX",
        "desc": "What the volatility index measures, why it jumps when stocks fall, and what it cannot tell you.",
        "dash": ("dashboards/volatility-term-structure/", "the volatility term structure dashboard"),
        "sections": [
            ("What the VIX measures", [
                "The Cboe Volatility Index, the VIX, is a measure of how much the S&P 500 is expected to move over "
                "the next 30 days. It is not calculated from past prices. Cboe derives it from the prices of S&P 500 "
                "options across a wide range of strike prices, using the fact that an option is worth more when "
                "bigger moves are expected. The result is quoted in annualised percentage points.",
                "A rough way to read the number: divide it by the square root of 12 to get the expected size of a "
                "one-month move. A VIX of 20 implies a typical move, one standard deviation, of about 5.8% over the "
                "next month, up or down. The VIX says nothing about direction. It prices the size of the move.",
            ]),
            ("Why it jumps when stocks fall", [
                "The VIX usually rises when the S&P 500 falls and drifts lower when stocks climb steadily. Several "
                "forces push the same way. Falling prices tend to be followed by larger daily swings, so realised "
                "volatility rises. Investors who own stocks buy put options to protect themselves after a fall, and "
                "that demand raises option prices. Lower share prices also leave companies more leveraged, which "
                "makes their equity riskier.",
                "Rallies rarely have the same effect. Steady gains tend to come with small daily moves and little "
                "demand for protection. That asymmetry is why the VIX is often called the fear gauge, even though "
                "it is a price of insurance rather than a survey of anyone's feelings.",
            ]),
            ("The other things that move it", [
                "Scheduled events. Option prices rise ahead of known risks, such as a Federal Reserve decision, a "
                "consumer price index release or the results of the largest companies, and often fall back once the "
                "event has passed. A drop in the VIX the day after a big release is common and usually means the "
                "uncertainty was resolved, not that the outlook improved.",
                "The volatility risk premium. Implied volatility has usually been higher than the volatility that "
                "actually follows, because option sellers demand compensation for the risk of a crash. Academic "
                "studies of this variance risk premium find it is persistent and that it widens in stressed markets. "
                "A VIX of 15 does not mean the market will move 15% annualised; on average it has moved less.",
                "Mean reversion. Spikes in the VIX have tended to fade, and very low readings have tended not to "
                "last. That is a tendency in the history, not a rule, and it says nothing about timing.",
            ]),
            ("The term structure", [
                "The VIX looks 30 days ahead. Cboe publishes sister indices over other horizons, including nine days "
                "(VIX9D), three months (VIX3M) and six months (VIX6M). Plotted together they form a term structure. "
                "In calm markets it slopes upward, called contango: little is expected to happen soon, and more "
                "uncertainty is priced further out. In stress it inverts, called backwardation: near-term volatility "
                "is priced above longer-term volatility because the danger is now. The shape often says more than "
                "the level of any one index.",
            ]),
            ("What it cannot tell you", [
                "The VIX is not a forecast of returns, and a high reading is not a signal to buy or sell. It cannot "
                "be bought directly: investors trade VIX futures and options, whose prices follow where the index is "
                "expected to be at expiry, not where it is today, and products built on futures can lose value over "
                "time when the curve is in contango. The index also covers only the S&P 500. Other markets have their "
                "own measures, such as the MOVE index for Treasury yields.",
            ]),
            ("Reading it on the dashboard", [
                "The volatility term structure dashboard plots VIX9D, VIX, VIX3M and VIX6M as one line, with the "
                "structure at the start of the chosen range dashed behind it. Look first at the slope: rising from "
                "left to right is the normal state, falling is stress. Then compare with the dashed line to see "
                "whether near-term or longer-term volatility has done the moving.",
            ]),
        ],
        "sources": [
            ("Cboe, VIX Index", "https://www.cboe.com/tradable_products/vix/"),
            ("FRED, CBOE Volatility Index: VIX (VIXCLS)", "https://fred.stlouisfed.org/series/VIXCLS"),
            ("Variance Risk Premia, The Review of Financial Studies, 2009", "https://doi.org/10.1093/rfs/hhn038"),
        ],
    },
    {
        "slug": "earnings-season",
        "title": "How earnings season works",
        "desc": "When companies report, what is in the release, and why guidance often matters more than the beat.",
        "dash": ("calendar/", "the calendar's earnings rows"),
        "sections": [
            ("Four times a year", [
                "Listed companies in the United States report their results every quarter. The formal report is a "
                "filing with the Securities and Exchange Commission: Form 10-Q after each of the first three fiscal "
                "quarters and Form 10-K after the full year. The largest companies must file the 10-Q within 40 days "
                "of the quarter's end and the 10-K within 60 days; smaller companies have longer.",
                "Most companies announce their numbers before the filing, in a press release furnished to the SEC on "
                "Form 8-K, often followed the same day by a conference call with analysts. Because most companies "
                "close their quarters at the end of March, June, September and December, the releases bunch "
                "together. Earnings season usually starts with the large banks a couple of weeks after the quarter "
                "ends, and most of the S&P 500 has reported within about six weeks.",
            ]),
            ("What is in a release", [
                "Revenue, profit and earnings per share for the quarter, against the same quarter a year earlier. "
                "Most companies also report adjusted figures that leave out items such as restructuring charges or "
                "the cost of share-based pay. SEC rules require any such non-GAAP measure to be reconciled to the "
                "closest measure under US accounting standards, so the reader can see what was left out and why.",
                "Many companies also give guidance: their own expectation for revenue, margins or earnings in the "
                "next quarter or the full year. On the call, management explains the numbers and answers questions. "
                "The call often moves the shares as much as the release itself.",
            ]),
            ("Before the open, after the close", [
                "Most US companies release results either before the market opens or after it closes, so that "
                "investors have time to read them before they can trade on them in the regular session. Under the "
                "SEC's Regulation FD, material information has to be made public to everyone at once, not shared "
                "first with selected analysts or investors. That is why results arrive as a press release and a "
                "public call rather than in private meetings.",
            ]),
            ("Estimates, beats and misses", [
                "Analysts at banks and research firms publish forecasts for each company. The average of those "
                "forecasts is the consensus, and a result above it is a beat, below it a miss. Two habits make a "
                "beat less informative than it sounds. Estimates are often trimmed in the weeks before a release, "
                "and companies with some discretion over their guidance tend to set expectations they can clear. "
                "Over many seasons a clear majority of S&P 500 companies have reported earnings above consensus.",
                "So the market tends to judge a result by more than the headline. Revenue tells you about demand, "
                "which is harder to manage than costs. Margins show whether growth is profitable. Guidance shows "
                "what the company itself expects next, and a beat paired with weak guidance is often met with a "
                "falling share price.",
            ]),
            ("Reading the reaction", [
                "A useful measure of how a result was received is the move in the shares on the first full trading "
                "session after the release, set against the move in the wider market that day. A stock that falls 2% "
                "on a day the index falls 2% was not punished for its results. Moves are often largest in the first "
                "minutes after the release, outside regular hours, when fewer shares trade and prices can overshoot.",
                "Earnings season also gives a reading of the economy as a whole. Banks describe borrowers and "
                "deposits, retailers describe the consumer, manufacturers describe orders. The aggregate figure, "
                "the growth in earnings for the index as a whole, is one of the main inputs into how investors value "
                "the market.",
            ]),
            ("Reading it on the calendar", [
                "There is no earnings season dashboard yet, because there is no reliable free source of consensus "
                "estimates. The calendar lists the next report date of the largest companies in the US, Europe and "
                "Asia, marks each date as confirmed or estimated, shows the earnings per share a year earlier and, "
                "once the results are out, the reported figure and the first-session move against the company's "
                "benchmark.",
            ]),
        ],
        "sources": [
            ("Investor.gov (US Securities and Exchange Commission), Form 10-Q",
             "https://www.investor.gov/introduction-investing/investing-basics/glossary/form-10-q"),
            ("Investor.gov (US Securities and Exchange Commission), Form 8-K",
             "https://www.investor.gov/introduction-investing/investing-basics/glossary/form-8-k"),
            ("US Securities and Exchange Commission, Selective Disclosure and Insider Trading (Regulation FD), final rule",
             "https://www.sec.gov/rules/final/33-7881.htm"),
            ("US Securities and Exchange Commission, Conditions for Use of Non-GAAP Financial Measures (Regulation G), final rule",
             "https://www.sec.gov/rules/final/33-8176.htm"),
        ],
    },
    {
        "slug": "cpi-vs-pce",
        "title": "CPI vs PCE",
        "desc": "Two measures of US inflation, why they differ, and why the Fed targets the one that comes out second.",
        "dash": ("dashboards/inflation-and-labour/", "the inflation and labour dashboard"),
        "sections": [
            ("Two ways to measure the same thing", [
                "The United States has two headline measures of consumer price inflation. The consumer price index, "
                "the CPI, is published by the Bureau of Labor Statistics. The price index for personal consumption "
                "expenditures, the PCE price index, is published by the Bureau of Economic Analysis. Both track what "
                "happens to the prices of the goods and services households buy, and over long periods they move "
                "together. But they are built differently, and the CPI has usually run a little higher.",
            ]),
            ("The CPI", [
                "The CPI is built from prices collected across the country, for a basket of goods and services, "
                "weighted by what households report spending in the Consumer Expenditure Surveys. The headline "
                "series, the CPI for all urban consumers, covers the large majority of the US population. It is "
                "released around the middle of the month after the one it measures, before the PCE index, which is "
                "one reason markets react to it so strongly.",
                "Because it is not revised once published, apart from its seasonal factors, the CPI is used in "
                "contracts and law. Social Security payments are adjusted with a version of it, and the principal of "
                "Treasury Inflation-Protected Securities is indexed to it.",
            ]),
            ("The PCE price index", [
                "The PCE price index is part of the national accounts that also give GDP. It comes out near the end "
                "of the month, in the BEA's personal income and outlays report, and it uses many of the same price "
                "measurements as the CPI. Unlike the CPI, it is revised as better spending data arrive.",
                "It differs from the CPI in three main ways. Its scope is wider: it counts spending made on behalf of "
                "households as well as by them, such as medical care paid for by employers or by Medicare and "
                "Medicaid. Its weights come from business data on what is actually sold rather than from household "
                "surveys, so items carry different importance; housing, in particular, is a much larger share of the "
                "CPI. And its formula updates the weights every period, so when consumers switch from a good whose "
                "price has jumped to a cheaper substitute, the index reflects it.",
            ]),
            ("Why the gap", [
                "Analysts at the BLS and BEA break the difference between the two measures into parts: a formula "
                "effect from the way prices are averaged, a weight effect from the different importance given to each "
                "item, a scope effect from what each index covers, and smaller technical differences. The formula and "
                "weight effects explain most of the gap in most years. When shelter costs are rising quickly, the "
                "heavier housing weight in the CPI tends to widen it.",
            ]),
            ("Headline and core", [
                "Both indices are published in a headline form and a core form that leaves out food and energy. Core "
                "is not a better measure of the cost of living: people eat and drive. It is used because food and "
                "energy prices swing with harvests, weather and conflicts, and those swings tend to reverse. Core "
                "inflation gives a steadier read of the underlying trend that monetary policy can influence.",
            ]),
            ("Why the Fed targets PCE", [
                "The Federal Open Market Committee states its inflation goal as 2% a year, measured by the PCE price "
                "index. Its statement on longer-run goals has said so since 2012. The Fed prefers PCE for its wider "
                "coverage, its weights that adjust as spending shifts, and its consistency with the rest of the "
                "national accounts. In practice markets watch the CPI first, because it comes out first, and read "
                "the PCE figure partly from it: once the CPI and producer prices are out, much of the PCE outcome "
                "can be estimated before the BEA publishes it.",
            ]),
            ("Reading it on the dashboard", [
                "The inflation and labour dashboard plots CPI inflation, the change in the index over twelve months, "
                "alongside the monthly change in payrolls: the two halves of the Fed's mandate, stable prices and "
                "maximum employment. When reading a CPI figure against the Fed's 2% goal, remember the goal is "
                "defined in PCE, which has usually run a little lower.",
            ]),
        ],
        "sources": [
            ("US Bureau of Labor Statistics, Consumer Price Index", "https://www.bls.gov/cpi/"),
            ("US Bureau of Economic Analysis, Personal Consumption Expenditures Price Index",
             "https://www.bea.gov/data/personal-consumption-expenditures-price-index"),
            ("US Bureau of Labor Statistics, Differences between the consumer price index and the personal "
             "consumption expenditures price index, Beyond the Numbers",
             "https://www.bls.gov/opub/btn/volume-2/differences-between-the-consumer-price-index-and-the-personal-consumption-expenditures-price-index.htm"),
            ("Federal Open Market Committee, Statement on Longer-Run Goals and Monetary Policy Strategy",
             "https://www.federalreserve.gov/monetarypolicy/files/FOMC_LongerRunGoals.pdf"),
        ],
    },
    {
        "slug": "credit-spreads",
        "title": "What credit spreads signal",
        "desc": "The extra yield companies pay over the government, and why it widens before trouble.",
        "dash": ("dashboards/credit-spreads/", "the credit spreads dashboard"),
        "sections": [
            ("The extra yield", [
                "When a company borrows by selling bonds, it pays more than the US government does for the same "
                "length of time. The difference between the yield on a corporate bond and the yield on a Treasury of "
                "the same maturity is its credit spread, usually quoted in percentage points or basis points (one "
                "basis point is a hundredth of a percentage point).",
                "Many corporate bonds can be repaid early at the company's choice, which changes how they behave. "
                "The option-adjusted spread, OAS, strips out the value of that option so that bonds with and without "
                "it can be compared. The ICE BofA index spreads shown on the dashboard are option-adjusted.",
            ]),
            ("What the spread pays for", [
                "The spread compensates the lender for several things. The first is expected loss: the chance the "
                "company defaults, times how much of the money is lost if it does. The second is liquidity: corporate "
                "bonds trade less easily than Treasuries, and selling a large position in a hurry can be costly. The "
                "third is a risk premium, the extra return investors demand for holding risk that tends to hurt at "
                "the worst times, because defaults rise together in recessions.",
                "Research has found that expected default losses explain only part of the level of spreads. The rest, "
                "the premium, moves with investors' appetite for risk, which is why spreads can widen sharply even "
                "when few companies are actually defaulting.",
            ]),
            ("Investment grade and high yield", [
                "Rating agencies grade bonds by credit quality. Bonds rated BBB minus or above (Baa3 at one agency) "
                "are investment grade; anything below is high yield, sometimes called junk. Investment grade "
                "companies are mostly large and stable, and their spreads are measured in tenths of a percentage "
                "point to a little over one point in normal times. High yield issuers are smaller or more indebted, "
                "and their spreads are several times larger and far more volatile.",
                "Because defaults are rare among investment grade issuers, their spreads mostly reflect liquidity and "
                "the risk premium. High yield spreads respond more directly to the outlook for defaults, and so to "
                "the economy.",
            ]),
            ("Why markets watch them", [
                "Credit investors are paid back at most in full, so they gain little when things go well and lose a "
                "lot when they go badly. That makes the credit market quick to react to signs of trouble. A sudden "
                "widening in high yield spreads, without a matching move in Treasuries, is often an early sign of "
                "stress.",
                "Academic research supports the signal. A study published in the American Economic Review in 2012 "
                "separated corporate bond spreads into a part explained by expected defaults and an excess bond "
                "premium, the part that reflects lenders' willingness to take risk. A rising excess premium was "
                "followed by weaker investment and output. The Federal Reserve tracks spreads and this premium in "
                "its assessment of financial stability.",
                "Spreads also matter in their own right. They set what companies pay to borrow, so wider spreads "
                "tighten financial conditions even if the Fed has not moved.",
            ]),
            ("What they do not tell you", [
                "Very tight spreads are not a guarantee of safety. They can mean investors are reaching for yield "
                "and being paid little for the risk they take. Index spreads also change with the mix of bonds in "
                "the index: if many lower-rated issuers are upgraded or default and leave, the average moves for "
                "reasons that have little to do with the market. And the spread is only one part of a company's "
                "borrowing cost. When Treasury yields rise, a company can pay much more to borrow even with an "
                "unchanged spread.",
            ]),
            ("Reading it on the dashboard", [
                "The credit spreads dashboard plots the ICE BofA US High Yield and US Corporate (investment grade) "
                "option-adjusted spreads over the chosen range. Look at the direction more than the level, and at "
                "whether high yield is moving faster than investment grade: a widening led by high yield is the "
                "classic sign of rising concern about defaults.",
            ]),
        ],
        "sources": [
            ("FRED, ICE BofA US High Yield Index Option-Adjusted Spread (BAMLH0A0HYM2)",
             "https://fred.stlouisfed.org/series/BAMLH0A0HYM2"),
            ("FRED, ICE BofA US Corporate Index Option-Adjusted Spread (BAMLC0A0CM)",
             "https://fred.stlouisfed.org/series/BAMLC0A0CM"),
            ("Credit Spreads and Business Cycle Fluctuations, American Economic Review, 2012",
             "https://doi.org/10.1257/aer.102.4.1692"),
            ("Board of Governors of the Federal Reserve System, Financial Stability Report",
             "https://www.federalreserve.gov/publications/financial-stability-report.htm"),
        ],
    },
    {
        "slug": "fed-rates",
        "title": "How the Fed sets rates",
        "desc": "Who decides, what the target range is, and how the Fed makes the market follow it.",
        "dash": ("fed-rates/", "Fed & Rates"),
        "sections": [
            ("The mandate", [
                "Congress has given the Federal Reserve two goals for monetary policy: maximum employment and stable "
                "prices, along with moderate long-term interest rates. The Fed has defined stable prices as inflation "
                "of 2% a year, measured by the price index for personal consumption expenditures. Its main tool for "
                "pursuing both goals is the level of short-term interest rates.",
            ]),
            ("Who decides", [
                "Rates are set by the Federal Open Market Committee, the FOMC. It has twelve voting members: the seven "
                "governors of the Federal Reserve Board in Washington, the president of the Federal Reserve Bank of "
                "New York, and four of the other eleven Reserve Bank presidents, who take turns a year at a time. "
                "All twelve Reserve Bank presidents take part in the discussion. The committee holds eight scheduled "
                "meetings a year and can meet in between if it needs to.",
            ]),
            ("What it sets", [
                "The FOMC sets a target range for the federal funds rate, the rate at which banks lend reserves to "
                "each other overnight. The range is a quarter of a percentage point wide, for example 4.25% to 4.50%. "
                "The Federal Reserve Bank of New York publishes the rate actually paid each day, the effective "
                "federal funds rate, calculated from reported overnight loans as a volume-weighted median.",
            ]),
            ("How the market follows it", [
                "The Fed does not order banks to lend at a given rate. Today it steers the market with rates it pays "
                "and charges itself. It pays interest on the reserves banks hold at the Fed. No bank should lend "
                "reserves for much less than it can earn by leaving them at the Fed, so this rate pulls the market "
                "toward the target range. Through its overnight reverse repurchase facility the Fed also borrows "
                "from a wider set of institutions, including money market funds, at a rate that sets a floor under "
                "short-term rates. Banks can borrow from the Fed at the discount window at a rate above the range.",
                "This works because the banking system holds ample reserves. Before 2008 reserves were scarce, and "
                "the Fed hit its target by adding or draining small amounts of reserves each day through open market "
                "operations. Now it moves the rates it administers and the market rate follows.",
            ]),
            ("Decision day", [
                "At the end of each meeting the committee releases a statement, at 2:00 pm New York time, giving the "
                "decision, a short assessment of the economy and how each member voted. The Chair holds a press "
                "conference half an hour later. At four meetings a year, in March, June, September and December, "
                "participants also publish their economic projections, including the dot plot: each participant's "
                "view of the appropriate rate at the end of the next few years, shown as a dot. The dots are "
                "individual views, not a committee plan. Minutes follow three weeks after each meeting.",
            ]),
            ("From the overnight rate to the economy", [
                "A change in the overnight rate reaches the economy through other prices. Bank lending rates and "
                "money market yields move almost at once. Longer rates, such as mortgage rates and corporate bond "
                "yields, move with the expected path of policy, which is why the Fed's guidance about future meetings "
                "can matter as much as the decision itself. Asset prices and the dollar respond too. The effect on "
                "spending, hiring and inflation builds over many months, which is why the Fed has to act on forecasts "
                "rather than on today's data.",
                "The Fed also has its balance sheet. By buying Treasury and mortgage-backed securities it can push "
                "down long-term yields when short-term rates are already near zero, and by letting them mature it "
                "can do the opposite.",
            ]),
            ("Reading it on the dashboard", [
                "The Fed path dashboard turns 30-day federal funds futures into the average overnight rate the market "
                "expects month by month: 100 minus the futures price. A path sloping down prices cuts, one sloping up "
                "prices hikes. The dashed line shows the path at the start of the range, so you can see how "
                "expectations have shifted. Futures include a small risk premium, so the path is a guide to market "
                "expectations, not a forecast of what the committee will do.",
            ]),
        ],
        "sources": [
            ("Board of Governors of the Federal Reserve System, Policy Tools",
             "https://www.federalreserve.gov/monetarypolicy/policytools.htm"),
            ("Board of Governors of the Federal Reserve System, Federal Open Market Committee",
             "https://www.federalreserve.gov/monetarypolicy/fomc.htm"),
            ("Federal Reserve Bank of New York, Effective Federal Funds Rate",
             "https://www.newyorkfed.org/markets/reference-rates/effr"),
            ("Federal Open Market Committee, Statement on Longer-Run Goals and Monetary Policy Strategy",
             "https://www.federalreserve.gov/monetarypolicy/files/FOMC_LongerRunGoals.pdf"),
        ],
    },
]
