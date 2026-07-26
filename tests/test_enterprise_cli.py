"""Smoke tests for epi enterprise bootstrap / kit / capabilities."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from epi_cli.main import app
from epi_recorder import get_current_session, record

runner = CliRunner()


def test_enterprise_capabilities() -> None:
    r = runner.invoke(app, ["enterprise", "capabilities"])
    assert r.exit_code == 0
    assert "Shipped today" in r.stdout
    assert "bootstrap" in r.stdout


def test_enterprise_bootstrap_and_kit(tmp_path: Path) -> None:
    out = tmp_path / "kit"
    key = "ent-cli-test"
    r = runner.invoke(
        app,
        [
            "enterprise",
            "bootstrap",
            "--out",
            str(out),
            "--key-name",
            key,
            "--force",
        ],
    )
    assert r.exit_code == 0, r.stdout + r.stderr
    assert (out / "README.md").exists()
    assert (out / "epi_policy.json").exists()
    assert (out / "org-trust-bundle.zip").exists()
    assert (out / ".github" / "workflows" / "epi-enterprise-verify.yml").exists()

    epi = tmp_path / "run.epi"
    with record(str(epi), goal="enterprise test"):
        s = get_current_session()
        s.log("decision", ok=True)

    pack = tmp_path / "auditor-pack.zip"
    r2 = runner.invoke(
        app,
        ["enterprise", "kit", str(epi), "--out", str(pack)],
    )
    assert r2.exit_code == 0, r2.stdout + r2.stderr
    assert pack.exists() and pack.stat().st_size > 1000
