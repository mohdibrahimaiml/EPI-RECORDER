<p align="center">
  <img src="https://raw.githubusercontent.com/mohdibrahimaiml/epi-recorder/main/docs/assets/logo.png" alt="EPI Logo" width="180"/>
  <br>
  <h1 align="center">EPI</h1>
  <p align="center"><strong>Verifiable Execution Evidence for AI Systems / AI Agents</strong></p>
  <p align="center">
    <em>A portable, cryptographically sealed artifact format for AI execution records.</em>
  </p>
</p>

<p align="center">
  <a href="https://pypi.org/project/epi-recorder/"><img src="https://img.shields.io/pypi/v/epi-recorder?style=for-the-badge&color=00d4ff&label=PyPI" alt="PyPI"/></a>
  <a href="https://github.com/mohdibrahimaiml/epi-recorder"><img src="https://img.shields.io/badge/python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="License"/></a>
</p>

---

## What is EPI?

EPI (Evidence Package for AI) is a **file format** for capturing and verifying AI execution evidence.

An `.epi` file is to AI execution what PDF is to documents:
- **Self-contained** — prompts, responses, environment, viewer — all in one file
- **Universally viewable** — opens in any browser, no software required
- **Tamper-evident** — Ed25519 signatures prove the record wasn't altered

EPI is designed for **adversarial review**: audits, incident response, compliance, litigation.

---

## Design Guarantees

EPI artifacts provide the following guarantees:

| Guarantee | Implementation |
|:----------|:---------------|
| **Explicitness** | Evidence capture is intentional and reviewable in source code |
| **Portability** | Single file, no external dependencies, works offline |
| **Offline Verifiability** | Signature verification requires no network or cloud services |
| **Adversarial Review** | Format assumes the reviewer does not trust the producer |

These are not features. They are **constraints** that define what EPI is.

---

## Quick Start

```bash
pip install epi-recorder
```

### Capture Evidence (Explicit API)

```python
from epi_recorder import record

with record("evidence.epi") as epi:
    response = client.chat.completions.create(model="gpt-4", messages=[...])
    epi.log_llm_call(response)  # Explicit capture
```

### Capture Evidence (Wrapper Client)

```python
from epi_recorder import record, wrap_openai
from openai import OpenAI

client = wrap_openai(OpenAI())

with record("evidence.epi"):
    response = client.chat.completions.create(...)  # Captured via wrapper
```

### Verify Evidence

```bash
epi verify evidence.epi
```

---

## The `.epi` Artifact Format

An `.epi` file is a ZIP archive with a defined structure. See [docs/EPI-SPEC.md](docs/EPI-SPEC.md) for the full specification.

```
evidence.epi
├── mimetype              # "application/epi+zip"
├── manifest.json         # Metadata + Ed25519 signature
├── steps.jsonl           # Execution steps (NDJSON)
├── env.json              # Runtime environment snapshot
└── viewer/
    └── index.html        # Self-contained offline viewer
```

The embedded viewer allows any recipient to:
- View the complete execution timeline
- Verify cryptographic integrity
- Inspect individual steps

No software installation required.

---

## CLI Reference

### Primary Commands

| Command | Purpose |
|:--------|:--------|
| `epi run <script.py>` | Capture execution evidence to `.epi` |
| `epi verify <file.epi>` | Verify artifact integrity and signature |
| `epi view <file.epi>` | Open artifact in browser viewer |
| `epi keys list` | Manage signing keys |

### Secondary Tools

These tools consume evidence artifacts for analysis:

| Command | Purpose |
|:--------|:--------|
| `epi debug <file.epi>` | Heuristic analysis (loops, errors, inefficiencies) |
| `epi chat <file.epi>` | Natural language querying via LLM |

> **Note:** `debug` and `chat` are convenience tools built on top of the evidence format.
> They are not part of the core specification.

---

## Cryptographic Properties

| Property | Implementation |
|:---------|:---------------|
| **Signatures** | Ed25519 (RFC 8032) |
| **Hashing** | SHA-256 content addressing |
| **Key Storage** | Local keyring, user-controlled |
| **Verification** | Client-side, zero external dependencies |

Signatures are **optional but recommended**. Unsigned artifacts are still valid but cannot prove origin.

---

## When to Use EPI

### Appropriate Use Cases

- Post-incident forensics
- Compliance documentation
- Audit trails for autonomous systems
- Reproducibility evidence for research
- Litigation-grade execution records

### Not Designed For

- Real-time monitoring dashboards
- High-frequency telemetry
- System health metrics
- Application performance monitoring

EPI produces **artifacts**, not **streams**.

---

## Supported Providers

| Provider | Capture Method |
|:---------|:---------------|
| OpenAI | Wrapper client or explicit API |
| Anthropic | Explicit API |
| Google Gemini | Explicit API |
| Any HTTP-based LLM | Explicit API via `log_llm_call()` |

EPI does not depend on provider-specific integrations. The explicit API works with any response format.

---

## v2.3.0 — Design Correction

This release corrects EPI's evidence capture model.

