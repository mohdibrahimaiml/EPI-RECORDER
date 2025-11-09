# EPI Demo - Evidence Package Infrastructure

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-production-green.svg)]()

**Live examples of the EPI (Evidence Package Infrastructure) format** - The universal standard for AI workflow reproducibility.

> 🎯 **What is EPI?** Think of it as "PDF for AI workflows" - self-contained, cryptographically signed packages that capture everything about an AI interaction: prompts, responses, environment, timing, and metadata.

---

## 🚀 Quick Start

### Try It Now

```bash
# Clone this repo
git clone https://github.com/mohdibrahimaiml/epi-demo.git
cd epi-demo

# Install epi-recorder
pip install epi-recorder

# Run the demo (creates 3 signed .epi files)
python demo/real_demo.py

# Verify cryptographic signatures
epi verify basic-usage/basic-usage.epi
```

**Output:**
```
✅ Trust Level: HIGH
✅ Signature: Valid (key: default)
✅ Integrity: Verified (2 files)
```

---

## 📦 What's Included

### 3 Working Examples (All Cryptographically Signed)

#### 1. **basic-usage/** - Simple Chat Completion
```python
# Single API call recording
with record("basic-usage.epi", workflow_name="Basic Chat") as epi:
    epi.log_step("llm.request", {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Explain quantum computing"}]
    })
    epi.log_step("llm.response", {...})
```

- ✅ Request/response capture
- ✅ Model configuration
- ✅ Token usage tracking
- 📊 **Size:** 7.1 KB (fully signed)

#### 2. **openai-streaming/** - Streaming Response
```python
# Streaming chat completion
with record("streaming.epi", workflow_name="Streaming Chat") as epi:
    epi.log_step("llm.request", {"stream": True, ...})
    for chunk in stream:
        epi.log_step("llm.stream_chunk", {"delta": chunk})
```

- ✅ Token-by-token capture
- ✅ Real-time streaming
- ✅ Latency measurement
- 📊 **Size:** 7.0 KB

#### 3. **multi-turn/** - Conversation Flow
```python
# Multi-turn conversation
with record("conversation.epi", workflow_name="Multi-Turn") as epi:
    # Turn 1
    epi.log_step("llm.request", {...})
    epi.log_step("llm.response", {...})
    # Turn 2
    epi.log_step("llm.request", {...})  # with history
    epi.log_step("llm.response", {...})
```

- ✅ Context maintenance
- ✅ Message history
- ✅ Complete interaction flow
- 📊 **Size:** 7.2 KB

---

## 🔐 Real Production Features

All examples use the **production epi-recorder package** with:

### Cryptographic Security
- **Ed25519 Signatures** - 256-bit elliptic curve cryptography
- **Public/Private Keys** - Secure key management
- **Tamper Detection** - Any modification invalidates signature

### Integrity Verification
- **SHA-256 Hashing** - Every file content-addressed
- **Manifest Validation** - JSON schema enforcement
- **File Integrity** - Automatic verification

### Environment Capture
```json
{
  "platform": {"system": "Windows", "version": "10.0.19045"},
  "python": {"version": "3.11.9"},
  "packages": {"openai": "1.52.0", "pydantic": "2.9.2", ...}
}
```

### ZIP Archive Structure
```
example.epi (ZIP archive)
├── mimetype                 # "application/vnd.epi+zip"
├── manifest.json            # Metadata + signatures
├── steps.jsonl              # Workflow steps (JSON Lines)
└── environment.json         # System snapshot
```

---

## 📖 Usage Examples

### Verify Any .epi File
```bash
epi verify basic-usage/basic-usage.epi
```

### View in Browser
```bash
epi view basic-usage/basic-usage.epi
# Opens interactive timeline viewer
```

### Inspect Manually
```bash
# Extract archive
python -m zipfile -e basic-usage/basic-usage.epi extracted/

# View manifest
python -c "import zipfile, json; print(json.dumps(json.loads(zipfile.ZipFile('basic-usage/basic-usage.epi').read('manifest.json')), indent=2))"
```

