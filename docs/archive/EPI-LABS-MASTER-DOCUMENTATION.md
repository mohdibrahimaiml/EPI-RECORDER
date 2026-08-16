# EPI LABS — Master Technical & Enterprise System Documentation
**Product: `epi-recorder` | Version: v4.2.0 | Standard: EPI Evidence Container Format v1.1**

---

## Executive Summary

**EPI Labs** provides the open cryptographic evidence recording and forensic auditability infrastructure for Autonomous AI Systems. 

As AI agents increasingly execute high-stakes operational workflows—such as financial loan underwriting, insurance claim adjudication, automated code deployment, and healthcare clinical triage—they operate with non-deterministic model calls and complex tool invocations. When policy breaches, hallucinations, or operational failures occur, traditional application logging is insufficient for legal, compliance, and regulatory audits.

**`epi-recorder`** solves the "AI Accountability Black Box" by producing self-contained, portable, self-viewing, and cryptographically sealed evidence artifacts (`.epi` files).

```
   ┌────────────────┐      ┌─────────────────────────┐      ┌────────────────────────┐
   │ Autonomous AI  │ ───► │  `epi-recorder` SDK/CLI │ ───► │ Cryptographic Artifact │
   │ Agent Workflow │      │  Auto-Trace & Policy    │      │    `recording.epi`     │
   └────────────────┘      └─────────────────────────┘      └────────────────────────┘
                                                                         │
                                                                         ▼
                                                            ┌────────────────────────┐
                                                            │ Offline Self-Viewing   │
                                                            │ Forensic & Audit UI    │
                                                            │ (`viewer.html` / CLI)  │
                                                            └────────────────────────┘
```

---

## 1. System Architecture & `epi-recorder` Design

### 1.1 Core Principles

1. **Zero Vendor Lock-In (Self-Viewing Artifacts):** Every `.epi` artifact contains an embedded, offline-first HTML browser UI (`viewer.html`). Regulators, legal counsel, and third-party auditors can double-click a `.epi` file or open it in any standard web browser without installing server backends or database dependencies.
2. **Cryptographic Non-Repudiation:** Evidence payloads are sealed using SHA-256 Merkle-like canonical hashing and signed with Ed25519 or ECDSA public-key cryptography.
3. **Human Oversight & Attestation (Model A Ledger):** Human auditors can review flagged agent steps, record verdicts, and append cryptographically signed review records directly onto the evidence ledger.
4. **Zero-Latency Async Recorder:** Designed for zero runtime overhead on production AI workloads via asynchronous non-blocking event buffers.

---

## 2. `.epi` Evidence Container Specification

A `.epi` container is a portable ZIP archive adhering to the EPI Evidence Specification v1.1.

```
recording.epi (ZIP Archive)
├── manifest.json       # Cryptographic manifest, signature, & file hashes
├── trace.jsonl          # Step-by-step execution trace (inputs, outputs, tools)
├── policy_eval.json     # Policy evaluation results & guardrail checks
├── review.json          # Human review ledger & attestation records
├── environment.json     # Execution environment snapshot (Python, OS, packages, git hash)
└── viewer.html          # Embedded offline forensic presentation UI
```

### 2.1 File Manifest (`manifest.json`)
The `manifest.json` file serves as the root cryptographic contract:

```json
{
  "epi_version": "4.2.0",
  "container_version": "1.1",
  "created_at": "2026-08-09T16:00:00Z",
  "signer_identity": "auditor@epilabs.org",
  "public_key_fingerprint": "ed25519:a1b2c3d4...",
  "signature_algorithm": "ed25519",
  "payload_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "file_manifest": {
    "trace.jsonl": "5a91b4...",
    "policy_eval.json": "8c2d1e...",
    "environment.json": "9f3a7b...",
    "review.json": "1b4c9e..."
  },
  "signature": "3045022100..."
}
```

### 2.2 Canonical Hashing Algorithm
1. The `payload_sha256` is calculated over the canonical byte streams of `trace.jsonl`, `policy_eval.json`, `environment.json`, and `review.json`.
2. The `signature` is generated over `payload_sha256` using the signer's private Ed25519 key.
3. Any byte modification to the trace, policies, or review records causes immediate verification failure in both CLI (`epi verify`) and the offline browser viewer.

### 2.3 Review Ledger & Outcome Mapping
Human auditor actions map directly to standardized audit ledger codes:

| Auditor UI Verdict | Internal Ledger Outcome | Meaning in Audit Trail | UI Section 7 Display |
| :--- | :--- | :--- | :--- |
| **Approve** | `dismissed` | Auditor reviewed policy flag and dismissed it | `FLAG CLEARED (APPROVED)` |
| **Reject** | `confirmed_fault` | Auditor confirmed a policy or model violation | `FAULT CONFIRMED (REJECTED)` |
| **Escalate** | `skipped` | Auditor deferred judgment for higher review | `REVIEW SKIPPED` |

