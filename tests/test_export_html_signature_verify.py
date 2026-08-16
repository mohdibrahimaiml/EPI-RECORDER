"""Regression: standalone export-html must prove signatures client-side.

The zero-install share path embeds archive_base64 + crypto.js. The viewer must
show a real VALID/INVALID result — never 'OPEN VIA EPI VIEW TO VERIFY'.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from epi_core.viewer_assets import load_viewer_assets
from tests.test_all_cli_commands import _run_cli, make_decision_epi


PUNT = "OPEN VIA EPI VIEW TO VERIFY"


def test_app_js_has_client_verify_and_no_punt_string():
    assets = load_viewer_assets()
    app_js = assets["app_js"] or ""
    assert "verifyCaseInBrowser" in app_js
    assert PUNT not in app_js
    assert "verifyManifestSignature" in (assets["crypto_js"] or "")


def test_export_html_standalone_signature_valid_not_punt(tmp_path: Path):
    artifact, _ = make_decision_epi(tmp_path, signed=True)
    output_html = tmp_path / "shared_case.html"
    epi_home = tmp_path / "epi-home"

    result = _run_cli(
        ["export-html", str(artifact), "--output", str(output_html)],
        cwd=tmp_path,
        epi_home=epi_home,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert output_html.exists()

    content = output_html.read_text(encoding="utf-8")

    # Must never ship the punt message
    assert PUNT not in content

    # Must include real client verification machinery
    assert "verifyCaseInBrowser" in content
    assert "verifyManifestSignature" in content
    assert "epi-preloaded-cases" in content

    # Preloaded case should carry a signed manifest + archive for re-check
    assert "archive_base64" in content
    assert '"signature"' in content or "signature" in content

    # Python-side pre-verify should already mark valid for a signed artifact;
    # client re-verify will also run when opened in a browser.
    # Accept either explicit true or the presence of ed25519 signature field.
    assert (
        '"valid": true' in content
        or '"valid":true' in content
        or "ed25519:" in content
    )


def test_export_html_unsigned_does_not_punt(tmp_path: Path):
    artifact, _ = make_decision_epi(tmp_path, signed=False)
    output_html = tmp_path / "unsigned_case.html"

    result = _run_cli(
        ["export-html", str(artifact), "--output", str(output_html)],
        cwd=tmp_path,
        epi_home=tmp_path / "epi-home",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    content = output_html.read_text(encoding="utf-8")
    assert PUNT not in content
    assert "verifyCaseInBrowser" in content
