"""Sealed step payloads are full; viewer preview is display-only."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from epi_core.container import EPIContainer
from epi_core.schemas import ManifestModel
from epi_core.serialize import get_canonical_hash
from epi_core.trust import sealed_payload_gate
from epi_recorder.patcher import RecordingContext


def test_long_step_content_is_sealed_in_full(tmp_path: Path) -> None:
    ctx = RecordingContext(tmp_path, enable_redaction=False)
    payload = "Z" * 5000
    ctx.add_step("llm.response", {"text": payload})
    ctx.finalize()
    line = (tmp_path / "steps.jsonl").read_text(encoding="utf-8").strip().splitlines()[-1]
    step = json.loads(line)
    assert step["content"]["text"] == payload
    assert "[...truncated:" not in step["content"]["text"]


def test_pack_asserts_content_truncated_false(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EPI_NOTARIZE", "0")
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "steps.jsonl").write_text(
        json.dumps({"index": 0, "kind": "llm.response", "content": {"text": "ok"}}) + "\n",
        encoding="utf-8",
    )
    out = tmp_path / "full.epi"
    EPIContainer.pack(workspace, ManifestModel(cli_command="test"), out)
    sealed = EPIContainer.read_manifest(out)
    assert sealed.content_truncated is False


def test_sealed_payload_gate_fails_only_when_true() -> None:
    assert sealed_payload_gate(ManifestModel(cli_command="t", content_truncated=True), True) is False
    assert sealed_payload_gate(ManifestModel(cli_command="t", content_truncated=False), True) is True
    assert sealed_payload_gate(ManifestModel(cli_command="t"), True) is True


def test_absent_content_truncated_does_not_change_unsigned_hash() -> None:
    from datetime import datetime, timezone
    from uuid import UUID

    kwargs = {
        "cli_command": "test command",
        "workflow_id": UUID("550e8400-e29b-41d4-a716-446655440000"),
        "created_at": datetime(2026, 1, 15, 10, 30, tzinfo=timezone.utc),
    }
    a = ManifestModel(**kwargs)
    assert a.content_truncated is None
    dumped = a.model_dump()
    assert dumped.get("content_truncated") is None
    h1 = get_canonical_hash(a, exclude_fields={"signature"})
    h2 = get_canonical_hash(ManifestModel(**kwargs), exclude_fields={"signature"})
    assert h1 == h2
