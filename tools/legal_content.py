"""Legal notice and privacy policy text for /legal/ and /privacy/.

Each page is a list of (id, heading, html). Text in [square brackets] is a
placeholder the owner fills in; build_site.py marks it with fill(). Keep both
pages in plain English and in line with what the site actually does: when a
cookie, a vendor or the newsletter changes, change the privacy policy too.
Both should be reviewed by a qualified lawyer before the paid tier opens.
"""

LEGAL_UPDATED = "2026-11-01"
PRIVACY_UPDATED = "2026-11-01"

LEGAL = [
    ("publisher", "Who publishes this site",
     "<p>This website is published by Andra Markets, based in Spain. Contact: <a href=\"mailto:andramarkets@gmail.com\">andramarkets@gmail.com</a>.</p>"
     "<p>Andra Markets is a non-commercial publication: it has no income, sells nothing and carries no "
     "advertising, sponsorship or affiliate links. When it starts any economic activity, such as a paid "
     "subscription, this notice will identify the company that runs it, as Article 10 of Spanish Law "
     "34/2002 on information society services and electronic commerce (LSSI) requires.</p>"
     "<p>Andra Markets publishes market research: daily close notes, weekly market reviews, research "
     "reports, dashboards, an economic calendar, interactive tools and educational material.</p>"),

    ("not-advice", "Not investment advice",
     "<p>Everything on this site is general information for educational and informational purposes. "
     "It does not take into account the objectives, financial situation or needs of any person, and it is "
     "not investment, financial, legal, tax or accounting advice.</p>"
     "<p>Nothing on this site is a personal recommendation, or an offer or solicitation to buy or sell any "
     "security, currency, commodity or other financial instrument, or to adopt any investment strategy. "
     "Andra Markets does not answer questions about what any individual should buy, sell or hold.</p>"
     "<p>Andra Markets is not authorised or registered as an investment firm, investment adviser or broker "
     "by the Spanish CNMV, the UK Financial Conduct Authority, the US Securities and Exchange Commission or "
     "any other regulator. Before making an investment decision, consider whether it suits your "
     "circumstances and, if you need advice, speak to an authorised adviser.</p>"),

    ("research", "How to read our research",
     "<p>Each report is dated and states its sources. Reports separate facts (published figures) from "
     "interpretation and opinion. Opinions are those of Andra Markets on the date of publication, may "
     "change without notice, and Andra Markets has no obligation to update a report after it is "
     "published.</p>"
     "<p>Reports are produced with an automated pipeline: the figures are collected from the sources listed "
     "on the <a href=\"../sources/\">data sources</a> page, the text is drafted with the help of a language "
     "model and every figure in it is checked against the session's verified data before publication. "
     "The <a href=\"../methodology/\">methodology</a> explains the process.</p>"
     "<p>Illustrations in research reports may be generated with AI tools; each report says so in its "
     "methodology. They are artwork, not photographs, and do not depict real events.</p>"
     "<p>Interview Prep model answers, Break into Wall Street and the technical training pages are "
     "educational. Lab tools, simulators, backtests and diagrams marked Illustrative are hypothetical and "
     "are not a record of any real portfolio.</p>"),

    ("conflicts", "Conflicts of interest",
     "<p>Andra Markets receives no payment from the companies or issuers it writes about, and publishes no "
     "sponsored research. Where Andra Markets or its operator holds a position in an instrument that a "
     "report discusses specifically, the report says so. Andra Markets does not trade on a report before "
     "it is published.</p>"),

    ("performance", "Past performance and forecasts",
     "<p>Past performance is not a reliable indicator of future results. The value of investments and the "
     "income from them can fall as well as rise, and investors may get back less than they invested. "
     "Changes in exchange rates can affect the value of investments in other currencies.</p>"
     "<p>Market expectations, forecasts and scenarios on this site are not guarantees of future events or "
     "returns.</p>"),

    ("data", "Data, errors and delays",
     "<p>Market and economic data come from third parties, listed on the <a href=\"../sources/\">data "
     "sources</a> page. Figures are not real-time: prices are closing prices or may be delayed, and "
     "economic figures are revised after release. Data may be incomplete, late or wrong, a source may fail, "
     "and the site may show a source's last good figures, with their date, until the next good read.</p>"
     "<p>Andra Markets checks figures carefully but gives no warranty that any content is accurate, "
     "complete or up to date, and the site should not be used for trading decisions. When an error is "
     "found it is corrected as the methodology describes.</p>"),

    ("ip", "Intellectual property",
     "<p>The text, reports, charts, tables, tools, design, the Andra Markets name and the horse mark are the "
     "property of Andra Markets or are used under licence, and are protected by intellectual property law. "
     "&copy; Andra Markets. All rights reserved.</p>"
     "<p>You may read the site, share links to any page and quote short extracts with attribution to Andra "
     "Markets and a link to the source. You may not reproduce, republish, sell or redistribute the content, "
     "scrape it systematically or use it to train machine learning models without written permission.</p>"
     "<p>Third-party data remain the property of their providers. Company names, tickers and logos belong "
     "to their owners and are used only to identify the companies.</p>"),

    ("us", "Users in the United States",
     "<p>Andra Markets is not registered as an investment adviser with the SEC or any state. Its content is "
     "impersonal, general commentary published on a regular schedule for a general audience, and is not "
     "tailored to any reader. Nothing on the site is an offer of securities.</p>"),

    ("uk", "Users in the United Kingdom",
     "<p>Andra Markets is not authorised or regulated by the Financial Conduct Authority. Nothing on this "
     "site is intended as an invitation or inducement to engage in investment activity, and no content is "
     "made available for the purpose of promoting a particular investment.</p>"),

    ("eu", "Users in the European Union",
     "<p>Andra Markets is not an investment firm under MiFID II and is not registered with the CNMV or any "
     "other national competent authority. Where a report contains an opinion on a specific issuer or "
     "instrument, it is prepared with the disclosures the Market Abuse Regulation (EU) No 596/2014 asks of "
     "investment recommendations: who produced it, its date, its sources, the difference between facts and "
     "opinions, and any conflicts of interest.</p>"),

    ("links", "Links to other websites",
     "<p>The site links to third-party websites, such as data publishers and the Andra Markets pages on "
     "LinkedIn and TikTok. It embeds no third-party players or feeds. Andra Markets is not responsible for "
     "the content or practices of other websites, which are governed by their own terms.</p>"),

    ("liability", "Limitation of liability",
     "<p>To the fullest extent permitted by law, Andra Markets is not liable for any loss or damage arising "
     "from the use of, or reliance on, this site or its content, including investment losses. Nothing in "
     "this notice limits liability that cannot be limited by law, or any right you have as a "
     "consumer.</p>"),

    ("law", "Changes and governing law",
     "<p>This notice may be updated; the date of the latest version is shown below. It is governed by "
     "Spanish law. If you are a consumer, you keep the protection of the mandatory laws of the country where "
     "you live and may bring a claim there.</p>"),
]

