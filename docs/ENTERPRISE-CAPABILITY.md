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

## 30-minute enterprise path

```bash
pip install epi-recorder
epi enterprise bootstrap --out enterprise-epi
# seal agent runs with org-seal key
epi keys bundle-import enterprise-epi/org-trust-bundle.zip
epi verify path/to/run.epi --policy strict
epi enterprise kit path/to/run.epi --out auditor-pack.zip
```

Or list the inventory anytime:

```bash
epi enterprise capabilities
```

See also: [ENTERPRISE-EVIDENCE-PLAYBOOK.md](./ENTERPRISE-EVIDENCE-PLAYBOOK.md), [ENTERPRISE-TRUST-BUNDLE.md](./ENTERPRISE-TRUST-BUNDLE.md), [SELF-HOSTED-RUNBOOK.md](./SELF-HOSTED-RUNBOOK.md).