| Before (v2.2.x) | After (v2.3.0) |
|:----------------|:---------------|
| Implicit monkey-patching | Explicit capture |
| Fragile to SDK changes | Stable across versions |
| Hidden instrumentation | Reviewable in source |

**Rationale:** Evidence systems must be intentional. Implicit capture was convenient but violated the explicitness guarantee.

**Migration:** Replace implicit capture with `epi.log_llm_call(response)` or `wrap_openai()`.

**Legacy mode:** `record(legacy_patching=True)` is deprecated and will be removed in v3.0.

---

## Release History

### 2.3.0 — The "Explicitness" Update (Current)
**Released:** February 6, 2026
**Theme:** *Design Correction & Stability*

**The Problem:** Previous versions relied on "Implicit Monkey Patching" (automatically intercepting library calls). This was convenient but fragile—if OpenAI updated their SDK, interception could break silently. It also violated the core principle of evidence: "Nothing should happen by magic."
**The Improvement:**
*   **Explicit API (`log_llm_call`)**: Introduced a direct way to log evidence. This is 100% stable and will never break when libraries update.
*   **Wrapper Clients**: Added `wrap_openai()` and `TracedOpenAI` so you can add evidence capture with a single line of code change, rather than implicit magic.
*   **Significance:** Shifts EPI from a "Logger" to a true "Evidence System" where every capture is an intentional, code-reviewed act.

### 2.2.1 — The "Fidelity" Update
**Released:** February 6, 2026
**Theme:** *Error Visibility & Fixes*

**The Problem:** The Viewer didn't clearly distinguish between a successful HTTP call and a failed one. Also, `steps.jsonl` creation had edge cases where it might not initialize instantly.
**The Improvement:**
*   **Error Visualization:** The Viewer now renders `llm.error`, `http.error` in distinct red badges. You can see *exactly* why an agent failed (e.g., 401 Unauthorized or Context Length Exceeded).
*   **Initialization Fixes:** Guaranteed `steps.jsonl` creation to prevent "missing file" errors on very short scripts.

### 2.2.0 — The "Architecture" Update
**Released:** January 30, 2026
**Theme:** *Crash Safety & Async*

**The Problem:**
1.  **Crash Risk:** Early versions wrote JSONs at the end. If the process crashed (OOM), evidence was lost.
2.  **Concurrency:** Global state made it hard to record async agents handling multiple requests.
**The Improvement:**
*   **SQLite WAL Storage:** Moved to a Write-Ahead-Log database. Every step is an atomic transaction. If the plug is pulled, the evidence survives.
*   **Async Native:** Introduced `ContextVars` for thread-safety and an `AsyncRecorder` that doesn't block the main event loop.
*   **Significance:** This made EPI "Production Ready" for high-concurrency backend agents.

### 2.1.3 — The "Gemini" Update
**Released:** January 24, 2026
**Theme:** *Model Support & Querying*

**The Problem:** EPI only supported OpenAI. Also, finding things in large logs was hard.
**The Improvement:**
*   **Google Gemini Support:** Added native patching for `google.generativeai`.
*   **`epi chat`:** Added a CLI tool to "talk" to your evidence. You can ask "Why did the agent fail?" and it queries the `.epi` file content using an LLM.

### 2.1.2 — The "Trust" Update
**Released:** January 17, 2026
**Theme:** *Security Verification*

**The Problem:** The `.epi` file was just a container. Verification was server-side or CLI-only.
**The Improvement:**
*   **Client-Side Verification:** The Embedded Viewer (HTML) received a JavaScript crypto library (`noble-ed25519`). It verifies the file *inside the browser*.
*   **Canonical Serialization:** Fixed hashing issues across different OSs (Windows/Linux) by enforcing JSON/CBOR canonical sorting.
*   **Significance:** You could now send an `.epi` file to a regulator, and they could verify it in their browser without installing Python.

### 2.1.1 — The "Windows" Update
**Released:** December 16, 2025
**Theme:** *Cross-Platform Polish*

**The Problem:** Windows users faced `PATH` issues (command not found) and Unicode errors (crash on emojis).
**The Improvement:**
*   **Auto-Repair:** `epi_postinstall.py` was added to automatically fix Windows Registry `PATH` variables.
*   **Terminal Fixes:** Forced UTF-8 output in the CLI to handle emojis on Windows PowerShell/CMD.
*   **`epi doctor`**: Added a self-diagnostic command to debug install issues.

### 1.0.0 — The "Genesis" Update
**Released:** December 15, 2025
**Theme:** *The MVP*

**The Beginning:** The first release to the world.
**Key Features:**
*   Defined the `.epi` ZIP format.
*   Implemented Ed25519 signing from day one.
*   Created the first "Self-Contained Viewer" concept.
*   **Significance:** Proved that AI logs could be treated as *artifacts* rather than just text streams.

See [CHANGELOG.md](./CHANGELOG.md) for full details.

---

## Contributing

```bash
git clone https://github.com/mohdibrahimaiml/epi-recorder.git
cd epi-recorder
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

## License

MIT License. See [LICENSE](./LICENSE).
