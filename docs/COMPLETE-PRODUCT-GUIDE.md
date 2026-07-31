# EPI — Complete product guide  
### User paths that stay simple · Pro & Enterprise pitch that stays honest

**Last aligned with product:** dual-mode Verify, enterprise kit CLI, honest pricing (repo `main`).  
**Source version:** **4.4.0** in this repository. **PyPI may lag** (confirm with `pip index versions epi-recorder`). Prefer a git pin for pilots — see [PILOT.md](./PILOT.md).  
**Docs map:** [README.md](./README.md).  
**Spine of the product:** a portable sealed **`.epi` file** — same bytes, same cryptographic answer offline, in CI, and on the hosted path.

Use this document for:

1. **Reducing user hassle** — who does what, in the fewest steps  
2. **Pitching Pro & Enterprise** — what money buys, what is open source, what is not built yet  

Related short docs (do not replace this overview):

| Doc | Audience |
|-----|----------|
| [ENTERPRISE-15-MINUTES.md](./ENTERPRISE-15-MINUTES.md) | Customer engineer pilot |
| [ENTERPRISE-CAPABILITY.md](./ENTERPRISE-CAPABILITY.md) | Security / procurement |
| [ENTERPRISE-EVIDENCE-PLAYBOOK.md](./ENTERPRISE-EVIDENCE-PLAYBOOK.md) | Org evidence process |
| [OPERATOR-RUNBOOK.md](./OPERATOR-RUNBOOK.md) | **EPI Labs ops only** (set-plan, Paddle env) |
| Live site | https://epilabs.org · Pricing · Account · Verify · Enterprise |

---

## 1. One-sentence product

**EPI turns AI agent runs into sealed evidence files that anyone can verify without trusting a dashboard.**

- **File-first**, not “log into our app to see the truth.”  
- **Crypto integrity** (Ed25519 seal, hashes, chain) is independent of marketing names or free-text “who ran this.”  
- **Open source core free forever** (MIT). Revenue is **hosted scale + remote transparency + human help**, not a second closed evidence format.

---

## 2. What a `.epi` is (and is not)

| It is | It is not |
|-------|-----------|
| A sealed **envelope** of run evidence (steps, hashes, signature, optional policy/fault snapshot) | A general-purpose **filesystem** or database |
| Verifiable **offline** with `epi verify` / browser **Private check** | Dependent on EPI being online for the offline path |
| Portable across machines and auditors | A multi-tenant “seats” product by itself |

**Trust language (important for users and investors):**

- **SEAL OK** = file integrity + signature checks passed.  
- **Identity** (KNOWN / LOCAL / UNKNOWN) = whether the sealer key is pinned in a trust store — **not** HR badge identity.  
- Seal OK with unpinned identity is **not** a failed seal.

---

## 3. How we reduced user hassle (what “simple” means)

### 3.1 Fewer entry points

| Before (felt hard) | After (shipped UX) |
|--------------------|--------------------|
| Portal vs Verify vs API key first | **One Verify page** + Account |
| “Get an API key to try Pro” | **Sign in → drop file** (session); keys only under **Advanced / CI** |
| Enterprise = SSO / dashboard myth | Enterprise = **file kit** + optional hosted volume + services |
| Pricing listed free CLI features as paid | **Honest matrix**: free stays free; pay for hosted gates |

### 3.2 Three verification paths (same file)

```text
                    your-run.epi
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   A) Fully offline    B) Private      C) Full report
      epi verify          check            (upload)
      epi view            browser          plan quota
      no website          file NEVER       file IS
                          uploaded         uploaded
```

| Mode | URL / command | File leaves machine? | Uses plan quota? |
|------|---------------|----------------------|------------------|
| **Offline CLI** | `epi verify file.epi` | No | No |
| **Private check** | https://epilabs.org/verify/ | **No** (browser only) | No |
| **Full report** | https://epilabs.org/verify/?mode=server | **Yes** (uploaded) | Yes if signed in |

**Critical UX truth:** both browser modes **load the website over the internet**. The choice is only **whether the `.epi` file is uploaded**, not “online vs offline website.”

Truly offline = CLI only.

### 3.3 Account UX principles

1. Show **plan + usage** first.  
2. Primary button: **Full report (upload)** or **Private check**.  
3. **API keys** under Advanced — CI/scripts only.  
4. Pro / Team / Enterprise: browser verify **without** a key when signed in.

### 3.4 Enterprise customer path (15 minutes)

```bash
pip install epi-recorder
epi enterprise setup          # kit: keys, trust bundle, policy, CI recipe
# … record one real agent run → your-run.epi …
epi enterprise pack your-run.epi   # auditor-pack.zip
```

