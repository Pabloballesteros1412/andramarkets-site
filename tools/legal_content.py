"""Legal notice and privacy policy text for /legal/ and /privacy/.

Each page is a list of (id, heading, html). Text in [square brackets] is a
placeholder the owner fills in; build_site.py marks it with fill(). Keep both
pages in plain English and in line with what the site actually does: when a
cookie, a vendor or the newsletter changes, change the privacy policy too.
Both should be reviewed by a qualified lawyer before the paid tier opens.
"""

LEGAL_UPDATED = "2026-11-02"
PRIVACY_UPDATED = "2026-11-11"

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
     "on the <a href=\"../sources/\">data sources</a> page, the text is drafted by a language model and "
     "every figure in it is checked against the session's verified data before publication. Every page "
     "whose text is machine-drafted says so where it is read, as the EU Artificial Intelligence Act "
     "(Regulation (EU) 2024/1689, Article 50) requires. The <a href=\"../methodology/\">methodology</a> "
     "explains the process.</p>"
     "<p>Illustrations in research reports may be generated with AI tools; each report says so in its "
     "methodology. They are artwork, not photographs, and do not depict real events.</p>"
     "<p>Interview Prep model answers, Break into Wall Street and the technical training pages are "
     "educational. Lab tools, simulators, backtests and diagrams marked Illustrative are hypothetical and "
     "are not a record of any real portfolio.</p>"),

    ("conflicts", "Conflicts of interest",
     "<p>Andra Markets receives no payment from anyone: not from the companies or issuers it writes about, "
     "nor from any data provider, broker or platform, and it publishes no sponsored research.</p>"
     "<p>Neither Andra Markets nor its operator holds a position in any instrument the reports discuss "
     "specifically. If that ever changes, the report concerned will say so clearly, and no one at Andra "
     "Markets will trade on a report before it is published.</p>"),

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
     "other national competent authority. Its content is market commentary and education, not investment "
     "recommendations under the Market Abuse Regulation (EU) No 596/2014: it does not tell readers to buy, "
     "sell or hold any instrument, sets no price targets and gives no view on what a specific instrument "
     "is worth or where its price will go. If Andra Markets ever publishes such a recommendation, it will "
     "carry every disclosure that Regulation and Delegated Regulation (EU) 2016/958 require, including the "
     "identity of the person who produced it.</p>"),

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
     "<p>Andra Markets is run by Pablo Ballesteros S&aacute;nchez, based in Spain, who is the controller of "
     "any personal data processed through this site under the General Data Protection Regulation (EU) "
     "2016/679 and Spanish Organic Law 3/2018. Contact: "
     "<a href=\"mailto:andramarkets@gmail.com\">andramarkets@gmail.com</a>. The site collects almost no "
     "personal data (see below).</p>"),

    ("collect", "What we collect",
     "<p>Very little. The site has no accounts, no advertising and no tracking pixels, and Andra Markets "
     "sets no cookies.</p>"
     "<p>The site does not collect email addresses. If a newsletter launches, this policy will name the "
     "newsletter platform and explain how your address is used before any address is collected.</p>"),

    ("storage", "Cookies and storage on your device",
     "<p>Andra Markets sets no cookies. A few features keep a small note in your browser's storage so they "
     "work as you expect. Each one stays on your device, is never sent to us or to anyone else and is used "
     "only for the feature you are using. Only the Application tracker can hold personal details, and only "
     "those you type into it:</p>"
     "<ul class=\"ruled\">"
     "<li><b>andra-tq-</b> and <b>andra-md-</b> followed by the topic (local storage): your progress on the "
     "practice cards and your best score in the mental maths drill on the technical training pages.</li>"
     "<li><b>andra-sim-games</b>, <b>andra-panic-games</b> and <b>andra-fed-games</b> (local storage): your "
     "last results in the simulators, so you can compare your games.</li>"
     "<li><b>andra-isim</b> (local storage): your progress and results in the Interview simulator, so you "
     "can resume an interview and see how you did by topic.</li>"
     "<li><b>andra-tool-map</b> (local storage): where you left the tools on a Tools section's map, if you "
     "moved them. A double click on that map removes it.</li>"
     "<li><b>andra-fund</b> (local storage): the paper fund you run in Your fund: its name, cash, positions, "
     "pending orders, trades and daily values. You can export it to a file, import that file again, or delete "
     "it by starting a new fund or in your browser.</li>"
     "<li><b>andra-tracker</b> (local storage): the applications you add to the Application tracker, with "
     "their dates, status, next steps, notes and any contacts you type in. You can export them to a file, "
     "import that file again, or delete them in the tracker or in your browser.</li>"
     "<li><b>andra-arrive</b>, <b>andra-move</b> and <b>andra-opened</b> (session storage): how you moved to "
     "another page and whether the homepage's opening has already played, so pages follow one another "
     "smoothly and the opening is not repeated in full. They are deleted when you close the tab.</li>"
     "</ul>"
     "<p>Storage that is strictly necessary for a service you request is exempt from consent under Article "
     "22.2 of the LSSI, so the site shows no cookie banner. You can clear it in your browser settings at "
     "any time; the site keeps working, and only your theme, progress, results and tracker entries are "
     "reset.</p>"),

    ("hosting", "Hosting and service providers",
     "<ul class=\"ruled\">"
     "<li><b>GitHub Pages</b> (GitHub, Inc., United States) serves this site. Like any web server it "
     "processes your IP address and request details to deliver pages and protect the service, under "
     "GitHub's privacy statement.</li>"
     "<li><b>Gmail</b> (Google) hosts the Andra Markets mailbox: if you write to us, your message and "
     "address are stored there, under Google's privacy policy.</li>"
     "<li><b>Cloudflare Workers</b> (Cloudflare, Inc., United States) runs the Andra Markets data service "
     "behind the company pages. When you look up a company, the ticker is passed to Finnhub and Financial "
     "Modeling Prep to fetch its figures; no personal data is sent to them. Cloudflare processes your IP "
     "address to deliver the response and protect the service.</li>"
     "</ul>"
     "<p>Apart from the services named here, nothing loads from third-party networks: the site's fonts, "
     "scripts and images are served from the site itself, and no third-party player, feed or widget is "
     "embedded. Links to LinkedIn and TikTok are plain links: nothing loads from those services unless you "
     "follow one, and then their own policies apply.</p>"),

    ("basis", "Legal basis, retention and transfers",
     "<p>Server data is processed for the legitimate interest of delivering a secure website (Article "
     "6(1)(f) GDPR), and kept by the providers above for the periods their own policies set. If you email "
     "us, your message is used only to reply, on the same legitimate interest of answering you, and is "
     "deleted within 12 months of the last message, unless it is needed for a legal claim. Writing to us is "
     "voluntary: it is the only way you give us personal data. No decision about you is made by automated "
     "means and no profile of you is built. Providers in the United States receive data under the "
     "safeguards they offer, such as the EU-US Data Privacy Framework or standard contractual "
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


# Cloudflare Web Analytics, described only when the pages carry its beacon (build_site.py,
# ANALYTICS_TOKEN): section id -> (the text it goes right after, the text). The rest of the
# policy must stay true with and without it; the build stops if an anchor is gone.
PRIVACY_ANALYTICS = {
    "collect": (
        "sets no cookies.</p>",
        "<p>The site counts its visits with Cloudflare Web Analytics, which sets no cookies and keeps "
        "nothing in your browser, so it cannot tell that two visits came from the same person. We see only "
        "totals, such as how many times a page was viewed, which site visitors came from and from which "
        "countries, never who you are.</p>"),
    "hosting": (
        "deliver the response and protect the service.</li>",
        "<li><b>Cloudflare Web Analytics</b> (Cloudflare, Inc., United States) counts the site's visits. When "
        "a page opens, a small script from Cloudflare sends it the page's address, the address of the page "
        "you came from, your browser and device type and how long the page took to load. Cloudflare uses "
        "your IP address to receive this and to tell which country the visit came from; it states that it "
        "does not use cookies, your IP address or any other identifier to recognise you or follow you "
        "across visits or sites.</li>"),
    "basis": (
        "for the periods their own policies set.",
        " The count of visits rests on the same basis: the legitimate interest of knowing, in totals, how "
        "many people read the site and which pages."),
}