### Create Your Own
```python
from epi_recorder import record

with record("my_workflow.epi", workflow_name="My AI App") as epi:
    # Your AI code here
    epi.log_step("data.loaded", {"rows": 1000})
    
    # Make OpenAI call (auto-captured if using OpenAI SDK)
    response = openai.chat.completions.create(...)
    
    # Or log manually
    epi.log_step("llm.response", {"content": response.text})
```

---

## 🎯 Use Cases

### 🔬 **Research & Development**
- Reproduce experiments exactly
- Share verifiable results
- Peer review with proof

### 🏢 **Enterprise AI**
- Audit trails for compliance (EU AI Act, SOC-2)
- Debug production failures
- Version control for AI systems

### 🐛 **Debugging & Testing**
- Capture failing interactions
- Regression tests from recordings
- Replay workflows offline

### 📊 **Monitoring & Analytics**
- Track model performance
- Cost analysis
- Token usage patterns

---

## 🛠️ Installation

### From PyPI (Recommended)
```bash
pip install epi-recorder
```

### From Source
```bash
git clone https://github.com/yourusername/epi-recorder.git
cd epi-recorder
pip install -e .
```

### Requirements
- Python 3.11+
- Windows, macOS, or Linux

---

## 📚 Documentation

### Core Commands
```bash
epi record --out run.epi -- python script.py  # Record CLI execution
epi verify run.epi                             # Verify signature
epi view run.epi                               # Open in browser
epi keys list                                  # Manage signing keys
```

### Python API
```python
from epi_recorder import record

# Basic usage
with record("output.epi", workflow_name="Demo"):
    # Your code here
    pass

# Advanced usage
with record("output.epi", 
            workflow_name="Advanced",
            tags=["v1.0", "prod"],
            auto_sign=True) as epi:
    
    epi.log_step("custom_step", {"data": "value"})
    epi.log_artifact(Path("output.txt"))
```

---

## 🧪 Testing

### Run Demo
```bash
python demo/real_demo.py
```

### Run Tests
```bash
python test_demo.py
```

**Expected Output:**
```
🧪 EPI Demo Test Suite
============================================================
Testing 5 .epi files...

✅ PASS: demo/basic_demo.epi
✅ PASS: demo/multi_step_demo.epi
✅ PASS: basic-usage/basic-usage.epi
✅ PASS: openai-streaming/openai-streaming.epi
✅ PASS: multi-turn/multi-turn.epi

5/5 tests passed

🎉 ALL TESTS PASSED! Demo is fully functional.
```

---

## 📄 File Format Specification

### Manifest Structure
```json
{
  "spec_version": "1.0",
  "session_id": "uuid-here",
  "workflow_name": "Demo Workflow",
  "created_at": "2025-11-06T10:30:00Z",
  "duration": 2.34,
  "step_count": 5,
  "files": {
    "steps.jsonl": {
      "sha256": "abc123...",
      "size": 1234
    }
  },
  "signature": {
    "algorithm": "ed25519",
    "public_key": "base64...",
    "signature": "base64..."
  }
}
```

### Steps Format (JSONL)
```json
{"kind": "session.start", "content": {...}, "timestamp": "2025-11-06T10:30:00Z"}
{"kind": "llm.request", "content": {...}, "timestamp": "2025-11-06T10:30:01Z"}
{"kind": "llm.response", "content": {...}, "timestamp": "2025-11-06T10:30:03Z"}
{"kind": "session.end", "content": {...}, "timestamp": "2025-11-06T10:30:05Z"}
```

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

---

## 📞 Contact & Support

- **Email:** afridiibrahim41@gmail.com
- **Issues:** [GitHub Issues](https://github.com/mohdibrahimaiml/epi-demo/issues)
- **Discussions:** [GitHub Discussions](https://github.com/mohdibrahimaiml/epi-demo/discussions)

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with:
- [Pydantic](https://pydantic.dev/) - Data validation
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [cryptography](https://cryptography.io/) - Ed25519 signatures

---

## 🌟 Star History

If you find EPI useful, please ⭐ star the repository!

---

## 🔗 Related Projects

- **epi-recorder** - Main package (production-ready)
- **epi-viewer** - Web-based .epi file viewer
- **epi-tools** - Additional utilities

---

**Made with ❤️ for the AI community**

*Turning opaque AI workflows into transparent, verifiable evidence packages.*
