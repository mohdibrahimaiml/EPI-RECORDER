# EPI pilot pack

**Audience:** customer engineers, security reviewers, and EPI Labs running a **guided pilot**.  
**Product spine:** a portable sealed **`.epi` file** — record → seal → verify offline. Hosted features are optional scale.

**Repo version:** 4.4.0 (source). **License:** MIT.

---

## 1. What this pilot is

| In scope | Out of scope |
|----------|----------------|
| Install CLI/SDK and seal real agent runs | Self-serve card checkout (Paddle may be unconfigured) |
| Offline `epi verify` / `epi view` | Cloud SSO / SAML (roadmap) |
| Optional org kit: `epi enterprise setup` + `pack` | Multi-user seats product |
| Optional hosted verify after account + plan | Hosted PDF API (use CLI PDF) |
| Founder-led onboarding | “Compliance certified” claims or legal advice |

Success is **evidence you can re-check without trusting a dashboard**, not a full SaaS control plane.

---

## 2. Install (pin the version)

PyPI may lag the GitHub source. Prefer an explicit pin for pilots.

**Option A — from GitHub (recommended until PyPI matches repo):**

```bash
pip install "git+https://github.com/mohdibrahimaiml/epi-recorder.git@main"
# Or pin a commit/tag when EPI Labs provides one:
# pip install "git+https://github.com/mohdibrahimaiml/epi-recorder.git@<tag-or-sha>"
```

**Option B — PyPI:**

```bash
pip install epi-recorder
pip show epi-recorder   # confirm Version
```

Check available releases:

```bash
pip index versions epi-recorder
```

Verify CLI:

```bash
epi --version
# or: python -m epi_cli --version
```

---

## 3. Day-1 path (everyone)

### Offline golden path (no API key, no account)

```bash
epi demo --no-browser
epi verify epi-recordings/demo_refund.epi
epi view epi-recordings/demo_refund.epi
```

Or with the Python API (see root [README.md](../README.md)):

```python
from epi_recorder import record, get_current_session

with record("demo.epi", goal="pilot golden path"):
    s = get_current_session()
    s.log("decision", action="approve", reason="pilot")
```

```bash
epi verify demo.epi
```

| Expect | Meaning |
|--------|---------|
| Integrity + signature OK | Seal is good |
| Identity LOCAL / UNKNOWN / WARN | Normal until org trust pin — **not** a broken seal |

### Enterprise kit (optional, ~15 minutes)

```bash
epi enterprise setup
# record one real agent run → your-run.epi
epi enterprise pack your-run.epi
```

Details: [ENTERPRISE-15-MINUTES.md](./ENTERPRISE-15-MINUTES.md).  
Honest inventory: [ENTERPRISE-CAPABILITY.md](./ENTERPRISE-CAPABILITY.md) or `epi enterprise capabilities`.

### Hosted verify (optional)

1. Sign in at https://epilabs.org/account  
2. EPI Labs may promote plan via operator **set-plan** (see [OPERATOR-RUNBOOK.md](./OPERATOR-RUNBOOK.md) — **ops only**)  
3. Open https://epilabs.org/verify/  
   - **Private check:** file stays in the browser (not uploaded)  
   - **Full report:** file is **uploaded** (uses plan quota if signed in)

API keys are for **CI/scripts** only (Advanced on the account page).

---

## 4. Reading list for this pilot

| Who | Docs |
|-----|------|
| All | This file + root [README.md](../README.md) |
| Customer engineer | [ENTERPRISE-15-MINUTES.md](./ENTERPRISE-15-MINUTES.md) |
| Security / procurement | [ENTERPRISE-CAPABILITY.md](./ENTERPRISE-CAPABILITY.md), [KNOWN_LIMITATIONS.md](./KNOWN_LIMITATIONS.md) |
| Independent auditor | [AUDITORS-GUIDE.md](./AUDITORS-GUIDE.md) |
| EPI Labs operator | [OPERATOR-RUNBOOK.md](./OPERATOR-RUNBOOK.md) |
| Doc map | [README.md](./README.md) |

### Do not use as pilot source of truth

- Strategy / “master pivot” writeups (marked historical in-repo)  
- `docs/archive/` and `docs/archive/junk-docs/`  
- Any doc claiming **AGPL** dual license (incorrect; product is **MIT**)  
- Random versioned `EPI-DOC-v*` files without checking the [docs index](./README.md)

---

## 5. Success criteria (template)

Fill in with the pilot sponsor:

| Criterion | Target | Pass? |
|-----------|--------|-------|
| Install and `epi --version` | Agreed pin works | ☐ |
| At least one sealed `.epi` from a **real** workflow | Path: ________ | ☐ |
| Offline verify PASS (integrity + signature) | `epi verify …` | ☐ |
| Optional: auditor pack zip | `epi enterprise pack` | ☐ |
| Optional: hosted full report while signed in | Account + verify | ☐ |
| Out-of-scope items not required | SSO, seats, hosted PDF, self-serve pay | ☐ |

---

## 6. Support

- Customer contact: as agreed in the pilot email  
- Product issues: GitHub https://github.com/mohdibrahimaiml/epi-recorder  
- Hosted ops (plans): EPI Labs only — not customer-facing curl/admin keys  

---

## 7. Related

- Full journeys and tier matrix: [COMPLETE-PRODUCT-GUIDE.md](./COMPLETE-PRODUCT-GUIDE.md)  
- CLI reference: [CLI.md](./CLI.md)
