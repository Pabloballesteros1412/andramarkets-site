"""Market history (market-history/). Stub: replaced by the page's own build."""


def pages(site):
    """{output path: page HTML}. site is tools/build_site.py, for shell(), icon() and the loaders."""
    body = f"""<main id="main" class="page">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Market history</h1>
      <p class="lede">The S&amp;P 500 since 1928, episode by episode.</p>
    </header>
  </div>
</main>"""
    return {"market-history/": site.shell(title="Market history: Andra Markets", desc="The S&amp;P 500 since 1928, episode by episode.", body=body,
                                  home="../", base="../", path="market-history/")}
