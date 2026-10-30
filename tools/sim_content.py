"""The episodes the Trading Simulator reveals at the end of a game.

Each episode covers a run of months, from its first month to its last, and the
episodes cover every month since 1928 without gaps. A game names the episode
its two years overlap most. Figures are S&P 500 price moves, rounded and given
as "about"; text in the Andra Markets voice: what happened, plainly, no
hindsight lessons. Links point at Learn explainers and dashboards on the site
(relative to the site root).
"""

FED = ("Learn: How the Fed sets rates", "learn/fed-rates/")
CPI = ("Learn: CPI vs PCE", "learn/cpi-vs-pce/")
CURVE = ("Learn: How to read the yield curve", "learn/yield-curve/")
VIX = ("Learn: What moves the VIX", "learn/vix/")
CREDIT = ("Learn: What credit spreads signal", "learn/credit-spreads/")
EARN = ("Learn: How earnings season works", "learn/earnings-season/")
D_COMMOD = ("Dashboard: Commodities", "dashboards/commodities/")
D_SECTORS = ("Dashboard: Sector heatmap", "dashboards/sector-heatmap/")
D_GLOBAL = ("Dashboard: Global indices", "dashboards/global-indices/")
D_INFL = ("Dashboard: Inflation and labour", "dashboards/inflation-and-labour/")

