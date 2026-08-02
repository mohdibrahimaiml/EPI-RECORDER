from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from epi_recorder.integrations.langchain import EPICallbackHandler
from epi_recorder.integrations.litellm import EPICallback
from epi_recorder.integrations.opentelemetry import EPISpanExporter


pytestmark = pytest.mark.unit


class _Session:
    def __init__(self):
        self.logged: list[tuple[str, dict]] = []

    def log_step(self, kind: str, payload: dict) -> None:
        self.logged.append((kind, payload))


def test_langchain_handler_captures_llm_tool_and_chain_events(monkeypatch):
    """Legacy EPICallbackHandler is a deprecated alias of adapters.EpiCallbackHandler."""
    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        handler = EPICallbackHandler()
    assert any(issubclass(x.category, DeprecationWarning) for x in w)

    session = _Session()
    monkeypatch.setattr(handler, "_get_session", lambda: session)

    llm_run = uuid4()
    tool_run = uuid4()
    chain_run = uuid4()

    handler.on_llm_start({"name": "offline-llm"}, ["prompt"], run_id=llm_run)
    handler.on_llm_end(SimpleNamespace(generations=[]), run_id=llm_run)
    handler.on_tool_start({"name": "lookup"}, "{}", run_id=tool_run)
    handler.on_tool_end({"ok": True}, run_id=tool_run)
    handler.on_chain_start({"name": "chain"}, {"question": "refund"}, run_id=chain_run)
    handler.on_chain_end({"answer": "review"}, run_id=chain_run)

    assert [kind for kind, _ in session.logged] == [
        "llm.call",
        "llm.response",
        "tool.call",
        "tool.response",
        "chain.start",
        "chain.end",
    ]


def test_litellm_provider_samples_resolve_without_live_provider_calls():
    callback = EPICallback()
    samples = {
        "openai/gpt-4o-mini": "openai",
        "anthropic/claude-3-5-sonnet": "anthropic",
        "ollama/llama3.2": "ollama",
        "bedrock/anthropic.claude-3-sonnet": "bedrock",
        "azure/gpt-4o": "azure",
        "gemini/gemini-1.5-pro": "gemini",
        "mistral/mistral-large": "mistral",
        "groq/llama-3.1-70b": "groq",
        "cohere/command-r": "cohere",
        "huggingface/meta-llama": "huggingface",
    }

    for model, provider in samples.items():
        assert callback._extract_provider({"model": model}) == provider


def test_otel_span_to_epi_conversion_maps_llm_tool_and_generic_spans():
    exporter = EPISpanExporter.__new__(EPISpanExporter)

    llm_span = SimpleNamespace(
        name="chat",
        attributes={"gen_ai.request.model": "offline", "gen_ai.system": "local"},
        status=None,
    )
    tool_span = SimpleNamespace(
        name="tool.lookup",
        attributes={"tool.name": "lookup"},
        status=None,
    )
    generic_span = SimpleNamespace(name="agent.step", attributes={}, status=None)

    assert exporter._infer_step_kind(llm_span) == "llm.response"
    assert exporter._infer_step_kind(tool_span) == "tool.response"
    assert exporter._extract_tool_name(tool_span) == "lookup"
    assert exporter._infer_step_kind(generic_span) == "span.end"