PRIVACY = [
    ("controller", "Who is responsible",
     "<p>Andra Markets, based in Spain, is responsible for any personal data processed through this site, "
     "under the General Data Protection Regulation (EU) 2016/679 and Spanish Organic Law 3/2018. Contact: "
     "<a href=\"mailto:andramarkets@gmail.com\">andramarkets@gmail.com</a>. The site collects almost no personal data (see below); when that changes, this "
     "policy will give the full identity of the controller first.</p>"),

    ("collect", "What we collect",
     "<p>Very little. The site has no accounts, no analytics, no advertising and no tracking pixels, and "
     "Andra Markets sets no cookies.</p>"
     "<p>The site does not collect email addresses. If a newsletter launches, this policy will name the "
     "newsletter platform and explain how your address is used before any address is collected.</p>"),

    ("storage", "Cookies and storage on your device",
     "<p>Andra Markets sets no cookies. A few features keep a small note in your browser's storage so they "
     "work as you expect. Each one stays on your device, is never sent to us or to anyone else, holds "
     "nothing that identifies you and is used only for the feature you are using:</p>"
     "<ul class=\"ruled\">"
     "<li><b>andra-theme</b> (local storage): the light or dark theme you chose, so the site opens in the "
     "same theme next time.</li>"
     "<li><b>andra-tq-</b> and <b>andra-md-</b> followed by the topic (local storage): your progress on the "
     "practice cards and your best score in the mental maths drill on the technical training pages.</li>"
     "<li><b>andra-sim-games</b>, <b>andra-panic-games</b> and <b>andra-fed-games</b> (local storage): your "
     "last results in the simulators, so you can compare your games.</li>"
     "<li><b>andra-arrive</b> and <b>andra-scene</b> (session storage): where the background animation was "
     "when you moved to another page, so it carries on smoothly. They are deleted when you close the "
     "tab.</li>"
     "</ul>"
     "<p>Storage that is strictly necessary for a service you request is exempt from consent under Article "
     "22.2 of the LSSI, so the site shows no cookie banner. You can clear it in your browser settings at "
     "any time; the site keeps working, and only your theme, progress and results are reset.</p>"),

    ("hosting", "Hosting and service providers",
     "<ul class=\"ruled\">"
     "<li><b>GitHub Pages</b> (GitHub, Inc., United States) serves this site. Like any web server it "
     "processes your IP address and request details to deliver pages and protect the service, under "
     "GitHub's privacy statement.</li>"
     "<li><b>Cloudflare Workers</b> (Cloudflare, Inc., United States) runs the Andra Markets data service "
     "behind the company pages. When you look up a company, the ticker is passed to Finnhub and Financial "
     "Modeling Prep to fetch its figures; no personal data is sent to them. Cloudflare processes your IP "
     "address to deliver the response and protect the service.</li>"
     "</ul>"
     "<p>The site's fonts, scripts and images are served from the site itself, not from third-party "
     "networks, and no third-party player, feed or widget is embedded. Links to LinkedIn and TikTok are "
     "plain links: nothing loads from those services unless you follow one, and then their own policies "
     "apply.</p>"),

    ("basis", "Legal basis, retention and transfers",
     "<p>Server data is processed for the legitimate interest of delivering a secure website, and kept by "
     "the providers above for the periods their own policies set. If you email us, we use your message "
     "only to reply and keep it no longer than needed. Providers in the United States receive data under "
     "the safeguards they offer, such as the EU-US Data Privacy Framework or standard contractual "
     "clauses.</p>"),

    ("rights", "Your rights",
     "<p>If you are in the European Union or the United Kingdom, you have the right to access, correct, "
     "delete, restrict or object to the processing of your personal data, and to data portability. Write "
     "to <a href=\"mailto:andramarkets@gmail.com\">andramarkets@gmail.com</a>. You can also complain to a data protection authority: in Spain the Agencia "
     "Espa&ntilde;ola de Protecci&oacute;n de Datos (aepd.es), in the UK the Information Commissioner's "
     "Office (ico.org.uk), or the authority where you live.</p>"
     "<p>If you are in the United States: Andra Markets does not sell or share personal information and "
     "does not use it for targeted advertising. Residents of states with privacy laws, such as California, "
     "can ask what we hold and ask us to delete it at the same address.</p>"),

    ("children", "Children",
     "<p>The site is not directed at children under 16 and does not knowingly collect their data.</p>"),

    ("changes", "Changes",
     "<p>This policy will change when the site does, for example when the newsletter launches. The date of "
     "the latest version is shown below.</p>"),
]
