# Sector demo \.epi\ artifacts

Live-LLM sealed demos (Groq). Regenerate:

\\ash
export GROQ_API_KEY=…   # never commit keys
python scripts/generate_sector_demo_epis.py
\
## Flagship (DM / sales)

| Asset | Path |
|-------|------|
| Sealed case | \docs/assets/demo-finance-loan-underwriter.epi\ |
| Zero-install HTML | \website/assets/demo/demo-finance-loan-underwriter.html\ (also on site after deploy: \/assets/demo/demo-finance-loan-underwriter.html\) |

\\ash
# Claim / insurer path — always use strict (FAIL if sealer not org-pinned):
epi verify docs/assets/demo-finance-loan-underwriter.epi --policy strict
# Dev skim (unpinned → WARN · UNVERIFIED IDENTITY):
epi verify docs/assets/demo-finance-loan-underwriter.epi
# or open the HTML export in any browser
\
## All sector demos

| File | Domain |
|------|--------|
| \demo-finance-loan-underwriter.epi\ | Finance — loan underwriting |
| \demo-healthcare-clinical-triage.epi\ | Healthcare — clinical triage (not medical advice) |
| \demo-insurance-claim-adjudication.epi\ | Insurance — claim adjudication |
| \demo-legal-contract-review.epi\ | Legal — MSA review (not legal advice) |

HTML exports for all four live under \website/assets/demo/*.html\.

Leak-scan every seal: no \gsk_\ / \GROQ_API_KEY\ in archive.
