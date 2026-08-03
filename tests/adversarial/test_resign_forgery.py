"""Adversarial: full-chain rebuild + foreign-key re-sign must not look claim-safe.

Core claim for insurers: a valid seal proves internal consistency under some
key, not who sealed. STRICT requires org-pinned KNOWN identity → FAIL.
STANDARD may WARN (dev) but must never chrome as SEAL OK.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from epi_cli.main import app
from epi_core.container import EPIContainer
from epi_core.keys import KeyManager
from epi_core.schemas import ManifestModel
from epi_core.trust import sign_manifest
from tests.helpers.artifacts import make_decision_epi, make_decision_workspace

runner = CliRunner()


def _flip_approval_in_workspace(workspace: Path) -> None:
    """Flip approve → decline in steps.jsonl (material decision change)."""
    steps_path = workspace / "steps.jsonl"
    lines = steps_path.read_text(encoding="utf-8").splitlines()
    flipped = []
    changed = False
    for line in lines:
        if not line.strip():
            continue
        step = json.loads(line)
        content = step.get("content") or {}
        if "approved" in content and content["approved"] is True:
            content["approved"] = False
            content["reason"] = "Attacker flipped approve → decline"
            step["content"] = content
            changed = True
        if step.get("kind") == "agent.decision":
            content = dict(content)
            content["decision"] = "decline — forged"
            step["content"] = content
            changed = True
        flipped.append(json.dumps(step, sort_keys=True))
    assert changed, "expected an approved step to flip"
    steps_path.write_text("\n".join(flipped) + "\n", encoding="utf-8")


def _full_rebuild_foreign_resign(
    tmp_path: Path, *, attacker_keys: Path
) -> tuple[Path, Path]:
    """Simulate sophisticated forgery: rebuild consistent chain + attacker key.

    1. Start from a legitimate-looking decision workspace (approve).
    2. Flip the material decision.
    3. Re-pack with a fresh Ed25519 key (library rebuilds file_manifest + seal).
    """
    victim_ws = make_decision_workspace(tmp_path / "victim_ws")
    # Prove victim path can seal with a different key (optional baseline)
    victim_epi = tmp_path / "victim.epi"
    victim_key_dir = tmp_path / "victim_keys"
    victim_key_dir.mkdir()
    vkm = KeyManager(keys_dir=victim_key_dir)
    vkm.generate_keypair("victim", overwrite=True)
    vpriv = vkm.load_private_key("victim")
    EPIContainer.pack(
        victim_ws,
        ManifestModel(cli_command="victim", goal="approve refund"),
        victim_epi,
        signer_function=lambda m: sign_manifest(m, vpriv, "victim"),
        preserve_generated=True,
        generate_analysis=False,
    )

    # Attacker: extract narrative via fresh workspace + flip (full rebuild)
    attack_ws = make_decision_workspace(tmp_path / "attack_ws")
    _flip_approval_in_workspace(attack_ws)

    attacker_keys.mkdir(parents=True, exist_ok=True)
    akm = KeyManager(keys_dir=attacker_keys)
    akm.generate_keypair("attacker", overwrite=True)
    apriv = akm.load_private_key("attacker")

    forged = tmp_path / "forged.epi"
    EPIContainer.pack(
        attack_ws,
        ManifestModel(cli_command="forged", goal="decline refund (forged)"),
        forged,
        signer_function=lambda m: sign_manifest(m, apriv, "attacker"),
        preserve_generated=True,
        generate_analysis=False,
    )
    return forged, victim_epi


def test_full_resign_forgery_fails_under_strict(tmp_path: Path, monkeypatch):
    """Tamper + full-chain-rebuild + foreign-key re-sign → FAIL under strict."""
    attacker_keys = tmp_path / "attacker_keys"
    empty_trust = tmp_path / "empty_trust"
    empty_trust.mkdir()
    monkeypatch.setenv("EPI_TRUSTED_KEYS_DIR", str(empty_trust))
    # Attacker key present → LOCAL; still must FAIL strict (not KNOWN)
    monkeypatch.setenv("EPI_KEYS_DIR", str(attacker_keys))

    forged, _victim = _full_rebuild_foreign_resign(tmp_path, attacker_keys=attacker_keys)

    # Seal must be internally consistent (integrity + signature)
    ok, mismatches = EPIContainer.verify_integrity(forged)
    assert ok is True, f"forged seal should pass integrity: {mismatches}"
    manifest = EPIContainer.read_manifest(forged)
    from epi_core.trust import verify_embedded_manifest_signature

    sig_ok, _, msg = verify_embedded_manifest_signature(manifest)
    assert sig_ok is True, msg

    result = runner.invoke(
        app, ["verify", str(forged), "--policy", "strict", "--json"]
    )
    assert result.exit_code != 0, result.output
    report = json.loads(result.stdout)
    assert report["facts"]["integrity_ok"] is True
    assert report["facts"]["signature_valid"] is True
    assert report["identity"]["status"] in ("UNKNOWN", "LOCAL")
    assert report["decision"]["status"] == "FAIL"
    assert report["decision"]["policy"] == "strict"


def test_full_resign_forgery_standard_warn_not_seal_ok(tmp_path: Path, monkeypatch):
    """Under STANDARD, forgery is WARN with UNVERIFIED IDENTITY — never SEAL OK chrome."""
    attacker_keys = tmp_path / "attacker_keys"
    empty_trust = tmp_path / "empty_trust"
    empty_trust.mkdir()
    # No local keys → UNKNOWN (pure unpinned)
    no_local = tmp_path / "no_local"
    no_local.mkdir()
    monkeypatch.setenv("EPI_TRUSTED_KEYS_DIR", str(empty_trust))
    monkeypatch.setenv("EPI_KEYS_DIR", str(no_local))

    # Build forge with attacker keys, then verify without those keys on disk
    forged, _ = _full_rebuild_foreign_resign(tmp_path, attacker_keys=attacker_keys)

    result_json = runner.invoke(app, ["verify", str(forged), "--json"])
    assert result_json.exit_code == 0, result_json.output
    report = json.loads(result_json.stdout)
    assert report["facts"]["integrity_ok"] is True
    assert report["facts"]["signature_valid"] is True
    assert report["identity"]["status"] == "UNKNOWN"
    assert report["decision"]["status"] == "WARN"
    reason = report["decision"]["reason"]
    assert not reason.strip().upper().startswith("SEAL OK")
    assert "unverified identity" in reason.lower() or "not pinned" in reason.lower()

    result_human = runner.invoke(app, ["verify", str(forged)])
    out = result_human.output
    assert result_human.exit_code == 0, out
    assert "UNVERIFIED IDENTITY" in out
    assert "SEAL OK" not in out
    assert "✘ SEAL FAIL" not in out
    # Identity block before seal proofs (ordering)
    id_pos = out.find("IDENTITY")
    seal_pos = out.find("SEAL (Objective")
    assert id_pos != -1 and seal_pos != -1
    assert id_pos < seal_pos


def test_full_resign_local_attacker_still_warn_and_strict_fail(
    tmp_path: Path, monkeypatch
):
    """Attacker machine with key in EPI_KEYS_DIR: LOCAL WARN, not PASS; strict FAIL."""
    attacker_keys = tmp_path / "attacker_keys"
    empty_trust = tmp_path / "empty_trust"
    empty_trust.mkdir()
    monkeypatch.setenv("EPI_TRUSTED_KEYS_DIR", str(empty_trust))
    monkeypatch.setenv("EPI_KEYS_DIR", str(attacker_keys))

    forged, _ = _full_rebuild_foreign_resign(tmp_path, attacker_keys=attacker_keys)

    result = runner.invoke(app, ["verify", str(forged), "--json"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.stdout)
    assert report["identity"]["status"] == "LOCAL"
    assert report["decision"]["status"] == "WARN"
    assert not report["decision"]["reason"].strip().upper().startswith("SEAL OK")

    human = runner.invoke(app, ["verify", str(forged)])
    assert "LOCAL SEALER" in human.output or "UNVERIFIED IDENTITY" in human.output
    assert "SEAL OK" not in human.output

    strict = runner.invoke(app, ["verify", str(forged), "--policy", "strict", "--json"])
    assert strict.exit_code != 0
    assert json.loads(strict.stdout)["decision"]["status"] == "FAIL"
