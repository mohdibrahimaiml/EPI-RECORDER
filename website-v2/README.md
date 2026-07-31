# website-v2 — experimental redesign (NOT production)

This folder is a **full clone** of `website/` used to redesign the public site
**without touching** the live source of truth.

| Path | Role |
|------|------|
| `website/` | **Production** — GitHub Pages / deploy / `sync_website.py` source |
| `website-v2/` | **Sandbox redesign** — edit freely; not deployed |

## Do not

- Point deploy workflows at this folder
- Change `scripts/sync_website.py` to use `website-v2`
- Run sync from this folder into `site/` or `verify_portal/static/`

## Preview locally

```powershell
cd website-v2
python -m http.server 8765
# open http://127.0.0.1:8765/
```

## Promote later (manual, separate PR)

Only after review: copy chosen files from `website-v2/` → `website/`, then
sync and deploy as usual.

## Redesign goals

- Product-first homepage (verify + install CTAs)
- Differentiate from LLM observability dashboards
- Honest free vs paid / seal vs identity
- Keep brand thesis; cut brochure noise