No dashboard login required for a pilot pack. Optional online: sign in → Full report.

---

## 4. Complete user journeys (copy/paste for support & onboarding)

### Journey A — Developer (open source, zero friction)

**Goal:** Prove a run was sealed and intact.

```bash
pip install epi-recorder
epi demo                    # or record() / wrap_openai in your code
epi verify path/to/run.epi
epi view path/to/run.epi
```

**Browser:** Private check at `/verify/` (file not uploaded).  
**Success:** SEAL OK offline forever free.

### Journey B — Auditor / security reviewer

**Goal:** Check a file without installing vendor cloud.

1. Receive `run.epi` + optional `org-trust-bundle.zip` (public keys only).  
2. Either:
   - Browser **Private check**, or  
   - `epi keys bundle-import org-trust-bundle.zip` then `epi verify run.epi --policy strict`  
3. Never need private keys.

### Journey C — Pro individual (hosted scale)

**Goal:** Many online checks + optional remote SCITT + simple UI.

1. Sign in: https://epilabs.org/account (GitHub OAuth).  
2. Get **Pro** (self-serve when Paddle is configured; until then: pilot email or operator set-plan).  
3. **Full report** at `/verify/?mode=server` while signed in — **no API key**.  
4. Optional: Advanced → create CI key for scripts:

```bash
curl -X POST https://epilabs.org/api/verify \
  -H "X-API-Key: epi_..." \
  -F "file=@run.epi"
```

**Plan (enforced in product):** ~**10,000** hosted verifications / month · up to **10** API keys · **remote SCITT** · founder email support · **$19/mo** list.

### Journey D — Team (volume, not seats)

**Goal:** Higher hosted quota for a group shipping agents.

- **50,000** hosted checks / month · up to **50** CI keys · remote SCITT · email support target 48h · shared onboarding.  
- **$499/mo** list · contact to enable.  
- **Honest gap:** multi-user seats / SSO **not built** — Team is **volume + support**, not Okta product.

### Journey E — Enterprise pilot

**Goal:** Security can accept the evidence model in one afternoon.

1. Engineer: 15-minute path (`setup` → record → `pack`).  
2. Security: import trust bundle, strict verify, optional review binding.  
3. Commercial: custom limits, onboarding, procurement, optional SLA **in writing**.  
4. Hosted: operator promotes plan (`set-plan`) after sign-in; unlimited/custom hosted verify; remote SCITT; dedicated support.

**Command inventory:**

```bash
epi enterprise capabilities   # honest printed inventory
epi enterprise setup
epi enterprise pack run.epi
```

### Journey F — CI gate (any tier offline)

```yaml
# idea: GitHub Action verify-epi / enterprise kit template
- run: pip install epi-recorder
- run: epi keys bundle-import org-trust-bundle.zip   # if org keys
- run: epi verify artifact.epi --policy strict
```

No Pro required for **local/CI offline** verify.

---

## 5. Plans matrix (shipped gates only)

Aligned with `verify_portal/tier_gating.py` and public pricing.

| | Open Source | Pro | Team | Enterprise |
|--|-------------|-----|------|------------|
| **Price** | $0 | $19/mo | $499/mo | Custom |
| **CLI / SDK / offline verify** | Yes | Yes | Yes | Yes |
| **Annex multi-sign + CLI PDF** | Yes | Yes | Yes | Yes |
| **Public GitHub Action** | Yes | Yes | Yes | Yes |
| **Local SCITT** | Yes | Yes | Yes | Yes |
| **Hosted verify quota** | Low free / abuse cap | **10k / mo** | **50k / mo** | **Custom** |
| **Browser verify w/ session** | Limited free | Yes | Yes | Yes |
| **API keys** | 1 (onboarding) | 10 | 50 | Custom |
| **Remote SCITT** | No (402 free) | Yes | Yes | Yes |
| **Support** | Community | Founder email | Email ~48h | Dedicated |
| **SLA** | — | — | — | **Only if signed** |
| **SSO / seats** | — | — | **Not built** | **Roadmap** |
| **Hosted PDF API** | — | **Not shipped** (use CLI PDF) | same | same |

**What you pay for:** hosted verification scale, remote transparency log, API automation volume, and human support — **not** a different `.epi` format.

**Payment readiness (ops truth):**

- Product tiers and gates: **live**.  
- **Invoice + admin set-plan:** ready now for pilots.  
- **Paddle self-serve Subscribe:** requires live env (client token + price IDs). Until then, Pro CTA correctly falls back to **sign in / contact**.

---

## 6. Investor pitch — Pro & Enterprise

### 6.1 Problem (why this market exists)