EPISODES = [
    ("1928-01", "1929-10", "the great crash",
     "Shares rose through 1928 and the summer of 1929 on cheap broker loans: investors could buy stock with as little "
     "as 10% down. The market peaked in September 1929. In late October it broke: Black Thursday, then Black Monday "
     "and Black Tuesday, two of the worst days on record, as margin calls forced selling into a falling market.",
     [FED, CREDIT]),
    ("1929-11", "1932-07", "the Great Depression",
     "After the crash the fall did not stop. Banks failed by the thousand, the money supply shrank, prices fell and "
     "unemployment passed 20%. From its 1929 peak to the summer of 1932 the index lost about 86%, the deepest bear "
     "market in its history. Bear market rallies of 20% and more came and went along the way.",
     [FED, CREDIT]),
    ("1932-08", "1936-12", "the New Deal recovery",
     "From the 1932 low the index more than doubled within a year. Roosevelt took office in March 1933, closed the "
     "banks for a week, took the dollar off gold and launched the New Deal. Recovery was uneven, but by 1936 the "
     "market had more than tripled from its low, still far below its 1929 peak.",
     [FED, CPI]),
    ("1937-01", "1938-12", "the recession of 1937",
     "With recovery under way, policy tightened: the Fed raised bank reserve requirements, the Treasury held back "
     "gold and the budget was cut. The economy fell back into a sharp recession, and from March 1937 to March 1938 "
     "the index lost roughly half its value.",
     [FED, CURVE]),
    ("1939-01", "1942-04", "war in Europe and Pearl Harbor",
     "Germany invaded Poland in September 1939 and France fell in June 1940. The United States entered the war after "
     "Pearl Harbor in December 1941. The index drifted lower for three years and touched its low in April 1942, as "
     "the war in the Pacific went badly.",
     [D_GLOBAL]),
    ("1942-05", "1946-04", "the wartime rally",
     "From the spring of 1942 the index rose steadily as the course of the war turned. Prices and interest rates were "
     "held down by controls and the Fed's cap on Treasury yields, while war production lifted profits. By 1946 the "
     "market had more than doubled from its low.",
     [FED, CURVE]),
    ("1946-05", "1949-06", "the post-war slump",
     "Peace brought the end of price controls, a burst of inflation and fear of a return to depression. The index "
     "fell sharply in the second half of 1946 and then went sideways for three years, through the 1948 election and "
     "a mild recession in 1949.",
     [CPI, D_INFL]),
    ("1949-07", "1953-08", "the Korean War years",
     "A long bull market began in mid-1949. The Korean War broke out in June 1950 and briefly knocked shares down, "
     "but profits were strong. In 1951 the Fed won its independence from the Treasury's cap on bond yields, the "
     "Treasury-Fed Accord.",
     [FED, CURVE]),
    ("1953-09", "1956-12", "the fifties boom",
     "Victory in Korea, low inflation and a consumer boom lifted the market. The index rose about 45% in 1954 alone "
     "and finally passed its 1929 peak that year, a quarter of a century after the crash.",
     [EARN, D_SECTORS]),
    ("1957-01", "1958-12", "Sputnik and the 1957 recession",
     "The Soviet launch of Sputnik in October 1957 came as the economy slid into a sharp recession. The index fell "
     "about 20% from its 1956 high, then recovered fast: 1958 was one of the best years of the decade.",
     [FED]),
    ("1959-01", "1961-12", "the Kennedy years begin",
     "A short recession in 1960 gave way to a long expansion. John F. Kennedy took office in January 1961 and growth "
     "stocks, the electronics names of the day, led a strong market.",
     [EARN]),
    ("1962-01", "1962-12", "the 1962 crash and the Cuban missile crisis",
     "Expensive growth stocks broke in the spring of 1962. On 28 May the index fell about 7% in a day, then the worst "
     "since 1929. It bottomed in June, about a quarter below its high, and was rattled again by the Cuban missile "
     "crisis in October before recovering.",
     [VIX]),
    ("1963-01", "1965-12", "the go-go years",
     "Kennedy's assassination in November 1963 caused a one-day fall; the tax cuts that followed under Lyndon Johnson "
     "supported a long rise. Inflation stayed low, growth was strong and a new class of fast-trading funds became "
     "the talk of Wall Street.",
     [EARN, D_SECTORS]),
    ("1966-01", "1968-11", "the credit crunch and Vietnam",
     "With the Vietnam War and the Great Society spending at once, inflation began to climb. The Fed tightened in "
     "1966, credit dried up and the index fell about 22%. It recovered through 1967 and 1968, a year of political "
     "turmoil at home.",
     [FED, CREDIT]),
    ("1968-12", "1970-06", "the 1969 to 1970 bear market",
     "With inflation near 6%, the Fed raised rates hard. The index fell about 36% from late 1968 to May 1970. The "
     "collapse of the Penn Central railroad in June 1970, then the largest US bankruptcy, froze the commercial paper "
     "market until the Fed stepped in.",
     [FED, CREDIT]),
    ("1970-07", "1972-12", "the Nixon shock and the Nifty Fifty",
     "In August 1971 Richard Nixon closed the gold window and imposed wage and price controls, ending the Bretton "
     "Woods system. The market rallied, led by fifty large growth stocks, the Nifty Fifty, which traded at very high "
     "valuations by the end of 1972.",
     [CPI, D_COMMOD]),
    ("1973-01", "1974-12", "the oil shock bear market",
     "The S&P 500 entered 1973 near a record, carried by the Nifty Fifty. Then inflation climbed toward 12% and in "
     "October 1973 the Arab oil embargo sent the price of crude up about fourfold. With Watergate on top, the index "
     "fell about 48% from January 1973 to October 1974, its worst fall since the 1930s. It did not regain its old "
     "high until 1980.",
     [CPI, D_COMMOD]),
    ("1975-01", "1976-12", "the recovery of 1975",
     "From the October 1974 low the market rebounded hard: the index rose more than 30% in 1975 as inflation eased "
     "and the Fed cut rates. Unemployment stayed high and New York City came close to default.",
     [FED, CPI]),
    ("1977-01", "1979-12", "stagflation",
     "Inflation came back, the dollar weakened and the second oil shock followed the Iranian revolution in 1979. "
     "Shares went nowhere in real terms. In October 1979 Paul Volcker's Fed switched to targeting the money supply "
     "and let interest rates rise as far as needed.",
     [CPI, FED, D_COMMOD]),
    ("1980-01", "1982-07", "the Volcker squeeze",
     "To break inflation the Fed pushed short-term rates near 20%. The economy fell into recession in 1980 and again "
     "from 1981 to 1982. The index fell about 27% from late 1980 to August 1982, while bond yields reached the "
     "highest levels in US history.",
     [FED, CURVE]),
    ("1982-08", "1986-12", "the start of the great bull market",
     "With inflation falling, the Fed eased in the summer of 1982 and Mexico's debt crisis was contained. The index "
     "began one of its longest rises. Falling rates, tax cuts and a wave of takeovers drove it on; the Plaza Accord "
     "of 1985 brought the dollar down.",
     [FED, CURVE]),
    ("1987-01", "1988-12", "Black Monday",
     "The market rose about a third in the first eight months of 1987 as bond yields climbed. On Monday 19 October "
     "1987 the index fell about 20% in a single day, still its largest daily fall. Portfolio insurance selling "
     "swamped buyers. The Fed promised liquidity, and the economy carried on: the index ended 1987 slightly up.",
     [VIX, FED]),
    ("1989-01", "1991-12", "the savings and loan crisis and the Gulf War",
     "Hundreds of savings and loan banks failed and the junk bond market collapsed. Iraq invaded Kuwait in August "
     "1990, oil prices doubled and the US entered recession; the index fell about 20%. It recovered quickly once the "
     "Gulf War began in January 1991.",
     [CREDIT, D_COMMOD]),
    ("1992-01", "1994-12", "the 1994 bond rout",
     "A slow recovery and low rates gave way to a surprise: in February 1994 the Fed began to raise rates and doubled "
     "them within a year. Bond prices fell hard worldwide. Shares held up better, ending 1994 roughly flat.",
     [FED, CURVE]),
    ("1995-01", "1997-12", "the mid-nineties bull market",
     "With inflation tame and a soft landing achieved, the index rose more than 30% in 1995 and kept going. Alan "
     "Greenspan's warning of irrational exuberance in December 1996 barely slowed it. The Asian financial crisis in "
     "1997 caused a sharp one-day fall in October.",
     [FED, EARN]),
    ("1998-01", "2000-02", "LTCM and the dot-com mania",
     "Russia defaulted in August 1998 and the hedge fund Long-Term Capital Management had to be rescued; the index "
     "fell about 19% in weeks. The Fed cut rates three times and technology shares took off. By early 2000 internet "
     "companies with no profits were valued in the billions.",
     [CREDIT, D_SECTORS]),
    ("2000-03", "2002-12", "the dot-com bust",
     "The technology bubble burst in March 2000. A recession followed in 2001, then the attacks of 11 September and "
     "a run of accounting scandals, Enron and WorldCom among them. The index fell about 49% from March 2000 to "
     "October 2002; the Nasdaq lost almost four fifths.",
     [EARN, D_SECTORS]),
    ("2003-01", "2007-06", "the mid-2000s expansion",
     "The invasion of Iraq in March 2003 marked the low for many markets. Low interest rates fed a housing boom and "
     "easy credit; the index rose steadily for four years and volatility fell to unusually low levels.",
     [VIX, CREDIT]),
    ("2007-07", "2009-06", "the global financial crisis",
     "Losses on US subprime mortgages spread through the banks from the summer of 2007. Bear Stearns was rescued in "
     "March 2008 and Lehman Brothers failed in September. The index fell about 57% from October 2007 to March 2009, "
     "the worst bear market since the Depression, before rates near zero and bank rescues turned it.",
     [CREDIT, VIX, FED]),
    ("2009-07", "2012-12", "the euro crisis years",
     "The recovery from 2009 was interrupted by the flash crash of May 2010, Greece's debt crisis and, in August 2011, "
     "the loss of the US AAA credit rating; the index fell nearly 20% that summer. The ECB's promise in 2012 to do "
     "whatever it takes calmed Europe.",
     [CREDIT, D_GLOBAL]),
    ("2013-01", "2015-12", "the taper tantrum",
     "Quantitative easing lifted shares about 30% in 2013, despite a jump in bond yields when the Fed said it would "
     "slow its bond buying. In August 2015 China's devaluation of the yuan caused a sharp, brief fall. The Fed raised "
     "rates for the first time in nearly a decade that December.",
     [FED, CURVE]),
    ("2016-01", "2017-12", "Brexit and the reflation trade",
     "Oil's fall and fears about China shook markets in early 2016. The UK voted to leave the EU in June. After the "
     "US election in November, shares rose on hopes of tax cuts, and 2017 was one of the calmest years on record: "
     "the index never fell more than 3% from its high.",
     [VIX, D_GLOBAL]),
    ("2018-01", "2019-12", "Volmageddon and the Fed pivot",
     "In February 2018 a spike in volatility wiped out funds that had bet against it. Trade tensions with China and "
     "Fed rate rises pushed the index down almost 20% by Christmas Eve 2018. The Fed paused, then cut three times in "
     "2019, and shares hit new highs.",
     [VIX, FED]),
    ("2020-01", "2021-12", "the Covid crash and recovery",
     "As Covid-19 spread, the index fell about 34% in five weeks to 23 March 2020, the fastest bear market on record. "
     "Rates near zero, huge Fed bond buying and government support turned it: the index had recovered all its "
     "losses by August and kept rising through 2021.",
     [FED, VIX]),
    ("2022-01", "2023-12", "inflation and the fastest rate rises in decades",
     "Inflation passed 9% in 2022 and the Fed raised rates from near zero to above 5% in little more than a year. "
     "The index fell about 25% to October 2022 as stocks and bonds dropped together. In 2023 bank failures in March "
     "were contained, and a rally in AI-linked shares lifted the market.",
     [FED, CPI, CURVE]),
    ("2024-01", "2099-12", "the AI boom and the tariff shock",
     "A handful of large technology companies building AI led the index to repeated records in 2024. In April 2025 "
     "broad US tariffs set off one of the sharpest sell-offs since 2020, taking the index nearly 20% below its high, "
     "before it recovered to new records.",
     [D_SECTORS, EARN]),
]

