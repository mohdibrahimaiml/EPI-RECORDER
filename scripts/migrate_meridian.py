#!/usr/bin/env python3
"""Meridian migration: swap every page's stylesheet stack to meridian.css
and replace the legacy footer with the Meridian footer grid."""
from __future__ import annotations

import re
import sys
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "website"

# Stylesheet stack: any of these lines get collapsed into a single meridian link
CSS_LINE = re.compile(
    r'^[ \t]*<link rel="stylesheet" href="[^"]*css/(?:tokens|components-enterprise|epi|epi-v2|polish|wow|mobile|terminal)\.css[^"]*">\s*\n',
    re.M,
)

MERIDIAN_RE = re.compile(r'<link rel="stylesheet" href="([^"]*)css/meridian\.css[^"]*">')


def meridian_link(prefix: str) -> str:
    return f'<link rel="stylesheet" href="{prefix}css/meridian.css?v=1">'


def new_footer(logo_src: str) -> str:
    return f'''<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <img src="{logo_src}" alt="EPI Labs">
        <p>The evidence layer that makes AI agents insurable and auditable. Sealed .epi files — verify offline, forever.</p>
      </div>
      <div class="footer-col">
        <h4>Product</h4>
        <ul>
          <li><a href="/verify/">Verify a file</a></li>
          <li><a href="/how-it-works">How it works</a></li>
          <li><a href="/integrations">Integrations</a></li>
          <li><a href="/pricing">Pricing</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Evidence</h4>
        <ul>
          <li><a href="/trust">Trust model</a></li>
          <li><a href="/use-cases">Use cases</a></li>
          <li><a href="/enterprise">Enterprise</a></li>
          <li><a href="/status">Status</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Company</h4>
        <ul>
          <li><a href="/account">Account</a></li>
          <li><a href="https://github.com/mohdibrahimaiml/epi-recorder" target="_blank" rel="noopener">GitHub</a></li>
          <li><a href="/terms">Terms</a></li>
          <li><a href="/privacy">Privacy</a></li>
          <li><a href="mailto:mohdibrahim@epilabs.org">Contact</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; 2026 EPI LABS · MIT License</span>
    </div>
  </div>
</footer>'''


FOOTER_RE = re.compile(
    r'<footer class="site-footer">.*?</footer>\s*(?=<script|</body)',
    re.S,
)


def migrate(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    orig = text

    # Determine prefix from an existing css ref ("" for root pages, "../" for subdirs)
    m = re.search(r'<link rel="stylesheet" href="([^"]*?)css/', text)
    prefix = m.group(1) if m else ""

    # Collapse the whole legacy stack into meridian.css
    if CSS_LINE.search(text):
        text = CSS_LINE.sub("", text)
        if not MERIDIAN_RE.search(text):
            text = text.replace("</head>", "  " + meridian_link(prefix) + "\n</head>", 1)
    elif not MERIDIAN_RE.search(text):
        return None  # no known stylesheets; leave alone (login/portal stubs)

    # Replace footer
    logo = "../assets/logo.png" if path.parent.name != "website" else "assets/logo.png"
    fm = FOOTER_RE.search(text)
    if fm and "footer-grid" not in fm.group(0):
        text = FOOTER_RE.sub(new_footer(logo), text, count=1)

    if text != orig:
        path.write_text(text, encoding="utf-8")
        return "updated"
    return None


def main() -> int:
    changed, skipped = [], []
    for html in sorted(WEB.rglob("*.html")):
        rel = html.relative_to(WEB).as_posix()
        if rel.startswith(("assets/", "viewer/", "epi-viewer/", "enterprise/index.html")):
            continue
        r = migrate(html)
        (changed if r else skipped).append(rel)
    print(f"Migrated {len(changed)}:")
    for c in changed:
        print("  +", c)
    print(f"Untouched {len(skipped)}: {', '.join(skipped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
