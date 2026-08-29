"""Python CLI and browser JS must agree on signature_valid for every spec generation.

Two independent verifiers that can silently diverge is a format defect.
This test is not marked browser — release-gate runs pytest -m "not browser".
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
GOLDENS = Path(__file__).resolve().parent / "goldens"
NODE_SCRIPT = REPO / "scripts" / "browser_verify_signature.mjs"

ARTIFACTS = (
    (GOLDENS / "legacy-spec-4.3.0.epi", "4.3.0"),
    (GOLDENS / "legacy-spec-4.4.0.epi", "4.4.0"),
    (GOLDENS / "spec-4.4.3.epi", "4.4.3"),
)


def _python_verify(path: Path) -> dict:
    r = subprocess.run(
        [sys.executable, "-m", "epi_cli", "verify", str(path), "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO),
        timeout=180,
    )
    text = (r.stdout or "") + (r.stderr or "")
    i, j = text.find("{"), text.rfind("}")
    assert i >= 0, text[-600:] or f"rc={r.returncode}"
    return json.loads(text[i : j + 1])


def _browser_verify(path: Path) -> dict:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is required for cross-verifier parity")
    r = subprocess.run(
        [node, str(NODE_SCRIPT), str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO),
        timeout=60,
    )
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    line = (r.stdout or "").strip().splitlines()[-1]
    return json.loads(line)


@pytest.mark.parametrize("path,spec", ARTIFACTS, ids=["4.3.0", "4.4.0", "4.4.3"])
def test_python_and_browser_signature_valid_agree(path: Path, spec: str) -> None:
    assert path.is_file(), f"missing golden {path}"
    py = _python_verify(path)
    facts = py.get("facts") or py
    meta = py.get("metadata") or {}
    assert str(meta.get("spec_version") or "") == spec
    js = _browser_verify(path)
    assert facts.get("signature_valid") is js["signature_valid"], {
        "python": facts.get("signature_valid"),
        "browser": js.get("signature_valid"),
        "browser_raw": js,
        "decision": py.get("decision"),
    }
    assert facts.get("signature_valid") is True