# The Nikkei 225, for the Trading Simulator and the Panic Test on Japan.
EPISODES_JP = [
    ("1965-01", "1972-12", "the high-growth years",
     "Japan's economy grew close to 10% a year, led by exports of steel, ships, cars and electronics. A securities "
     "slump in 1965 forced a central bank rescue of Yamaichi Securities, then shares rose with the boom, fast in "
     "1972.",
     [D_GLOBAL]),
    ("1973-01", "1974-12", "the oil shock",
     "Japan imported almost all its oil. When the 1973 embargo quadrupled the price of crude, consumer prices rose "
     "more than 20% in a year and the economy shrank in 1974 for the first time since the war. The Nikkei fell "
     "sharply from its early 1973 high.",
     [CPI, D_COMMOD]),
    ("1975-01", "1985-08", "the export boom",
     "Japanese industry adapted to dear oil faster than most and won market share around the world. Inflation came "
     "down and the Nikkei rose steadily through the decade, as Japan became the world's second-largest economy.",
     [D_GLOBAL]),
    ("1985-09", "1989-12", "the bubble economy",
     "The Plaza Accord of September 1985 drove the yen up sharply. To cushion exporters the Bank of Japan cut its "
     "rate to 2.5% in 1987, and cheap credit poured into shares and land. The Nikkei tripled and peaked near 38,916 "
     "on 29 December 1989.",
     [FED, CREDIT]),
    ("1990-01", "1992-12", "the bubble bursts",
     "The Bank of Japan raised rates to cool land prices, and the market broke at once. By August 1992 the Nikkei "
     "had lost more than half its value, and banks were left with loans secured on land worth far less than they "
     "had lent.",
     [FED, CREDIT]),
    ("1993-01", "1996-12", "the lost decade begins",
     "Growth stalled under the weight of bad loans. The yen hit a record near 80 to the dollar in April 1995, the "
     "year the Kobe earthquake struck. The Nikkei went sideways, far below its peak.",
     [CREDIT]),
    ("1997-01", "1999-12", "the banking crisis",
     "In November 1997 Yamaichi Securities and Hokkaido Takushoku Bank failed, and in 1998 the government took over "
     "Long-Term Credit Bank of Japan. In February 1999 the Bank of Japan cut its rate to zero, the first major "
     "central bank to do so.",
     [CREDIT, FED]),
    ("2000-01", "2003-04", "the 2003 low",
     "The global technology bust and a return of deflation pushed the Nikkei down again. In April 2003 it touched "
     "about 7,600, roughly 80% below its 1989 peak.",
     [D_SECTORS]),
    ("2003-05", "2007-06", "the Koizumi recovery",
     "The rescue of Resona Bank in May 2003 marked the turn. Bank clean-ups, reforms under Junichiro Koizumi and "
     "demand from China lifted profits, and the Nikkei more than doubled by 2007.",
     [D_GLOBAL]),
    ("2007-07", "2009-03", "the global financial crisis",
     "Japan's banks had little exposure to US mortgages, but exports collapsed as world trade froze. The Nikkei "
     "fell to about 7,050 in March 2009, its lowest since 1982.",
     [CREDIT, VIX]),
    ("2009-04", "2012-10", "the tsunami and the strong yen",
     "The yen climbed as investors sought safety. In March 2011 the Tohoku earthquake and tsunami killed nearly "
     "20,000 people and caused the Fukushima nuclear disaster; the Nikkei fell about 18% in two days. The yen "
     "reached a record near 76 to the dollar that year.",
     [D_GLOBAL]),
    ("2012-11", "2019-12", "Abenomics",
     "Shinzo Abe won the December 2012 election promising to end deflation. The Bank of Japan under Haruhiko "
     "Kuroda launched massive bond buying in April 2013, the yen weakened and the Nikkei more than doubled. Rates "
     "went negative in 2016.",
     [FED, D_GLOBAL]),
    ("2020-01", "2022-12", "Covid and the weak yen",
     "The Nikkei fell about 30% as Covid-19 spread in early 2020, then recovered with the world's markets. In 2022 "
     "the Bank of Japan kept rates near zero while others raised theirs, and the yen fell to its weakest in decades.",
     [FED, D_GLOBAL]),
    ("2023-01", "2099-12", "back to the 1989 high",
     "Weak yen, record profits and pressure on companies to reward shareholders drew investors back. In February "
     "2024 the Nikkei passed its 1989 record for the first time in 34 years. The Bank of Japan ended negative rates "
     "in March 2024; on 5 August 2024 the index fell about 12% in a day, its worst since 1987.",
     [FED, D_GLOBAL]),
]