AI agents act with tools, money, data, and customers. Boards and regulators will ask:

> *What did the agent do, was the record tampered with, and can a third party check it without trusting the vendor’s UI?*

Logs and screenshots fail that test. Dashboards fail air-gapped and adversarial review.  
**Portable cryptographic evidence** is the missing layer between “agent framework” and “audit / insurance / procurement.”

### 6.2 Solution (wedge)

| Layer | Role |
|-------|------|
| **Open-source CLI/SDK** | Land with developers; zero purchase friction; viral install |
| **`.epi` standard artifact** | Network effect: one file format auditors learn once |
| **Pro** | Expand: hosted verify volume + remote SCITT for individuals shipping agents |
| **Team** | Expand: volume for groups before seats product exists |
| **Enterprise** | Monetize trust: kit, custom limits, onboarding, procurement, services |

**Business model honesty (strength, not weakness):**

- Do **not** claim open-core hostage features that already ship free (multi-sign, CLI PDF, Action).  
- Monetize **what the hosted product actually gates**.  
- Enterprise is **limits + services + trust process**, not a fake closed crypto stack.

### 6.3 Why Pro exists ($19)

**Buyer:** solo builder / indie / early team member shipping agents.

**Job to be done:** “I need many online checks and optional remote anchoring without running infra.”

**Value props (accurate):**

1. 10k hosted verifications / month  
2. Sign-in browser path (no key for humans)  
3. Optional CI keys  
4. Remote SCITT when service configured  
5. Founder email support  

**Why not free forever for hosted:** abuse + infra cost of uploads and logs. Offline remains free → trust with community.

**14-day pilot:** Pro-level limits + onboarding call, no card — conversion path into Pro or Enterprise conversation.

### 6.4 Why Enterprise exists (custom)

**Buyer:** security, platform, compliance, procurement.

**Job to be done:** “We need an evidence process we can defend in CI and to auditors, with optional scale and a human who will onboard us.”

**What ships as software today:**

- Org keys + trust bundles  
- Strict verify / review binding  
- Policy + fault analysis at seal  
- Enterprise kit (`setup` / `pack`)  
- Self-host paths (`gateway` / connect)  
- Hosted verify + remote SCITT at custom volume  

**What sells as services:**

- Dedicated onboarding / pilot  
- Custom hosted limits & ops attention  
- Legal & procurement  
- **SLA only in writing**  

**What we do not pitch as shipped:**

- Cloud SSO / SAML product  
- Multi-tenant seat admin  
- FDA / HIPAA / NIST adapter suite as product  
- Managed multi-tenant DID registry  

Roadmap can be deal-driven; **do not** checkmark them on slides.

### 6.5 Competitive framing (positioning)

| Approach | Weakness vs EPI |
|----------|-----------------|
| Vendor dashboard logs | Vendor lock-in; hard air-gap; hard third-party verify |
| Raw cloud logs | No seal of agent step graph; easy rewrite |
| Video / screenshots | Not hash-linked; not CI-native |
| “Trust our SaaS” | Buyer still depends on your uptime and UI |

**EPI pitch line:**  
*Evidence is a file. Verification is a command or a browser tab. Hosted is optional scale — not the source of truth.*

### 6.6 Go-to-market (practical)

```text
1. Open source land  →  pip install / GitHub / integrations (LangChain, etc.)
2. Pro expand        →  individuals who outgrow free hosted cap
3. Team expand       →  volume (until seats exist, sell volume honestly)
4. Enterprise close  →  pilot pack in 15 minutes + procurement + set-plan
```

**Sales motion today that works without Paddle:**

1. Demo offline seal/verify.  
2. Run enterprise 15-minute path live.  
3. Invoice / pilot.  
4. User signs in once → operator **set-plan**.  
5. They use Full report + usage meter.

### 6.7 Demo script (5–7 minutes)

| Min | Action | Say |
|-----|--------|-----|
| 0–1 | Problem slide | Agents need evidence, not screenshots |
| 1–3 | `epi demo` / seal | “This produces a file, not a login” |
| 3–4 | `epi verify` + Private check | “Same checks; file never uploaded in private mode” |
| 4–5 | Full report signed-in | “Plan-backed upload when you want hosted scale” |
| 5–6 | `epi enterprise setup` + pack | “Security gets a zip, not a vendor dashboard” |
| 6–7 | Pricing honesty | “Pay for hosted gates and help; core crypto free” |

### 6.8 Slide-ready bullet lists

**Pro slide**

- $19/mo self-serve target  
- 10k hosted verifies · session browser path · 10 CI keys  
- Remote SCITT · founder support  
- Same open-source CLI forever  

