# EPI Enterprise capability map (honest)

**Audience:** security, platform, compliance, procurement.  
**Spine:** portable sealed `.epi` — same bytes, same answer offline and in CI.

## What we provide today (shipped)

| Capability | How |
|------------|-----|
| Cryptographic evidence file | Ed25519 seal, SHA-256 member hashes, hash-linked steps |
| Offline verify / view | `epi verify`, `epi view` — no vendor login required |
| Air-gapped seal | `EPI_NOTARIZE=0` |
| Org identity (keys) | `epi keys generate`, trust pin, **trust bundles** |
| Policy + fault analysis | `epi_policy.json`, FaultAnalyzer at seal |
| Annex IV technical tooling | `epi annex` (multi-sign, report HTML/PDF via CLI) |
| CI gate | GitHub Action `verify-epi` |
| Hosted verify + remote SCITT | Plan-gated API (Pro+ / Enterprise volume) |
| Self-hosted review path | `epi gateway` / `epi connect` |
| Enterprise kit | `epi enterprise bootstrap`, `epi enterprise kit` |

## What we provide as services (not software checkboxes)

- Dedicated onboarding and pilot setup  
- Custom hosted limits / private ops attention  
- Legal & procurement support  
- **Contractual SLA only if signed in writing**

## Not shipped as product (roadmap / deal-driven)

- Cloud SSO / SAML  
- Multi-tenant SaaS seat admin  
- FDA / HIPAA / NIST **adapter product suite**  
- Managed multi-tenant DID registry  
- Hosted PDF API (use `epi annex report --format pdf`)

## 15-minute enterprise path

```bash
pip install epi-recorder
epi enterprise setup
# record one agent run → your-run.epi
epi enterprise pack your-run.epi
```

Online (Pro/Team/Enterprise): sign in → [Verify a file](https://epilabs.org/verify/) — **no API key in the browser**.

```bash
epi enterprise capabilities
```

See [PILOT.md](./PILOT.md) · [ENTERPRISE-15-MINUTES.md](./ENTERPRISE-15-MINUTES.md).  
Also: [ENTERPRISE-EVIDENCE-PLAYBOOK.md](./ENTERPRISE-EVIDENCE-PLAYBOOK.md), [SELF-HOSTED-RUNBOOK.md](./SELF-HOSTED-RUNBOOK.md).  
**Full user + investor guide:** [COMPLETE-PRODUCT-GUIDE.md](./COMPLETE-PRODUCT-GUIDE.md).  
**Docs map:** [README.md](./README.md).  
Operators only: [OPERATOR-RUNBOOK.md](./OPERATOR-RUNBOOK.md).
