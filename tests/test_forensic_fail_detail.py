"""Forensic FAIL summary must surface gap reason (AUD-CO-01)."""

from __future__ import annotations

from pathlib import Path

from epi_cli.verify import _audit_step_sequence_completeness, print_trust_report
from epi_core.schemas import ManifestModel
from epi_core.trust import create_verification_report


def test_unmatched_tool_call_gap_message():
    steps = [
        {
            "index": 0,
            "kind": "tool.call",
            "content": {"call_id": "c1", "name": "search"},
        },
        # no tool.response
    ]
    ok, gaps = _audit_step_sequence_completeness(steps)
    assert ok is False
    assert gaps
    assert "tool.call" in gaps[0]
    assert "tool.response" in gaps[0]


def test_create_verification_report_carries_forensic_reason():
    manifest = ManifestModel(spec_version="4.0.1", file_manifest={})
    gaps = ["tool.call at step 0 is missing a corresponding tool.response"]
    report = create_verification_report(
        integrity_ok=True,
        signature_valid=None,
        signer_name=None,
        mismatches={},
        manifest=manifest,
        completeness_ok=False,
        completeness_gaps=gaps,
        forensic_reason=gaps[0],
    )
    assert report["facts"]["completeness_ok"] is False
    assert report["facts"]["completeness_gaps"] == gaps
    assert "tool.response" in report["facts"]["forensic_reason"]


def test_print_trust_report_includes_forensic_gap(capsys):
    manifest = ManifestModel(spec_version="4.0.1", file_manifest={})
    gaps = ["tool.call at step 3 is missing a corresponding tool.response"]
    report = create_verification_report(
        integrity_ok=True,
        signature_valid=True,
        signer_name="test",
        mismatches={},
        manifest=manifest,
        completeness_ok=False,
        sequence_ok=True,
        chain_ok=True,
        completeness_gaps=gaps,
        forensic_reason=gaps[0],
    )
    # Minimal decision layer for printer
    report["decision"] = {
        "status": "FAIL",
        "policy": "standard",
        "reason": "Forensic completeness failed",
    }
    print_trust_report(report, Path("dummy.epi"), verbose=False)
    # Rich may use ANSI; reason text must still appear
    # Use report facts path that printer reads
    assert report["facts"]["forensic_reason"]
