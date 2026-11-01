"""Interview simulator (interview-simulator/). Stub: replaced by the page's own build."""


def pages(site):
    """{output path: page HTML}. site is tools/build_site.py, for shell(), icon() and the loaders."""
    body = f"""<main id="main" class="page">
  <div class="wrap">
    <header class="page__head">
      <h1 class="page__title">Interview simulator</h1>
      <p class="lede">A timed mock interview, answered aloud.</p>
    </header>
  </div>
</main>"""
    return {"interview-simulator/": site.shell(title="Interview simulator: Andra Markets", desc="A timed mock interview, answered aloud.", body=body,
                                  home="../", base="../", path="interview-simulator/")}