**Enterprise slide**

- File-first evidence kit in 15 minutes  
- Org trust bundles + strict CI gate  
- Custom hosted limits · remote SCITT · dedicated help  
- Services: onboarding, legal, optional written SLA  
- Honest roadmap: SSO/seats/adapters later  

**Risk / integrity slide (builds investor trust)**

- We removed false paid claims (e.g. free multi-sign already in CLI)  
- Hosted PDF API not sold (501 / CLI PDF instead)  
- Seal vs identity UX clarified (no false FAIL)  

---

## 7. Architecture map (enough for pitch, not a whitepaper)

```text
Developer app / agent
        │  epi-recorder / SDK / integrations
        ▼
   sealed .epi (envelope-v2 + Ed25519)
        │
        ├── offline: epi verify / epi view / GitHub Action
        ├── browser Private: WebCrypto in tab (no upload)
        └── hosted: POST /api/verify  [plan quota + optional SCITT]
                    session Bearer or X-API-Key
```

**Deploy surfaces**

| Surface | Role |
|---------|------|
| `website/` | Source of truth for marketing + account + verify UI |
| Cloudflare / Pages | Public site (incl. `site/` mirror where configured) |
| Render `verify_portal` | API, auth, plans, SCITT routes, static sync |

---

## 8. Support cheat-sheet (reduce hassle)

| User says | You say / do |
|-----------|----------------|
| “Portal and Verify both use internet — same?” | One Verify page; difference is **file upload**, not internet |
| “Do I need an API key?” | Humans: **no**. CI: Advanced → key |
| “Is seal fail because identity unknown?” | No — seal OK can coexist with unpinned key |
| “Is PDF a Pro feature?” | **CLI PDF free.** Hosted PDF API not productized |
| “Does Team give me seats?” | **Not yet** — Team is higher volume + support |
| “Enterprise SSO?” | Roadmap; today kit + services + optional self-host |
| “How do I upgrade without Paddle?” | Contact us → sign in once → we set plan |
| “Offline forever?” | Yes: `epi verify` |

**URLs**

- Account: https://epilabs.org/account  
- Verify private: https://epilabs.org/verify/  
- Verify upload: https://epilabs.org/verify/?mode=server  
- Pricing: https://epilabs.org/pricing  
- Enterprise: https://epilabs.org/enterprise  
- Contact: mohdibrahim@epilabs.org  

---

## 9. Operator notes (you only — not for customers)

See [OPERATOR-RUNBOOK.md](./OPERATOR-RUNBOOK.md).

- Promote plan: admin `set-plan` after user signs in once.  
- Plans: `free` \| `pro` \| `team` \| `enterprise`.  
- Paddle: set tokens/price IDs on Render when self-serve should go live.  
- Rotate admin keys if ever exposed in chat/logs.

---

## 10. Doc & site maintenance rules

1. Edit **product claims** only after checking `tier_gating.py` and real API behavior.  
2. Public HTML lives in **`website/`** only → `python scripts/sync_website.py`.  
3. Keep **customer docs** free of admin keys and Render ops.  
4. Prefer short journeys over long feature catalogs.  
5. Label roadmap as roadmap.

---

## 11. Checklist: ready for user vs ready for investor

### User-ready (hassle)

- [x] Offline golden path works without account  
- [x] Dual-mode Verify explains upload clearly  
- [x] Account prioritizes verify over API keys  
- [x] Enterprise 15-minute path documented  
- [x] Pricing does not sell non-existent features  
- [ ] Paddle self-serve live (ops config) — optional for first sales  

### Investor-ready (Pro / Enterprise narrative)

- [x] Clear free vs paid boundary  
- [x] Pro unit offer ($19, 10k, SCITT, support)  
- [x] Enterprise as kit + services + custom volume  
- [x] Honest gaps (seats, SSO, hosted PDF API)  
- [x] Demo path under 10 minutes  
- [ ] Traction metrics (fill with your real installs, pilots, revenue)  

---

## 12. One-page leave-behind (print / PDF later)

**EPI** seals AI agent runs into **`.epi` files**. Anyone verifies offline.  
**Free forever:** CLI, SDK, seal, verify, Annex, CI Action.  
**Pro ($19):** 10k hosted checks, browser path, CI keys, remote SCITT, email.  
**Team ($499):** 50k checks, more keys, volume support (not seats yet).  
**Enterprise (custom):** org kit in 15 minutes, custom limits, onboarding, procurement, optional SLA.  
**Truth rule:** same file, same crypto answer — hosted is scale, not the source of truth.

---

*End of complete product guide. Update this file when tiers, verify UX, or enterprise kit commands change — keep it boring and true.*
