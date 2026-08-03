# Sector demo `.epi` artifacts

Live-LLM sealed demos for realistic agent situations (Groq). Regenerate with:

```bash
export GROQ_API_KEY=…   # never commit keys
python scripts/generate_sector_demo_epis.py
```

| File | Domain | Scenario |
|------|--------|----------|
| `demo-finance-loan-underwriter.epi` | Finance | Consumer loan underwriting: CRM, soft credit pull, income verify, credit-box policy, LLM approve/deny |
| `demo-healthcare-clinical-triage.epi` | Healthcare | Virtual-care triage for chest pressure: EHR intake, red-flag screen, protocol, nurse approval (demo only — not medical advice) |
| `demo-insurance-claim-adjudication.epi` | Insurance | HO-3 water claim: FNOL load, coverage lookup, photo analysis, denial recommendation + manager approval |
| `demo-legal-contract-review.epi` | Legal | Vendor MSA review: DMS fetch, playbook, clause risk extract, negotiation memo + GC approval (not legal advice) |

Each artifact includes paired `tool.call` / `tool.response` (AUD-CO-01), real `llm.call` / `llm.response` via LangChain + Groq, and is leak-scanned for `gsk_` / `GROQ_API_KEY` at seal time.

```bash
epi verify docs/assets/demo-finance-loan-underwriter.epi
epi view docs/assets/demo-healthcare-clinical-triage.epi
```

## Zero-install HTML export (share in DMs)

Regenerated via `epi export-html` into the static site (not gitignored):

| HTML (open in any browser) | Source `.epi` |
|----------------------------|---------------|
| [`/assets/demo/demo-finance-loan-underwriter.html`](../website/assets/demo/demo-finance-loan-underwriter.html) | `docs/assets/demo-finance-loan-underwriter.epi` |
| `/assets/demo/demo-healthcare-clinical-triage.html` | healthcare `.epi` |
| `/assets/demo/demo-insurance-claim-adjudication.html` | insurance `.epi` |
| `/assets/demo/demo-legal-contract-review.html` | legal `.epi` |

Live after deploy: `https://epilabs.org/assets/demo/demo-finance-loan-underwriter.html`

Each export is leak-scanned for `gsk_` / `GROQ_API_KEY` at generation time.

## Booking (Cal.com)

Edit `website/js/booking-config.js` and set:

```js
sprint: "https://cal.com/YOUR-USER/YOUR-EVENT"
```

Until that string is non-empty, “Book a sprint” stays on mailto.
