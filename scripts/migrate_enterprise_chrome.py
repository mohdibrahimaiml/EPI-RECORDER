#!/usr/bin/env python3
"""One-shot migration: apply enterprise chrome to every page in website/.

- Inserts tokens.css + components-enterprise.css <link> tags before epi.css
  on any page that loads epi.css but not the new files.
- Removes references to deleted CSS (design-system.css).
Idempotent: skips pages already migrated.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

WEBSITE = Path(__file__).resolve().parents[1] / "website"

TOKENS_LINK = '<link rel="stylesheet" href="{prefix}css/tokens.css?v=1">'
ENTERPRISE_LINK = '<link rel="stylesheet" href="{prefix}css/components-enterprise.css?v=1">'

def migrate(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    orig = text

    # Skip stubs without stylesheets
    if "epi.css" not in text:
        return False

    # Remove dead stylesheet refs
    text = re.sub(r'\s*<link rel="stylesheet" href="[^"]*design-system\.css[^"]*">', "", text)

    if "tokens.css" in text:
        return False  # already migrated

    # Determine relative prefix from existing epi.css ref
    m = re.search(r'<link rel="stylesheet" href="([^"]*)css/epi\.css', text)
    prefix = m.group(1) if m else ""

    # Insert before the FIRST stylesheet link line containing epi.css
    tokens = TOKENS_LINK.format(prefix=prefix)
    ent = ENTERPRISE_LINK.format(prefix=prefix)
    pattern = re.compile(r'([ \t]*)<link rel="stylesheet" href="' + re.escape(prefix) + r'css/epi\.css')
    mm = pattern.search(text)
    if not mm:
        return False
    indent = mm.group(1)
    insertion = f"{indent}{tokens}\n{indent}{ent}\n"
    text = text[:mm.start()] + insertion + text[mm.start():]

    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False

def main() -> int:
    changed = []
    for html in sorted(WEBSITE.rglob("*.html")):
        # Skip legacy/dead dirs slated for deletion
        rel = html.relative_to(WEBSITE).as_posix()
        if rel.startswith(("viewer/", "epi-viewer/", "assets/", "enterprise/index.html")):
            continue
        try:
            if migrate(html):
                changed.append(rel)
        except Exception as e:
            print(f"ERROR {rel}: {e}", file=sys.stderr)
    print(f"Migrated {len(changed)} pages:")
    for c in changed:
        print(f"  + {c}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