# The Euro Stoxx 50, whose history on Yahoo starts in 2007.
EPISODES_EU = [
    ("2007-01", "2009-03", "the global financial crisis",
     "European banks had bought heavily into US mortgage debt. From its 2007 high the Euro Stoxx 50 lost about 60% "
     "by March 2009, as banks were rescued across the continent and the euro area fell into deep recession.",
     [CREDIT, VIX]),
    ("2009-04", "2010-12", "Greece and the first bailouts",
     "Markets rebounded in 2009 until Greece revealed a far larger deficit than reported. The euro area and the IMF "
     "lent to Greece in May 2010 and to Ireland in November, and the question became which country would be next.",
     [CREDIT, D_GLOBAL]),
    ("2011-01", "2012-12", "the euro crisis",
     "Portugal needed a rescue in 2011 and the bond yields of Spain and Italy soared; the index fell about a third "
     "that year. In July 2012 Mario Draghi said the ECB would do whatever it takes to preserve the euro, and the "
     "panic began to ease.",
     [CREDIT, FED]),
    ("2013-01", "2015-12", "the ECB goes negative",
     "With inflation close to zero, the ECB cut its deposit rate below zero in June 2014 and began buying government "
     "bonds in January 2015. Greece came close to leaving the euro that summer.",
     [FED, CURVE]),
    ("2016-01", "2019-12", "Brexit and slow growth",
     "The United Kingdom voted to leave the European Union in June 2016. Growth picked up in 2017, then trade "
     "tensions and a slowdown in German industry weighed on European shares in 2018.",
     [D_GLOBAL]),
    ("2020-01", "2021-12", "Covid",
     "Europe was the first region after China to lock down. The index fell close to 40% in a month to March 2020, "
     "before the ECB's emergency bond buying and the EU's joint recovery fund supported a rebound.",
     [FED, VIX]),
    ("2022-01", "2023-12", "war and the energy shock",
     "Russia invaded Ukraine in February 2022 and gas prices soared. Euro area inflation passed 10% and the ECB "
     "raised its deposit rate from below zero to 4% by September 2023.",
     [CPI, FED, D_COMMOD]),
    ("2024-01", "2099-12", "rate cuts and tariffs",
     "The ECB began cutting rates in June 2024 as inflation fell back. In April 2025 broad US tariffs shook markets, "
     "and plans for higher defence spending in Europe lifted the shares of its industrial companies.",
     [FED, D_GLOBAL]),
]

MARKET_EPISODES = {"sp500": EPISODES, "nasdaq": EPISODES, "stoxx50": EPISODES_EU, "nikkei": EPISODES_JP}
