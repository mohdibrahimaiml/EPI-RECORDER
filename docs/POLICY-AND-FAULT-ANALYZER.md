# EPI Policy and Fault Analyzer — User Guide

**Audience:** normal users (engineers, reviewers, pilot teams)  
**Not:** cryptographic seal verify alone (`epi verify`) — that is a different layer  
**Docs map:** [README.md](./README.md) · **Pilot:** [PILOT.md](./PILOT.md) · **Policy deep dive:** [POLICY.md](./POLICY.md)

---

## 1. What these two things are

| Piece | What it is | What it is *not* |
|-------|------------|------------------|
| **Policy** | A company **rulebook** file (`epi_policy.json`) that defines mechanical rules for an agent workflow | Not a moral judge, not legal compliance by itself |
| **Fault analyzer** | Software that **reads the recorded steps** of a run and flags when those rules (or built-in heuristics) look broken | Not the same as “was the file tampered with?” |

### Seal vs policy (do not confuse them)

| Command / layer | Question it answers |
|-----------------|---------------------|
| **`epi verify`** | Is this `.epi` **intact**? Signature valid? (crypto integrity) |
| **Policy + fault analyzer** | Did this **run’s log** break **our rules** or look anomalous? |
| **Human review** | Was the business decision actually right? |

A run can be:

- **Seal PASS** + **fault DETECTED** — file is authentic, but the *behavior on the tape* broke a rule (common in demos).  
- **Seal FAIL** — do not trust the file; fix or re-record before debating policy.

EPI’s own model: **`steps.jsonl` inside the `.epi` is the ground truth** for analysis.  
What was never recorded cannot be judged.

---

## 2. How EPI “knows” right vs wrong

EPI does **not** understand right and wrong like a person.

It only checks:

> *Do the recorded steps match the mechanical rule types and fields you configured (plus some always-on heuristics)?*

### Rule types → what the machine checks

| Rule type in `epi_policy.json` | Roughly “wrong” means |
|--------------------------------|------------------------|
| `prohibition_guard` | A **forbidden pattern** (regex) appears in step content (e.g. API-key-like strings) |
| `sequence_guard` | Action **B** appears without earlier action **A** |
| `threshold_guard` | A **number** exceeds `threshold_value` without a required follow-up action |
| `constraint_guard` | A later decision **exceeds** a limit/balance-like value seen earlier (`watch_for`) |
| `approval_guard` | A sensitive action ran **without** an approval-style step first |
| `tool_permission_guard` | A **tool name** is outside allow-list / on deny-list |

Human-readable fields (`description`, `rationale`, free-text `violation_if`) help **people** read the rulebook.  
The detectors use structured fields: `must_call`, `required_before`, `threshold_value`, `prohibited_pattern`, `watch_for`, `allowed_tools`, etc.

### What EPI cannot know

- Whether a loan *should* have been approved in the real world  
- Actions that happened but were **not logged** into steps  
- Full natural-language meaning of every free-text field  
- “We are EU AI Act certified” (evidence ≠ certificate)

**You** encode operational rules; **EPI** scores the **tape** against those rules.

---

## 3. End-to-end flow (normal user)

```text
┌─────────────────┐
│ 1. Write rules  │  epi policy init  →  epi_policy.json
└────────┬────────┘
         ▼
┌─────────────────┐
│ 2. Run agent    │  From the same project folder (so policy is found)
│    with EPI     │  record() / wrappers / epi demo / epi record
└────────┬────────┘
         ▼
┌─────────────────┐
│ 3. Seal .epi    │  FaultAnalyzer runs automatically
│                 │  → analysis.json (+ policy.json / policy_evaluation.json)
└────────┬────────┘
         ▼
┌─────────────────┐
│ 4. Read results │  epi analyze run.epi
│                 │  epi view run.epi
│                 │  (optional) epi review …
└─────────────────┘
         │
         ├─ also: epi verify run.epi   ← integrity only (separate)
```

You do **not** call `FaultAnalyzer` yourself. It runs at **seal/pack** time when the `.epi` is built.

---

## 4. Creating a policy (rulebook)

### Commands

```bash
epi policy --help

epi policy init              # guided (profiles + questions)
epi policy init --yes        # non-interactive defaults
epi policy init --profile finance.refund-agent --yes
epi policy profiles          # list built-in profiles
epi policy validate epi_policy.json
epi policy show epi_policy.json
epi policy lint epi_policy.json
```

