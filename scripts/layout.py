"""Shared page shell: head, nav, footer.

Every page is generated through this, so the chrome cannot drift between
hand-written and generated pages -- there are no hand-written pages.
"""

import html

ARXIV_ID = "arXiv:XXXX.XXXXX"
ARXIV_URL = "https://arxiv.org/abs/XXXX.XXXXX"
REPO_URL = "https://github.com/ki-smile/post-training-taxonomy"
SITE_TITLE = "Post-Training Adaptation Taxonomy"

NAV = [
    ("Concepts", "/concepts/"),
    ("Explorer", "/explorer/"),
    ("Classify", "/wizard/"),
    ("Compare", "/compare/"),
    ("Terms", "/disambiguate/"),
    ("Map", "/map/"),
    ("Why it matters", "/ambiguity/"),
    ("Governance", "/governance/"),
    ("Data", "/data/"),
    ("Glossary", "/glossary/"),
]

DISCLAIMER = (
    "This taxonomy supplies technical vocabulary for describing model "
    "changes. It is not legal advice and does not determine whether a change "
    "is a substantial modification, a significant change, or a reportable "
    "device change. Those determinations rest with manufacturers, regulators, "
    "and notified or auditing bodies under the applicable framework."
)


def esc(s):
    return html.escape(str(s), quote=True)


def page(title, body, *, depth=1, description="", current=None, scripts=()):
    """Render a complete document.

    `depth` is how many directories below docs/ the page sits, so asset
    paths stay relative and the site works from any base URL.
    """
    up = "../" * depth if depth else ""
    prefix = up.rstrip("/") or "."
    items = []
    for label, href in NAV:
        aria = ' aria-current="page"' if href == current else ""
        items.append(
            f'<li><a href="{prefix}{href}"{aria}>{esc(label)}</a></li>'
        )
    nav_items = "".join(items)
    script_tags = "".join(
        f'<script type="module" src="{up}js/{s}"></script>' for s in scripts
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · {esc(SITE_TITLE)}</title>
<meta name="description" content="{esc(description)}">
<link rel="stylesheet" href="{up}css/tokens.css">
<link rel="stylesheet" href="{up}css/style.css">
<script>
  // Set the theme before first paint to avoid a flash.
  (function () {{
    var t = localStorage.getItem('ptt-theme');
    if (t) document.documentElement.setAttribute('data-theme', t);
  }})();
</script>
</head>
<body>
<a class="visually-hidden" href="#main">Skip to content</a>
<nav class="nav">
  <div class="wrap nav__inner">
    <a class="nav__brand" href="{up or "./"}">6D&nbsp;Taxonomy</a>
    <ul class="nav__links">{nav_items}</ul>
    <button class="theme-toggle" data-theme-toggle type="button">dark</button>
  </div>
</nav>
<main id="main">
{body}
</main>
<footer class="footer">
  <div class="wrap">
    <div class="footer__grid">
      <div>
        <p class="eyebrow">Paper</p>
        <ul>
          <li><a href="{ARXIV_URL}">{ARXIV_ID}</a> <em>(placeholder)</em></li>
          <li><a href="{up}data/">Download the data</a></li>
        </ul>
      </div>
      <div>
        <p class="eyebrow">Repository</p>
        <ul>
          <li><a href="{REPO_URL}">GitHub</a></li>
          <li><a href="{REPO_URL}/issues">Report a problem</a></li>
        </ul>
      </div>
      <div>
        <p class="eyebrow">Licence</p>
        <ul>
          <li>Code — MIT</li>
          <li>Data and prose — CC BY 4.0</li>
        </ul>
      </div>
      <div>
        <p class="eyebrow">Authors</p>
        <ul>
          <li>Fardin Afdideh</li>
          <li>Fernando Seoane</li>
          <li>Farhad Abtahi</li>
          <li>Karolinska Institutet</li>
        </ul>
      </div>
    </div>
    <p style="margin-top:var(--sp-4);font-size:var(--step--2);opacity:.75">
      {esc(DISCLAIMER)}
    </p>
  </div>
</footer>
<script type="module" src="{up}js/theme.js"></script>
{script_tags}
</body>
</html>
"""
