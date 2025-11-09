# EPI Demo - Public trimmed demo

This demo repo shows a safe, minimal public surface of Evidence Packaged Infrastructure (EPI).
It intentionally redacts cryptographic signing, packaging internals, advanced OpenAI patching,
and the full test suite. Those components remain private.

## What's included
- `demo/api_demo.py` — runnable demo that writes a minimal `.epi`-like folder.
- `examples/` — simplified examples that use `demo/api_demo.py`.
- `ARCHITECTURE.md` — high-level architecture and mermaid diagram.
- `PRIVATE_COMPONENTS.md` — lists private components that are intentionally redacted.

## Run the demo
```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
python demo/api_demo.py
# Inspect demo_output_basic folder
```

## What is redacted

See `PRIVATE_COMPONENTS.md`. Short list: signing keys, keygen, packaging internals, full CI tests, distribution artifacts.

## Request full source

Full source and enterprise features available under NDA. Contact: afridiibrahim41@gmail.com
