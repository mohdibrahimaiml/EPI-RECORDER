#!/usr/bin/env python3
"""
Regenerate a DM-safe langchain demo .epi without requiring a live API key.

Uses FakeListLLM so the artifact never needs GROQ_API_KEY in the environment.
Run: python scripts/regen_langchain_demo_epi.py
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from langchain_core.language_models.fake import FakeListLLM

from epi_core.container import EPIContainer
from epi_recorder import record
from epi_recorder.adapters.langchain import EpiCallbackHandler


def main() -> int:
    out = Path("epi-recordings") / "langchain_loan_agent.epi"
    out.parent.mkdir(parents=True, exist_ok=True)

    with record(out, goal="loan decision (demo)", auto_sign=True, redact=True) as session:
        handler = EpiCallbackHandler(session)
        llm = FakeListLLM(
            responses=[
                "APPROVE. Income and credit score support the requested amount."
            ],
            callbacks=[handler],
        )
        decision = llm.invoke(
            "Applicant income $72000/yr, credit score 710, requested amount $15000. Decision?"
        )
        print("decision:", decision)

    # Leak scan (gsk_ / GROQ_API_KEY)
    import tempfile

    inner = Path(tempfile.mkdtemp()) / "inner.zip"
    EPIContainer.extract_inner_payload(out, inner)
    hits = []
    with zipfile.ZipFile(inner) as zf:
        for name in zf.namelist():
            data = zf.read(name)
            if b"gsk_" in data or b"GROQ_API_KEY" in data:
                hits.append(name)
    if hits:
        print("LEAK IN:", hits)
        return 1
    print("CLEAN - no key material found")
    print("Artifact:", out.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
