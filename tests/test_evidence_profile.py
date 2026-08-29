"""Decision-grade evidence profile scorer."""

from pathlib import Path

import pytest

from epi_core.evidence_profile import load_evidence_profile, score_artifact
from tests.helpers.repo_paths import require_repo_file


def test_profile_loads():
    p = load_evidence_profile(require_repo_file("docs", "evidence-profile", "v0.1.json"))
    assert p["profile_id"] == "epi-decision-grade"
    assert "weights" in p["scoring"]


@pytest.mark.skipif(
    not (Path(__file__).resolve().parents[1] / "agicomply_demo.epi").exists(),
    reason="demo fixture missing",
)
def test_score_agicomply_demo():
    root = Path(__file__).resolve().parents[1]
    report = score_artifact(root / "agicomply_demo.epi")
    assert "score" in report
    assert report["checks"]["has_steps"] is True
    assert report["checks"]["has_signature"] is True
