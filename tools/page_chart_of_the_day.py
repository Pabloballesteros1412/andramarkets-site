"""Chart of the day (chart-of-the-day/). Stub: replaced by the page's own build."""


def pages(site):
    """{output path: page HTML}. site is tools/build_site.py, for shell(), icon() and the loaders."""
    body = f"""<main id="main" class="page">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Chart of the day</h1>
      <p class="lede">One chart from each session's close note.</p>
    </header>
  </div>
</main>"""
    return {"chart-of-the-day/": site.shell(title="Chart of the day: Andra Markets", desc="One chart from each session's close note.", body=body,
                                  home="../", base="../", path="chart-of-the-day/")}