---

## 3. Developer Integration & Framework Support

### 3.1 Python Decorator & Context Manager

```python
import epi

# Decorator Usage
@epi.record(name="loan_underwriter", policy="policies/financial_compliance.yml")
def run_underwriter_agent(applicant_data: dict):
    # Agent execution logic
    return result

# Context Manager Usage
with epi.record(name="claim_adjudication") as recorder:
    recorder.log_step(kind="input", data=claim_payload)
    response = call_llm(claim_payload)
    recorder.log_step(kind="output", data=response)
```

### 3.2 Framework Adapters

`epi-recorder` includes native, single-line adapters for major AI frameworks:

* **OpenAI / OpenAI Agents:**
  ```python
  from epi_recorder.integrations.openai_agents import EpiOpenAITracer
  tracer = EpiOpenAITracer()
  ```
* **LangChain & LangGraph:**
  ```python
  from epi_recorder.adapters.langchain import EpiCallbackHandler
  handler = EpiCallbackHandler(recording_name="langchain_workflow")
  agent.run(query, callbacks=[handler])
  ```
* **LiteLLM:**
  ```python
  import litellm
  from epi_recorder.integrations.litellm import EpiLiteLLMLogger
  litellm.success_callback = [EpiLiteLLMLogger()]
  ```
* **Anthropic SDK:**
  ```python
  from epi_recorder.wrappers.anthropic import EpiAnthropicWrapper
  client = EpiAnthropicWrapper(anthropic.Anthropic())
  ```
* **Pytest Test Integration (`pytest-epi`):**
  ```python
  import pytest

  @pytest.mark.epi
  def test_agent_policy_compliance():
      result = run_agent_workflow()
      assert result.status == "approved"
  ```

---

## 4. CLI Command Reference

The `epi` command-line interface manages recordings, verification, policy evaluation, and key distribution:

```bash
# 1. Record a Python script execution
epi record script.py --name loan_adjudication

# 2. Open interactive offline viewer in default browser
epi view docs/assets/demo-insurance-claim-adjudication.epi

# 3. Verify cryptographic integrity & signature
epi verify docs/assets/demo-insurance-claim-adjudication.epi

# 4. Generate Ed25519 signing keypair
epi keys generate --name auditor_key

# 5. Export single standalone HTML file (no dependencies)
epi export-html docs/assets/demo-insurance-claim-adjudication.epi --output report.html

# 6. Evaluate policy compliance rules
epi policy evaluate docs/assets/demo-insurance-claim-adjudication.epi --rules policies/eu_ai_act.yml

# 7. Start local team review server
epi connect open
```

---

## 5. Regulatory Compliance & Standards Mapping

`epi-recorder` provides out-of-the-box alignment with global AI governance standards:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                       REGULATORY ALIGNMENT MATRIX                         │
├───────────────────────┬───────────────────────────────────────────────────┤
│ Standard              │ `epi-recorder` Technical Mechanism                │
├───────────────────────┼───────────────────────────────────────────────────┤
│ EU AI Act Article 12  │ Automatic, tamper-proof event logging throughout  │
│ (Technical Logging)   │ the operational lifecycle of High-Risk AI systems │
├───────────────────────┼───────────────────────────────────────────────────┤
│ EU AI Act Article 14  │ Human oversight attestation interface & Model A   │
│ (Human Oversight)     │ signed review ledger                              │
├───────────────────────┼───────────────────────────────────────────────────┤
│ EU AI Act Annex IV    │ `environment.json` hardware/software snapshot &   │
│ (Technical Doc)       │ complete model parameter & prompt metadata        │
├───────────────────────┼───────────────────────────────────────────────────┤
│ NIST AI RMF           │ Continuous measure/manage audit trace with policy │
│ (Measure & Manage)    │ violation flagging and fault categorization       │
├───────────────────────┼───────────────────────────────────────────────────┤
│ ISO/IEC 42001 (AIMS)  │ Cryptographic non-repudiation and auditability    │
│                       │ for AI management systems                         │
└───────────────────────┴───────────────────────────────────────────────────┘
```

---

## 6. Enterprise Security & Threat Model

`epi-recorder` is designed under a Zero-Trust threat model:

* **Payload Tampering Protection:** Modifying any byte inside `trace.jsonl` or `policy_eval.json` invalidates `payload_sha256` and fails `epi verify`.
* **Signature Replay Prevention:** `manifest.json` binds `created_at`, unique recording ID, and `payload_sha256` to the public key signature.
* **UI Deception Defense:** The embedded browser viewer (`viewer.html`) computes cryptographic hashes on load via Web Crypto API and displays a visual warning banner if file hashes do not match `manifest.json`.
* **PII & Data Redaction:** Configurable regex redactors prevent sensitive user PII (SSNs, API keys, passwords, health data) from entering the recording stream.
