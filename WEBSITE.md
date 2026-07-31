# Website source of truth

Edit production public site files under **`website/`** only.

```bash
python scripts/sync_website.py   # → verify_portal/static + epi-official + site/
```

GitHub Pages deploys from `website/`.

| Path | Role |
|------|------|
| `website/` | **Production** source (`epilabs.org`) |
| `website-v2/` | **Sandbox redesign** — not deployed by default |

Details: [docs/SITE.md](docs/SITE.md) · Docs map: [docs/README.md](docs/README.md).