### Typical first-time session

```bash
cd my-agent-project
epi policy init
# Choose a domain profile (insurance, finance, healthcare, …)
# or "custom starter" and answer yes/no questions about thresholds, approvals, etc.

epi policy validate epi_policy.json
```

This writes **`epi_policy.json`** in the current directory (or `-o path`).

### Built-in profile flavors (examples)

Guided init maps friendly names to profiles such as:

- Insurance claim denials  
- Finance underwriting / refunds  
- Healthcare triage / clinical assistant  
- Custom starter (generic guards you refine)

Use `epi policy profiles` for the machine profile ids.

### Optional: browser rules editor

```bash
epi policy init --open-editor
# or
epi policy show epi_policy.json --open-editor
```

Opens a reviewer-oriented rules UI with the policy loaded (when available in your install).

---

## 5. Where EPI finds your policy at seal time

Order of lookup (conceptually):

1. Policy already in the recording workspace (`policy.json` / `epi_policy.json` next to steps)  
2. Else **`epi_policy.json` in the process current working directory** (`load_policy()`)  
3. If missing or invalid → **no formal policy** (heuristics only); recording **still succeeds**

**Practical rule:**  
Put `epi_policy.json` in the project root and **run the agent / seal from that directory**.

A broken policy file logs a warning and continues **without** policy-grounded analysis (never aborts the seal).

---

## 6. Recording a run so policy can fire

Policy only sees **structured steps**. Instrument with EPI:

```python
from epi_recorder import record, get_current_session, wrap_openai
from openai import OpenAI

client = wrap_openai(OpenAI())

with record("run.epi", goal="process refund"):
    # LLM / tools / decisions get captured as steps
    ...
```

Or:

```bash
epi demo --no-browser          # sample run that seals with analysis
epi record --out run.epi -- python agent.py
```

**Tip:** Name tools and events in ways your rules can match (`risk_assessment`, `approve_refund`, field names like `amount`, `credit_limit`).  
If the log never contains those names, sequence/threshold rules cannot “see” them.

---

## 7. Fault analyzer — what runs at seal

`FaultAnalyzer` walks **passes** over the step list:

| Pass | When | Example |
|------|------|---------|
| Error continuation | Always (heuristic) | Tool error, then continued as if OK |
| Constraint | Always / policy | Limit-like violations |
| Sequence | Policy | Missing prerequisite step |
| Threshold | Policy | Amount over limit without control |
| Prohibition | Policy | Secret/pattern in content |
| Approval gap | Always / policy | Sensitive action without approval trail |
| Context drop | Always | Identity fields vanishing mid-run |
| Tool permission | Policy | Disallowed tool |
| Coverage / gaps | Always | Thin instrumentation, orphan tools, LLM gaps |
| Time anomalies | Always | Suspicious gaps / SCITT timing |

Flags are ranked: **policy violations first**, then severity, then step index.  
Primary fault + secondary flags are stored in **`analysis.json`** inside the `.epi`.

If a formal policy was used, the artifact also typically includes:

- `policy.json` — copy of the rulebook used  
- `policy_evaluation.json` — per-control evaluation summary  

You can list members mentally as: “the sealed folder that is the `.epi`.”

---

## 8. Reading results as a user

### A. `epi analyze` (fast CLI summary)

```bash
epi analyze run.epi
```

Reads **`analysis.json` already embedded** (does not re-run the agent).

**If no policy at seal time:**

```text
No epi_policy.json was found for this run.
EPI used heuristic analysis only (less precise).
→ Run epi policy init to define compliance rules …
```

**If a fault was found:**

```text
FAULT DETECTED — run.epi
  Verdict:    Needs review before trust
  Severity:   CRITICAL
  Type:       POLICY_VIOLATION
  Rule:       R004 — …
  Step:       7
  … plain English …
  Run: epi review run.epi to confirm or dismiss
```

**If clean:**

```text
[OK] run.epi — No anomalies detected
  Steps: N recorded, …% coverage
```

### B. Simulate another rulebook without re-running the agent

```bash
epi analyze run.epi --policy path/to/other_epi_policy.json
```

Re-analyzes steps in memory with that policy (**read-only**; does not rewrite the `.epi` unless you re-seal).

### C. `epi view run.epi`

Opens the browser case view: timeline, analysis, policy context for reviewers.

### D. `epi review run.epi …`

Human follow-up on findings (show / bind review). Use after analyze flags issues you want attested.

