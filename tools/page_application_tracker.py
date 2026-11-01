"""Application tracker (application-tracker/). Stub: replaced by the page's own build."""


def pages(site):
    """{output path: page HTML}. site is tools/build_site.py, for shell(), icon() and the loaders."""
    body = f"""<main id="main" class="page">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Application tracker</h1>
      <p class="lede">Your applications, deadlines and contacts, kept in your browser.</p>
    </header>
  </div>
</main>"""
    return {"application-tracker/": site.shell(title="Application tracker: Andra Markets", desc="Your applications, deadlines and contacts, kept in your browser.", body=body,
                                  home="../", base="../", path="application-tracker/")}
