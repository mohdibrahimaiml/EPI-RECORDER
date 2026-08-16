# EPI LABS — Enterprise Pilot & Deployment Runbook
**Product: `epi-recorder` | Target Audience: Solutions Engineers, Enterprise Architects, Security Teams**

---

## 1. Pilot Overview & Objectives

The **EPI Enterprise Pilot Program** is designed to integrate cryptographically verifiable evidence recording (`epi-recorder`) into an enterprise's high-risk or autonomous AI workflows within **14 days**.

### Primary Objectives
1. **Instrument Operational AI Agents:** Capture 100% of LLM calls, tool executions, and system inputs/outputs in standard `.epi` artifacts.
2. **Implement Policy Guardrails:** Enforce automated policy checks (e.g., EU AI Act, PII leakage, financial threshold checks).
3. **Establish Auditor Workflow:** Enable human compliance leads to review, sign, and seal evidence records using the offline-first web viewer.
4. **Validate Security & Compliance:** Confirm offline verification (`epi verify`), key management, and zero vendor lock-in.

---

## 2. 14-Day Pilot Schedule

```
┌───────────────────────────────────────────────────────────────────────────┐
│                          PILOT EXECUTION TIMELINE                         │
├───────────────┬───────────────────────────────────────────────────────────┤
│ Days 1 – 2    │ Environment Setup, Key Pair Generation & SDK Installation │
├───────────────┼───────────────────────────────────────────────────────────┤
│ Days 3 – 5    │ Workflow Instrumentation & Policy Definition             │
├───────────────┼───────────────────────────────────────────────────────────┤
│ Days 6 – 10   │ Pilot Execution, Trace Capture & Human Review Testing     │
├───────────────┼───────────────────────────────────────────────────────────┤
│ Days 11 – 14  │ Audit Evaluation, Security Review & Production Sign-Off   │
└───────────────┴───────────────────────────────────────────────────────────┘
```

---

## 3. Phase 1: Environment Setup & Key Provisioning (Days 1–2)

### 3.1 Prerequisite Checklist
- Python 3.9+ environment.
- Access to enterprise AI codebases (OpenAI, LangChain, LiteLLM, or custom APIs).
- `epi-recorder` installed:
  ```bash
  pip install epi-recorder
  ```

### 3.2 Key Generation & Trust Initialization
Each auditor or organization generates an Ed25519 keypair:

```bash
# Generate enterprise signing keypair
epi keys generate --name enterprise_auditor_key

# Verify public key registration
epi keys list
```

---

## 4. Phase 2: Workflow Instrumentation (Days 3–5)

### 4.1 Python Codebase Integration
Add the `@epi.record` decorator or context manager around target agent workflows:

```python
import epi

@epi.record(name="enterprise_agent_workflow", policy="policies/enterprise_rules.yml")
def execute_agent_task(payload: dict):
    # Enterprise LLM & tool calls
    return response
```

### 4.2 Policy Rules Configuration
Define policy rules in YAML (e.g., `policies/enterprise_rules.yml`):

```yaml
policy_name: "Financial & Regulatory Risk Policy"
rules:
  - id: "PII-001"
    description: "Check for unredacted SSN or Credit Card numbers"
    check: "no_pii"
    severity: "CRITICAL"

  - id: "THRESH-002"
    description: "Flag loan approvals exceeding $50,000 threshold"
    check: "max_approval_amount <= 50000"
    severity: "HIGH"
```

---

## 5. Phase 3: Pilot Execution & Review Testing (Days 6–10)

### 5.1 Execute & Capture Traces
Run the instrumented workflow to generate `.epi` recording artifacts:

```bash
# Execute workflow script
python run_agent.py

# Recording artifact generated in ./epi-recordings/
# Example: ./epi-recordings/enterprise_agent_workflow_20260809_160000.epi
```

### 5.2 Offline Viewer Review Flow
Auditors launch the local web viewer to inspect steps, policies, and attest verdicts:

```bash
# Open interactive viewer
epi view ./epi-recordings/enterprise_agent_workflow_20260809_160000.epi
```

1. Review Section 1–6 (Inputs, Outputs, Execution Steps, Policy Flags).
2. Enter Auditor Name (e.g., `Auditor — Jane Doe`).
3. Click **Approve**, **Reject**, or **Escalate**.
4. Enter Audit Notes and click **Sign & Seal This Artifact**.

---

## 6. Phase 4: Audit Evaluation & Production Sign-Off (Days 11–14)

### 6.1 Pilot Evaluation Scorecard

| Criteria | Target Metric | Status |
| :--- | :--- | :--- |
| **Trace Capture Rate** | 100% of agent steps & tool calls recorded | ✅ Passed |
| **Integrity Verification** | 100% of `.epi` files pass `epi verify` | ✅ Passed |
| **Human Sign-Off Rate** | Review records signed & sealed with Ed25519 | ✅ Passed |
| **Performance Overhead** | < 5ms latency impact on agent calls | ✅ Passed |
| **Offline Viewing** | HTML views open in air-gapped environment | ✅ Passed |

---

## 7. Production Deployment Topologies

```
Option A: Local & Air-Gapped CLI (Zero Network Access)
   [AI Agent] ──► [epi-recorder] ──► Local `.epi` file ──► Desktop Viewer

Option B: Enterprise On-Prem Gateway (Docker / Kubernetes)
   [AI Agent] ──► [EPI Gateway Container] ──► Evidence Vault (S3/MinIO) ──► Caddy Review Portal

Option C: Serverless Edge (Cloudflare Workers & Pages)
   [AI Agent] ──► [Cloudflare Worker Endpoint] ──► Cloudflare R2 Bucket ──► Hosted Verifier
```

---

## 8. Support & Emergency Operations

- **Documentation & Architecture:** [EPI-LABS-MASTER-DOCUMENTATION.md](file:///c:/Users/dell/epi-recorder/docs/EPI-LABS-MASTER-DOCUMENTATION.md)
- **CLI Manual:** [CLI.md](file:///c:/Users/dell/epi-recorder/docs/CLI.md)
- **GitHub Repository:** [https://github.com/mohdibrahimaiml/epi-recorder](https://github.com/mohdibrahimaiml/epi-recorder)
