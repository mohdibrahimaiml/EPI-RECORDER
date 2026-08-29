"""Frozen pre-4.4.1 artifacts must keep verifying. Do not regenerate the goldens."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

from epi_core.container import EPI_ZIP_MARKER
from epi_core.schemas import ManifestModel
from epi_core.serialize import MANIFEST_OMIT_NONE_FROM_HASH

GOLDENS = Path(__file__).resolve().parent / "goldens"
GOLDEN_43 = GOLDENS / "legacy-spec-4.3.0.epi"
GOLDEN_440 = GOLDENS / "legacy-spec-4.4.0.epi"


def _raw_manifest(path: Path) -> dict:
    raw = path.read_bytes()
    idx = raw.find(EPI_ZIP_MARKER)
    payload = raw[idx + len(EPI_ZIP_MARKER) :] if idx >= 0 else raw
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        return json.loads(zf.read("manifest.json"))


def test_frozen_goldens_must_not_be_regenerated() -> None:
    assert GOLDEN_43.is_file() and GOLDEN_43.stat().st_size > 100
    assert GOLDEN_440.is_file() and GOLDEN_440.stat().st_size > 100
    m43 = _raw_manifest(GOLDEN_43)
    m440 = _raw_manifest(GOLDEN_440)
    assert m43["spec_version"] == "4.3.0"
    assert m440["spec_version"] == "4.4.0"
    assert "content_truncated" not in m43
    assert "content_truncated" not in m440


def test_frozen_goldens_signature_valid() -> None:
    from typer.testing import CliRunner

    from epi_cli.main import app

    runner = CliRunner()
    for path, spec in ((GOLDEN_43, "4.3.0"), (GOLDEN_440, "4.4.0")):
        result = runner.invoke(app, ["verify", str(path), "--json"])
        text = result.output or ""
        start, end = text.find("{"), text.rfind("}")
        report = json.loads(text[start : end + 1])
        facts = report.get("facts") or report
        meta = report.get("metadata") or {}
        assert meta.get("spec_version") == spec
        assert facts.get("signature_valid") is True, (path.name, report.get("decision"))


def test_optional_manifest_nones_absent_from_golden_must_be_omitted() -> None:
    """Next Optional field that is missing from the frozen JSON must join the omit set."""
    sealed = _raw_manifest(GOLDEN_43)
    loaded = ManifestModel.model_validate(sealed)
    dumped = loaded.model_dump()
    extra_nones = sorted(
        k for k, v in dumped.items() if v is None and k not in sealed
    )
    unlisted = [k for k in extra_nones if k not in MANIFEST_OMIT_NONE_FROM_HASH]
    assert unlisted == [], (
        "New ManifestModel optional fields appear as JSON null in the signature "
        "preimage but are absent from tests/goldens/legacy-spec-4.3.0.epi. "
        f"Add them to MANIFEST_OMIT_NONE_FROM_HASH: {unlisted}"
    )


def test_manifest_optional_none_defaults_are_catalogued() -> None:
    """Every Optional default-None field: omitted when absent, or already in old seals."""
    from pydantic_core import PydanticUndefined

    sealed = set(_raw_manifest(GOLDEN_43).keys())
    optional_none: list[str] = []
    for name, field in ManifestModel.model_fields.items():
        if field.default is None and field.default_factory is None:
            optional_none.append(name)
        elif field.default is PydanticUndefined and field.default_factory is None:
            continue
    rows = []
    for name in optional_none:
        if name == "signature":
            rows.append((name, "excluded at verify (popped)", "ok"))
            continue
        in_omit = name in MANIFEST_OMIT_NONE_FROM_HASH
        in_golden = name in sealed
        if in_omit:
            status = "omitted when None (JCS + legacy)"
        elif in_golden:
            status = "present on frozen 4.3.0 seal (nulls are part of signed bytes — do not omit)"
        else:
            status = "UNSAFE: absent on golden, not in omit set"
        rows.append((name, status, "ok" if in_omit or in_golden else "FAIL"))
    failed = [r for r in rows if r[2] == "FAIL"]
    assert not failed, failed
    assert all(r[2] == "ok" for r in rows)
