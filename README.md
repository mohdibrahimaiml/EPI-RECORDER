# EPI Recorder

**Debug AI agents like a black box.**

When your LangChain/CrewAI agent hallucinates, loops, or crashes—EPI shows you exactly which step failed.

[![PyPI Version](https://img.shields.io/pypi/v/epi-recorder)](https://pypi.org/project/epi-recorder/)
[![Python Support](https://img.shields.io/pypi/pyversions/epi-recorder)](https://pypi.org/project/epi-recorder/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## One Command

```bash
pip install epi-recorder
epi run your_agent.py
```

## Why

- **Zero config:** No code changes required
- **Mistake detection:** Finds infinite loops & hallucinations automatically  
- **Portable:** `.epi` files work offline
- **Thread-safe:** Single-agent workflows (multi-agent via separate processes)

## Quick Start

```python
from epi_recorder import record

with record():
    # Your agent code here
    agent.run("task")
```

Then debug:

```bash
epi view output.epi
```

## Debug Your Agent

When your agent fails, find out exactly why:

```bash
epi debug agent_session.epi
```

EPI will analyze the execution and identify:
- **Infinite loops** - repeated tool calls
- **Hallucinations** - LLM errors leading to tool failures
- **Inefficiencies** - excessive token usage for simple tasks

## How It Works

1. **Record** - Wrap your agent code with `epi run` or the `record()` context manager
2. **Capture** - EPI intercepts all LLM API calls (OpenAI, Gemini, etc.)
3. **Analyze** - Run `epi debug` to find exactly where things went wrong
4. **Fix** - Get actionable suggestions for each detected issue

## Tech

- Python 3.11+
- SQLite storage (atomic, crash-safe)
- Async-native
- Ed25519 integrity signatures

## Installation

```bash
pip install epi-recorder
```

## Examples

See [`examples/`](./examples) for working demos including:
- LangChain agent recording
- CrewAI workflow debugging
- OpenAI function calling traces

## Contributing

```bash
git clone https://github.com/mohdibrahimaiml/EPI-V2.1.2
cd epi-recorder
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## Community

- [GitHub Issues](https://github.com/mohdibrahimaiml/EPI-V2.1.2/issues) - Report bugs
- [Discussions](https://github.com/mohdibrahimaiml/EPI-V2.1.2/discussions) - Ask questions
- [Changelog](./CHANGELOG.md) - Release history

## License

MIT License - See [LICENSE](./LICENSE) for details.

---

**Built for developers who debug AI agents at 3am.**
