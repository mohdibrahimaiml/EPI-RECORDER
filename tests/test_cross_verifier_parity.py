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
EMBEDDED_SCRIPT = REPO / "scripts" / "browser_verify_embedded.mjs"

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


def _embedded_verify(path: Path) -> dict:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is required for embedded parity")
    r = subprocess.run(
        [node, str(EMBEDDED_SCRIPT), str(path)],
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


@pytest.mark.parametrize("path,spec", ARTIFACTS, ids=["4.3.0", "4.4.0", "4.4.3"])
def test_python_and_embedded_viewer_agree(path: Path, spec: str) -> None:
    """Behavioral parity for the 7th copy: the viewer baked into the .epi must agree with Python."""
    assert path.is_file(), f"missing golden {path}"
    py = _python_verify(path)
    facts = py.get("facts") or py
    meta = py.get("metadata") or {}
    assert str(meta.get("spec_version") or "") == spec
    emb = _embedded_verify(path)
    assert facts.get("signature_valid") is emb["signature_valid"], {
        "python": facts.get("signature_valid"),
        "embedded": emb.get("signature_valid"),
        "embedded_raw": emb,
        "decision": py.get("decision"),
    }
    assert emb["signature_valid"] is True
    assert emb["integrity_ok"] is True


def test_embedded_viewer_rejects_tampered_artifact(tmp_path: Path) -> None:
    """Seal, tamper, and assert embedded viewer and Python both fail."""
    # Seal a minimal artifact via Python
    from epi_core.container import EPIContainer
    from epi_core.schemas import ManifestModel
    from epi_core.keys import KeyManager
    from epi_core.trust import sign_manifest

    work = tmp_path / "work"
    work.mkdir()
    (work / "steps.jsonl").write_text('{"index":0,"kind":"session.start","content":{"workflow_name":"parity-tamper-test"}}\n', encoding="utf-8")
    manifest = ManifestModel(workflow_id="00000000-0000-4000-a000-000000000001")
    km = KeyManager()
    # Ensure key exists (generate if missing)
    if not km.has_key("default"):
        km.generate_keypair("default")
    priv = km.load_private_key("default")
    out = tmp_path / "good.epi"
    EPIContainer.pack(work, manifest, out, signer_function=lambda m: sign_manifest(m, priv, "default"))
    # Good must pass in both
    py_good = _python_verify(out)
    assert (py_good.get("facts") or py_good).get("signature_valid") is True
    emb_good = _embedded_verify(out)
    assert emb_good["signature_valid"] is True

    # Tamper: flip a byte inside ZIP payload (break file hash, keep envelope valid for this test)
    import io, zipfile
    raw = out.read_bytes()
    marker = b"<!-- EPI_ZIP_PAYLOAD_START -->"
    idx = raw.find(marker)
    payload = raw[idx + len(marker):] if idx != -1 else raw
    z = zipfile.ZipFile(io.BytesIO(payload))
    # Tamper steps.jsonl content
    tampered_bytes = z.read("steps.jsonl").replace(b"session.start", b"session.tamper")
    # Rebuild zip with tampered member (keep envelope header + marker)
    new_payload_io = io.BytesIO()
    with zipfile.ZipFile(new_payload_io, "w", zipfile.ZIP_DEFLATED) as nz:
        for info in z.infolist():
            data = z.read(info.filename)
            if info.filename == "steps.jsonl":
                data = tampered_bytes
            nz.writestr(info, data)
    new_payload = new_payload_io.getvalue()
    tampered = tmp_path / "tampered.epi"
    if idx != -1:
        tampered.write_bytes(raw[: idx + len(marker)] + new_payload)
    else:
        tampered.write_bytes(new_payload)

    py_bad = _python_verify(tampered)
    # Python must report tampered (integrity false or sig false or FAIL decision)
    facts_bad = py_bad.get("facts") or py_bad
    assert facts_bad.get("signature_valid") is not True or facts_bad.get("integrity_ok") is False or py_bad.get("decision", {}).get("status") == "FAIL"
    emb_bad = _embedded_verify(tampered)
    # Embedded must also not report valid
    assert emb_bad["signature_valid"] is not True or emb_bad["integrity_ok"] is False
