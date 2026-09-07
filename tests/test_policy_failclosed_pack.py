"""Fail-closed packing: a malformed policy must abort the seal in strict mode.

Regression test for the container.py fix that re-raises PolicyLoadError
instead of swallowing it as analysis_status="error". Without the fix,
packing with EPI_ENFORCE=1 and a broken epi_policy.json "succeeds" with
analysis_status="error" and the caller never learns the policy was bad.
"""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from epi_core.container import EPIContainer
from epi_core.policy import PolicyLoadError
from epi_core.schemas import ManifestModel


def _workspace(tmp_path, policy_text: str | None):
    src = tmp_path / "ws"
    src.mkdir(exist_ok=True)
    (src / "steps.jsonl").write_text('{"index": 0, "kind": "shell.command", "content": {}}\n')
    if policy_text is not None:
        (src / "epi_policy.json").write_text(policy_text)
    return src


def test_pack_malformed_local_policy_strict_raises(tmp_path):
    """EPI_ENFORCE=1 + broken epi_policy.json must raise, not warn-and-pack."""
    src = _workspace(tmp_path, "{not valid json")
    manifest = ManifestModel()
    with patch.dict(os.environ, {"EPI_ENFORCE": "1"}):
        with pytest.raises(PolicyLoadError):
            EPIContainer._pack_zip_payload(src, manifest, tmp_path / "payload.zip")


def test_pack_malformed_local_policy_nonstrict_packs_with_failed_status(tmp_path):
    """Without strict mode the same broken file must not abort packing."""
    src = _workspace(tmp_path, "{not valid json")
    manifest = ManifestModel()
    env = {k: v for k, v in os.environ.items() if k != "EPI_ENFORCE"}
    with patch.dict(os.environ, env, clear=True):
        EPIContainer._pack_zip_payload(src, manifest, tmp_path / "payload.zip")
    assert manifest.policy_load_status == "failed"
