"""Pro capability gates: API key quotas, SCITT plan gate, admin set-plan."""

from __future__ import annotations

import base64
import hashlib
import os
import time
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from epi_core.scitt import create_scitt_statement
from epi_core.schemas import ManifestModel
from tests.helpers.artifacts import make_decision_epi


@pytest.fixture
def portal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    storage = tmp_path / "data"
    storage.mkdir()
    monkeypatch.setenv("EPI_STORAGE_DIR", str(storage))
    monkeypatch.setenv("EPI_ADMIN_API_KEY", "test-admin-secret")
    key_bytes = b"\x11" * 32
    monkeypatch.setenv(
        "EPI_SCITT_SERVICE_PRIVATE_KEY",
        base64.b64encode(key_bytes).decode(),
    )
    att = Ed25519PrivateKey.generate()
    monkeypatch.setenv(
        "EPI_ATTESTATION_PRIVATE_KEY",
        base64.b64encode(att.private_bytes_raw()).decode(),
    )
    # Do NOT set PYTEST_RUNNING — we want real SCITT tier gates
    monkeypatch.delenv("PYTEST_RUNNING", raising=False)
    monkeypatch.setattr("verify_portal.main._check_rate_limit", lambda _ip: True)

    # Fresh import state for API keys memory cache
    import verify_portal.main as main_mod

    main_mod._api_keys.clear()

    return TestClient(main_mod.app)


def _insert_user(storage: Path, *, user_id: str, email: str, plan: str) -> None:
    from verify_portal.auth import init_auth_db, set_user_plan
    from verify_portal.db import connect_auth

    init_auth_db(storage)
    conn = connect_auth(storage)
    conn.execute(
        """
        INSERT INTO users (id, github_id, login, email, plan, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, "gh-" + user_id, "user", email, plan, "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
    )
    conn.commit()
    conn.close()
    set_user_plan(storage, plan=plan, user_id=user_id)


def _make_key(storage: Path, *, user_id: str, tier: str, name: str = "k") -> str:
    import secrets

    import verify_portal.main as main_mod

    plain = "epi_" + secrets.token_hex(16)
    kh = hashlib.sha256(plain.encode()).hexdigest()
    db = main_mod._init_api_keys_store()
    db.execute(
        "INSERT INTO api_keys (key_hash, tier, name, created_at, last_used_at, active, user_id) VALUES (?,?,?,?,0,1,?)",
        (kh, tier, name, time.time(), user_id),
    )
    db.commit()
    main_mod._api_keys[kh] = (tier, name, time.time())
    return plain


def _valid_statement() -> bytes:
    issuer_key = Ed25519PrivateKey.generate()
    manifest = ManifestModel(cli_command="pytest", goal="pro capability scitt")
    return create_scitt_statement(
        manifest,
        issuer_key,
        issuer="did:web:epilabs.org",
        kid=b"test",
    )


def test_scitt_register_free_blocked(portal: TestClient, tmp_path: Path) -> None:
    r = portal.post(
        "/scitt/register",
        content=_valid_statement(),
        headers={"Content-Type": "application/cose"},
    )
    assert r.status_code == 402
    assert "Pro" in r.json()["detail"]


def test_scitt_register_pro_api_key_allowed(portal: TestClient, tmp_path: Path) -> None:
    storage = Path(os.environ["EPI_STORAGE_DIR"])
    _insert_user(storage, user_id="u1", email="pro@example.com", plan="pro")
    key = _make_key(storage, user_id="u1", tier="pro")

    r = portal.post(
        "/scitt/register",
        content=_valid_statement(),
        headers={"Content-Type": "application/cose", "X-API-Key": key},
    )
    assert r.status_code == 200, r.text
    assert len(r.content) > 0


def test_verify_quota_enforced_for_pro_key(
    portal: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    storage = Path(os.environ["EPI_STORAGE_DIR"])
    _insert_user(storage, user_id="u2", email="q@example.com", plan="pro")
    key = _make_key(storage, user_id="u2", tier="pro")

    # Tiny limit for test
    monkeypatch.setattr(
        "verify_portal.main.get_rate_limit",
        lambda plan: 2 if plan == "pro" else 100,
    )

    epi_path, _ = make_decision_epi(tmp_path, signed=True)
    data = epi_path.read_bytes()

    for i in range(2):
        r = portal.post(
            "/api/verify",
            files={"file": ("t.epi", data, "application/octet-stream")},
            headers={"X-API-Key": key},
        )
        assert r.status_code == 200, f"iter {i}: {r.text}"

    r = portal.post(
        "/api/verify",
        files={"file": ("t.epi", data, "application/octet-stream")},
        headers={"X-API-Key": key},
    )
    assert r.status_code == 429


def test_admin_set_plan(portal: TestClient, tmp_path: Path) -> None:
    storage = Path(os.environ["EPI_STORAGE_DIR"])
    _insert_user(storage, user_id="u3", email="set@example.com", plan="free")
    r = portal.post(
        "/api/admin/set-plan",
        json={"email": "set@example.com", "plan": "pro"},
        headers={"X-Admin-Key": "test-admin-secret"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["plan"] == "pro"
    from verify_portal.auth import get_user_plan

    assert get_user_plan(storage, "u3") == "pro"


def test_admin_set_plan_requires_key(portal: TestClient) -> None:
    r = portal.post("/api/admin/set-plan", json={"email": "x@y.com", "plan": "pro"})
    assert r.status_code == 403


def test_pdf_still_501(portal: TestClient) -> None:
    r = portal.post("/api/reports/pdf", json={})
    assert r.status_code == 501
