from __future__ import annotations

from uuid import uuid4

import pytest

from epi_recorder.integrations.langchain import EPICallbackHandler


class _DummySession:
    def __init__(self):
        self.logged: list[tuple[str, dict]] = []

    def log_step(self, kind: str, payload: dict) -> None:
        self.logged.append((kind, payload))


def test_on_chain_start_tolerates_missing_serialized_payload(monkeypatch):
    with pytest.warns(DeprecationWarning, match="deprecated"):
        handler = EPICallbackHandler()
    session = _DummySession()
    monkeypatch.setattr(handler, "_get_session", lambda: session)

    handler.on_chain_start(
        None,
        {"text": "Quarterly financial report"},
        run_id=uuid4(),
    )

    assert session.logged
    kind, payload = session.logged[0]
    assert kind == "chain.start"
    # Missing serialized payload falls back to default chain name
    assert payload["name"] in ("unknown", "chain")
    assert "text" in payload["inputs"]


def test_tool_callbacks_emit_native_epi_tool_steps(monkeypatch):
    with pytest.warns(DeprecationWarning, match="deprecated"):
        handler = EPICallbackHandler()
    session = _DummySession()
    monkeypatch.setattr(handler, "_get_session", lambda: session)
    run_id = uuid4()

    handler.on_tool_start(
        {"name": "lookup_order"},
        '{"order_id":"123"}',
        run_id=run_id,
    )
    handler.on_tool_end({"status": "paid"}, run_id=run_id)

    assert [kind for kind, _ in session.logged] == ["tool.call", "tool.response"]
    assert session.logged[0][1]["tool"] == "lookup_order"
    assert session.logged[1][1]["tool"] == "lookup_order"
    # Canonical adapter uses ok=True (legacy status=success removed)
    assert session.logged[1][1].get("ok") is True
    assert session.logged[1][1].get("call_id") == str(run_id)


def test_deprecated_alias_accepts_explicit_session():
    session = _DummySession()
    with pytest.warns(DeprecationWarning, match="adapters.langchain"):
        handler = EPICallbackHandler(session)
    rid = uuid4()
    handler.on_tool_start({"name": "t"}, "x", run_id=rid)
    handler.on_tool_error(RuntimeError("boom"), run_id=rid)
    assert [k for k, _ in session.logged] == ["tool.call", "tool.response"]
    assert session.logged[1][1]["ok"] is False
