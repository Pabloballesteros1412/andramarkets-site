"""Firms (firms/). Stub: replaced by the page's own build."""


def pages(site):
    """{output path: page HTML}. site is tools/build_site.py, for shell(), icon() and the loaders."""
    body = f"""<main id="main" class="page">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Firms</h1>
      <p class="lede">The banks, boutiques, asset managers, hedge funds and trading firms that hire students.</p>
    </header>
  </div>
</main>"""
    return {"firms/": site.shell(title="Firms: Andra Markets", desc="The banks, boutiques, asset managers, hedge funds and trading firms that hire students.", body=body,
                                  home="../", base="../", path="firms/")}