### E. Still run verify for the file itself

```bash
epi verify run.epi
```

Use this before trusting the artifact as evidence of *what was sealed*, independent of policy faults.

---

## 9. Minimal cookbooks

### Cookbook A — First week (recommended)

```bash
cd my-project
pip install epi-recorder   # or git pin — see PILOT.md

# 1) Rulebook
epi policy init --yes
epi policy validate epi_policy.json

# 2) Run agent under EPI from this folder (or epi demo)
epi demo --no-browser

# 3) Integrity of the file
epi verify epi-recordings/demo_refund.epi

# 4) Policy / heuristic findings
epi analyze epi-recordings/demo_refund.epi

# 5) Inspect
epi view epi-recordings/demo_refund.epi
```

### Cookbook B — “I only care if the file was tampered with”

```bash
epi verify run.epi
```

You can ignore policy entirely. At seal, heuristics may still produce `analysis.json`.

### Cookbook C — “I care about company rules”

1. Maintain `epi_policy.json` in the project.  
2. Always seal from that project directory.  
3. `epi analyze run.epi` after each important run.  
4. Fix agent/process or update rules; re-record if needed.  
5. Optional: `epi analyze run.epi --policy trial_policy.json` to try rule changes offline.

### Cookbook D — Pilot / enterprise kit

Policy and fault analysis work alongside the evidence kit:

```bash
epi enterprise setup
# keep epi_policy.json in the project when you record
epi enterprise pack your-run.epi   # auditor-facing zip
epi analyze your-run.epi
```

See [ENTERPRISE-15-MINUTES.md](./ENTERPRISE-15-MINUTES.md).

---

## 10. Designing rules that actually work

| Do | Don’t |
|----|--------|
| Match **tool/step names** your code logs | Write only English essays with no structured fields |
| Use **prohibition** patterns for secrets/PII shapes you care about | Expect EPI to “understand” the whole business case |
| Put **threshold** numbers in `threshold_value` | Rely on `description` alone for detection |
| Instrument **risk_assessment** (or similar) if sequence rules require it | Assume unlogged side effects are visible |
| Keep policy next to the project and run from cwd | Scatter policy files EPI never searches |
| Treat analyze output as **review queue** | Treat clean analyze as “legally compliant forever” |

---

## 11. Interpreting common situations

| Situation | Meaning | What to do |
|-----------|---------|------------|
| Verify PASS, analyze FAULT | Authentic file; run broke a rule/heuristic | Review process/agent; fix or accept risk |
| Verify FAIL | File integrity/signature problem | Do not use as evidence; re-record |
| Analyze: heuristic_only | No valid `epi_policy.json` at seal | `epi policy init`; re-run from project dir |
| Analyze: no steps | Empty / uninstrumented recording | Use `record()` / wrappers properly |
| Demo flags R004-style secret pattern | Sample is built to exercise prohibition | Expected for demo; not “EPI is broken” |
| Policy file invalid | Warning; seal continues without formal policy | `epi policy validate` / `lint` |

---

## 12. Security and privacy notes

- Policy files are usually **not secret**, but may describe internal controls — treat as internal docs.  
- Prohibition rules scan **recorded content**; redaction at record time may already strip secrets (see redaction defaults). Demo content may still include **deliberate** secret-like strings for testing.  
- Private browser verify does not upload the file; analysis for `epi analyze` uses the **local** `.epi` you already have.

---

## 13. Related documentation

| Doc | Use when |
|-----|----------|
| [POLICY.md](./POLICY.md) | Full policy schema and authoring detail |
| [USAGE_GUIDE.md](./USAGE_GUIDE.md) | Install, record, verify basics |
| [CLI.md](./CLI.md) | Full command reference |
| [AUDITORS-GUIDE.md](./AUDITORS-GUIDE.md) | Independent verification of the file |
| [KNOWN_LIMITATIONS.md](./KNOWN_LIMITATIONS.md) | Product boundaries |
| [PILOT.md](./PILOT.md) | Guided pilot scope |

---

## 14. One-sentence summary

**Policy is the rulebook you write; the fault analyzer grades the sealed step log against that rulebook and built-in heuristics; `epi analyze` / `epi view` show the grade; `epi verify` only proves the file was not tampered with.**

---

*Aligned with source behavior in `epi_core/policy.py`, `epi_core/fault_analyzer.py`, seal path in `epi_core/container.py`, and CLI `epi policy` / `epi analyze`.*
