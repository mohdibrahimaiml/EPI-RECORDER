# EPI Demo Repository

Welcome! This repository contains example `.epi` recordings that demonstrate the Extended Prompt Interaction (EPI) format.

## What is EPI?

EPI is a standardized format for recording, replaying, and analyzing AI API interactions. Think of it as "video recording for AI conversations" — capturing the full context, timing, and behavior of LLM interactions in a shareable, auditable format.

## Quick Start

### View Online
Drag any `.epi` file to the [EPI Viewer](https://epi-viewer.example.com)

### View Locally
```bash
pip install epi-recorder
epi view basic-usage/basic-usage.epi
```

### Record Your Own
```bash
# Install
pip install epi-recorder

# Record in Python
from epi_recorder import Recorder
import openai

with Recorder("my-interaction.epi"):
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
```

## Demo Files

### 🎯 [basic-usage/](./basic-usage)
Simple chat completion demonstrating core recording capabilities.
- Single API call
- Request/response capture
- Model configuration

### 🌊 [openai-streaming/](./openai-streaming)
Streaming chat completion with real-time token delivery.
- SSE stream capture
- Token-by-token replay
- Latency measurement

### 💬 [multi-turn/](./multi-turn)
Complete conversation with context and follow-ups.
- Multiple API calls
- Message history
- Conversation flow

## File Format

Each `.epi` file is a signed ZIP archive containing:
- `manifest.json` — Metadata and step sequence
- `steps/` — Individual interaction steps (requests/responses)
- `context/` — Environment and configuration data
- `signature.json` — Cryptographic signature (optional)

## Use Cases

- **Debugging**: Capture and replay failing interactions
- **Testing**: Regression tests from real interactions
- **Documentation**: Executable API examples
- **Auditing**: Compliance and quality assurance
- **Research**: Dataset collection and analysis

## Toolchain

```bash
# View recording
epi view my-file.epi

# Validate format
epi check my-file.epi

# Replay interaction
epi replay my-file.epi

# Compare recordings
epi diff file1.epi file2.epi
```

## Learn More

- [EPI Format Specification](https://github.com/EPI-spec/spec)
- [EPI Recorder (Python)](https://github.com/yourusername/epi-recorder)
- [EPI Viewer](https://epi-viewer.example.com)
- [Integration Guides](https://docs.epi-format.org)

## Contributing

Found an issue or want to add more demos? Pull requests welcome!

## License

Demo files are provided as examples under CC0 (public domain).
