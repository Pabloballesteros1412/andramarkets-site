"""Recession watch (recession-watch/). Stub: replaced by the page's own build."""


def pages(site):
    """{output path: page HTML}. site is tools/build_site.py, for shell(), icon() and the loaders."""
    body = f"""<main id="main" class="page">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Recession watch</h1>
      <p class="lede">The indicators most watched for a US recession.</p>
    </header>
  </div>
</main>"""
    return {"recession-watch/": site.shell(title="Recession watch: Andra Markets", desc="The indicators most watched for a US recession.", body=body,
                                  home="../", base="../", path="recession-watch/")}
