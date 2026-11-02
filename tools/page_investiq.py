"""InvestIQ (investiq/): one page presenting InvestIQ, an independent product run by a
third party, not by Andra Markets. Owner-approved sketch, 2 Nov 2026: the name, a short text,
InvestIQ's own 58-second video and a button to its website, centred above 960px.

The video is served from the site itself (assets/investiq.mp4, its poster
assets/investiq-poster.jpg), never embedded from a video platform, so the page loads
nothing from a third party and sets no cookie (the site's Content Security Policy
would block a platform's player anyway). It does not play by itself and is fetched
only when the reader presses play.

The text says only what the video shows. The line under the button says who runs
InvestIQ, so the page reads as a promotion of InvestIQ on its behalf (LSSI article 20)
and never as Andra Markets research.
"""

URL = "https://www.getinvestiq.com/"

# What the video shows, in order, for readers who cannot see it (read by screen readers,
# not shown). Its text, as it appears on screen.
VIDEO_TEXT = (
    "Earnings are out. You're wondering what it means. You read endless filings, spreadsheets "
    "and headlines, and you still don't know. Wall Street has a research team. Now you do too: "
    "InvestIQ, your AI equity research team. Understand any company in minutes, with eight "
    "research modules. Four analysts stress-test your thesis, and you make the call. It writes "
    "you a full report and cites every claim. It reviews your whole portfolio, holding by "
    "holding. And it works right inside Claude, ChatGPT and Cursor. The research desk you never "
    "had. No noise. No guesswork. Just research. getinvestiq.com: free, no credit card."
)


def pages(site):
    """{output path: page HTML}. site is tools/build_site.py, for shell(), icon() and ver()."""
    body = f"""<main id="main" class="page iq">
  <div class="wrap">
    <header class="page__head iq__head">
      <h1 class="page__title">InvestIQ</h1>
      <p class="lede">An AI equity research team. Ask about a company and it reads the filings, works through eight research modules, puts the bull and the bear case side by side and writes you a full report that cites its sources. The call stays yours.</p>
    </header>
    <div class="iq__video">
      <video controls playsinline preload="none" width="848" height="480"
        poster="../assets/investiq-poster.jpg?v={site.ver("investiq-poster.jpg")}"
        aria-label="InvestIQ, a 58-second video" aria-describedby="iq-video-text">
        <source src="../assets/investiq.mp4?v={site.ver("investiq.mp4")}" type="video/mp4">
        <a href="../assets/investiq.mp4">Watch the InvestIQ video</a>
      </video>
      <p class="visually-hidden" id="iq-video-text">{VIDEO_TEXT}</p>
    </div>
    <p class="iq__cta"><a class="btn" href="{URL}" target="_blank" rel="noopener">Visit InvestIQ{site.icon("arrow-up-right")}</a></p>
    <p class="iq__note">InvestIQ is an independent product, not run by Andra Markets. It is free to start. Nothing on this page is investment advice.</p>
  </div>
</main>"""
    return {"investiq/": site.shell(
        title="InvestIQ: Andra Markets",
        desc="InvestIQ, an independent AI equity research product: what it does, "
             "a 58-second video and a link to its website.",
        body=body, home="../", base="../", path="investiq/")}
