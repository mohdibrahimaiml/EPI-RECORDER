#!/usr/bin/env python3
"""
Runnable LangChain + epi-recorder example (real LLM via Groq when key present).

Requires:
  pip install 'epi-recorder[langchain]' langchain-groq

Environment:
  GROQ_API_KEY  — if unset, prints how to set it and exits non-zero without calling network.

Usage:
  python examples/langchain_loan_agent.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        print(
            "GROQ_API_KEY is not set. Export it to run the live loan-agent example:\n"
            "  set GROQ_API_KEY=gsk_...   # Windows\n"
            "  export GROQ_API_KEY=gsk_...  # Unix\n"
            "Then: python examples/langchain_loan_agent.py",
            file=sys.stderr,
        )
        return 2

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from langchain_groq import ChatGroq
    except ImportError as exc:
        print(
            f"Missing dependency: {exc}\n"
            "Install: pip install 'epi-recorder[langchain]' langchain-groq",
            file=sys.stderr,
        )
        return 2

    from epi_recorder import record
    from epi_recorder.adapters.langchain import EpiCallbackHandler

    out = Path("epi-recordings") / "langchain_loan_agent.epi"
    out.parent.mkdir(parents=True, exist_ok=True)

    with record(out, goal="loan decision") as session:
        handler = EpiCallbackHandler(session)
        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=api_key,
            temperature=0,
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a cautious loan underwriter. Reply with APPROVE or DENY "
                    "and a one-sentence reason. No PII beyond what is given.",
                ),
                (
                    "human",
                    "Applicant income ${income}/yr, credit score {score}, "
                    "requested amount ${amount}. Decision?",
                ),
            ]
        )
        chain = prompt | llm | StrOutputParser()
        result = chain.invoke(
            {"income": "72000", "score": "710", "amount": "15000"},
            config={"callbacks": [handler]},
        )
        print("Model decision:", result)

    print("Artifact:", out.resolve())
    print("Verify with: epi verify", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
