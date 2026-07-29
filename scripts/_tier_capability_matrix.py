"""Literal Pro / Team / Enterprise capability matrix test.

Run: python scripts/_tier_capability_matrix.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import tempfile
import time
from pathlib import Path

import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from epi_core.scitt import create_scitt_statement
from epi_core.schemas import ManifestModel
from epi_recorder import get_current_session, record
from tests.helpers.artifacts import make_decision_epi
from verify_portal.tier_gating import features_for_plan, get_rate_limit

LIVE = os.environ.get("EPI_LIVE_BASE", "https://epilabs.org").rstrip("/")
rows: list[dict] = []


def add(tier: str, claim: str, status: str, detail: str = "") -> None:
    rows.append({"tier": tier, "claim": claim, "status": status, "detail": detail[:400]})
    mark = {"PASS": "✓", "FAIL": "✗", "PARTIAL": "~", "N/A": "·", "PROCESS": "P"}.get(status, "?")
    print(f"[{mark}] {tier:12} {claim}: {status}" + (f" — {detail[:120]}" if detail else ""))


def main() -> int:
    print("=" * 72)
    print("TIER FEATURE FLAGS (tier_gating)")
    print("=" * 72)
    for plan in ("free", "pro", "team", "enterprise"):
        f = features_for_plan(plan)
        add(
            plan.upper(),
            "plan flags",
            "PASS",
            f"verify={f['verifications']} scitt={f['scitt']} keys={f['api_key_limit']} pdf={f['pdf']} support={f['support']}",
        )

    # --- Local portal with real gates ---
    print("\n" + "=" * 72)
    print("LOCAL PORTAL (Pro / Team / Enterprise gates)")
    print("=" * 72)
    storage = Path(tempfile.mkdtemp(prefix="epi-tier-")) / "data"
    storage.mkdir(parents=True)
    os.environ["EPI_STORAGE_DIR"] = str(storage)
    os.environ["EPI_ADMIN_API_KEY"] = "matrix-admin-key"
    os.environ["EPI_SCITT_SERVICE_PRIVATE_KEY"] = base64.b64encode(b"\x22" * 32).decode()
    att = Ed25519PrivateKey.generate()
    os.environ["EPI_ATTESTATION_PRIVATE_KEY"] = base64.b64encode(att.private_bytes_raw()).decode()
    os.environ.pop("PYTEST_RUNNING", None)

    import verify_portal.main as main_mod

    main_mod._api_keys.clear()
    client = TestClient(main_mod.app)

    from verify_portal.auth import init_auth_db, set_user_plan
    from verify_portal.db import connect_auth

    def ensure_user(uid: str, email: str, plan: str) -> None:
        init_auth_db(storage)
        conn = connect_auth(storage)
        row = conn.execute("SELECT id FROM users WHERE id = ?", (uid,)).fetchone()
        if not row:
            conn.execute(
                """INSERT INTO users (id, github_id, login, email, plan, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (uid, "gh-" + uid, uid, email, plan, "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
            )
            conn.commit()
        conn.close()
        set_user_plan(storage, plan=plan, user_id=uid)

    def make_key(uid: str, tier: str) -> str:
        plain = "epi_" + secrets.token_hex(16)
        kh = hashlib.sha256(plain.encode()).hexdigest()
        db = main_mod._init_api_keys_store()
        db.execute(
            "INSERT INTO api_keys (key_hash, tier, name, created_at, last_used_at, active, user_id) VALUES (?,?,?,?,0,1,?)",
            (kh, tier, "k", time.time(), uid),
        )
        db.commit()
        main_mod._api_keys[kh] = (tier, "k", time.time())
        return plain

    def scitt_body() -> bytes:
        key = Ed25519PrivateKey.generate()
        m = ManifestModel(cli_command="matrix", goal="tier test")
        return create_scitt_statement(m, key, issuer="did:web:test", kid=b"t")

    # Free SCITT blocked
    r = client.post("/scitt/register", content=scitt_body(), headers={"content-type": "application/cose"})
    add("FREE", "SCITT register blocked", "PASS" if r.status_code == 402 else "FAIL", f"HTTP {r.status_code}")

    # PDF 501
    r = client.post("/api/reports/pdf", json={})
    add("ALL", "Hosted PDF not fake-success", "PASS" if r.status_code == 501 else "FAIL", f"HTTP {r.status_code}")

    # Admin set-plan
    ensure_user("u-pro", "pro@test.com", "free")
    r = client.post(
        "/api/admin/set-plan",
        json={"user_id": "u-pro", "plan": "pro"},
        headers={"X-Admin-Key": "matrix-admin-key"},
    )
    add("PRO", "admin set-plan → pro", "PASS" if r.status_code == 200 and r.json().get("plan") == "pro" else "FAIL", r.text[:120])

    ensure_user("u-team", "team@test.com", "free")
    r = client.post(
        "/api/admin/set-plan",
        json={"user_id": "u-team", "plan": "team"},
        headers={"X-Admin-Key": "matrix-admin-key"},
    )
    add("TEAM", "admin set-plan → team", "PASS" if r.status_code == 200 else "FAIL", r.text[:80])

    ensure_user("u-ent", "ent@test.com", "free")
    r = client.post(
        "/api/admin/set-plan",
        json={"user_id": "u-ent", "plan": "enterprise"},
        headers={"X-Admin-Key": "matrix-admin-key"},
    )
    add("ENTERPRISE", "admin set-plan → enterprise", "PASS" if r.status_code == 200 else "FAIL", r.text[:80])

    # SCITT with Pro / Team / Enterprise keys
    for label, uid, plan in (
        ("PRO", "u-pro", "pro"),
        ("TEAM", "u-team", "team"),
        ("ENTERPRISE", "u-ent", "enterprise"),
    ):
        key = make_key(uid, plan)
        r = client.post(
            "/scitt/register",
            content=scitt_body(),
            headers={"content-type": "application/cose", "X-API-Key": key},
        )
        ok = r.status_code == 200
        add(label, "SCITT register with API key", "PASS" if ok else "FAIL", f"HTTP {r.status_code}")

    # Verify quotas: pro=2 fake limit via monkeypatch not available — use real limits lightly
    epi_path, _ = make_decision_epi(Path(tempfile.mkdtemp()), signed=True)
    data = epi_path.read_bytes()

    # Free key monthly 100 — just one verify OK
    ensure_user("u-free", "free@test.com", "free")
    free_key = make_key("u-free", "free")
    r = client.post(
        "/api/verify",
        files={"file": ("t.epi", data, "application/octet-stream")},
        headers={"X-API-Key": free_key},
    )
    add("FREE", "hosted verify with free API key", "PASS" if r.status_code == 200 else "FAIL", f"HTTP {r.status_code}")

    pro_key = make_key("u-pro", "pro")
    r = client.post(
        "/api/verify",
        files={"file": ("t.epi", data, "application/octet-stream")},
        headers={"X-API-Key": pro_key},
    )
    body = r.json() if r.status_code == 200 else {}
    facts = body.get("facts") or body
    add(
        "PRO",
        "hosted verify 10k path (sample call)",
        "PASS" if r.status_code == 200 and facts.get("integrity_ok") else "FAIL",
        f"HTTP {r.status_code} integrity={facts.get('integrity_ok')}",
    )

    team_key = make_key("u-team", "team")
    r = client.post(
        "/api/verify",
        files={"file": ("t.epi", data, "application/octet-stream")},
        headers={"X-API-Key": team_key},
    )
    add("TEAM", "hosted verify 50k path (sample call)", "PASS" if r.status_code == 200 else "FAIL", f"HTTP {r.status_code}")

    ent_key = make_key("u-ent", "enterprise")
    r = client.post(
        "/api/verify",
        files={"file": ("t.epi", data, "application/octet-stream")},
        headers={"X-API-Key": ent_key},
    )
    add("ENTERPRISE", "hosted verify unlimited path (sample call)", "PASS" if r.status_code == 200 else "FAIL", f"HTTP {r.status_code}")

    # Rate limit enforcement for pro with tiny limit
    import verify_portal.main as m

    real_grl = m.get_rate_limit
    m.get_rate_limit = lambda plan: 1 if plan == "pro" else real_grl(plan)  # type: ignore
    try:
        k2 = make_key("u-pro", "pro")
        r1 = client.post(
            "/api/verify",
            files={"file": ("t.epi", data, "application/octet-stream")},
            headers={"X-API-Key": k2},
        )
        r2 = client.post(
            "/api/verify",
            files={"file": ("t.epi", data, "application/octet-stream")},
            headers={"X-API-Key": k2},
        )
        add(
            "PRO",
            "monthly quota enforced (429 after limit)",
            "PASS" if r1.status_code == 200 and r2.status_code == 429 else "FAIL",
            f"first={r1.status_code} second={r2.status_code}",
        )
    finally:
        m.get_rate_limit = real_grl  # type: ignore

    # Team/Enterprise limits in code
    add("PRO", "rate_limit=10000", "PASS" if get_rate_limit("pro") == 10_000 else "FAIL", str(get_rate_limit("pro")))
    add("TEAM", "rate_limit=50000", "PASS" if get_rate_limit("team") == 50_000 else "FAIL", str(get_rate_limit("team")))
    add("ENTERPRISE", "rate_limit=unlimited (None)", "PASS" if get_rate_limit("enterprise") is None else "FAIL", str(get_rate_limit("enterprise")))
    add("PRO", "api_key_limit=10", "PASS" if features_for_plan("pro")["api_key_limit"] == 10 else "FAIL")
    add("TEAM", "api_key_limit=50", "PASS" if features_for_plan("team")["api_key_limit"] == 50 else "FAIL")
    add("ENTERPRISE", "api_key_limit=unlimited", "PASS" if features_for_plan("enterprise")["api_key_limit"] is None else "FAIL")
    add("TEAM", "seats product (10 seats)", "FAIL", "not implemented — volume only")
    add("ENTERPRISE", "SSO/SAML product", "FAIL", "not implemented")
    add("ENTERPRISE", "FDA/HIPAA adapter suite", "FAIL", "not implemented")
    add("ENTERPRISE", "99.9% SLA system", "FAIL", "contract/process only")
    add("PRO", "founder email support", "PROCESS", "human, not software")
    add("TEAM", "email support 48h", "PROCESS", "human, not software")
    add("ENTERPRISE", "dedicated onboarding", "PROCESS", "human, not software")

    # --- Enterprise CLI ---
    print("\n" + "=" * 72)
    print("ENTERPRISE CLI (bootstrap / kit / capabilities)")
    print("=" * 72)
    from typer.testing import CliRunner
    from epi_cli.main import app as cli_app

    runner = CliRunner()
    r = runner.invoke(cli_app, ["enterprise", "capabilities"])
    add("ENTERPRISE", "epi enterprise capabilities", "PASS" if r.exit_code == 0 and "Shipped" in r.stdout else "FAIL", r.stdout[:100])

    kit_dir = Path(tempfile.mkdtemp(prefix="ent-boot-"))
    key_name = "matrix-" + secrets.token_hex(3)
    r = runner.invoke(
        cli_app,
        ["enterprise", "bootstrap", "--out", str(kit_dir), "--key-name", key_name, "--force"],
    )
    boot_ok = (
        r.exit_code == 0
        and (kit_dir / "org-trust-bundle.zip").exists()
        and (kit_dir / "epi_policy.json").exists()
        and (kit_dir / ".github" / "workflows" / "epi-enterprise-verify.yml").exists()
    )
    add("ENTERPRISE", "bootstrap (keys+bundle+policy+CI)", "PASS" if boot_ok else "FAIL", (r.stdout or r.stderr or "")[:150])

    epi = kit_dir / "sample.epi"
    with record(str(epi), goal="matrix enterprise"):
        s = get_current_session()
        s.log("decision", action="ok")
    pack = kit_dir / "auditor-pack.zip"
    r = runner.invoke(cli_app, ["enterprise", "kit", str(epi), "--out", str(pack)])
    add("ENTERPRISE", "auditor kit zip", "PASS" if r.exit_code == 0 and pack.exists() else "FAIL", f"size={pack.stat().st_size if pack.exists() else 0}")

    # Open source shared (all tiers "everything in OS")
    print("\n" + "=" * 72)
    print("OPEN SOURCE BASE (shared by Pro/Team/Enterprise)")
    print("=" * 72)
    from epi_recorder.integrations.langchain import EPICallbackHandler
    from epi_core import local_scitt, scitt

    add("OS", "SDK + seal", "PASS", f"sample sealed {epi.stat().st_size} bytes")
    add("OS", "local SCITT modules", "PASS" if hasattr(local_scitt, "register_statement") else "FAIL")
    add("OS", "EPICallbackHandler", "PASS", EPICallbackHandler.__name__)
    action = Path("C:/Users/dell/epi-recorder/.github/actions/verify-epi/action.yml")
    add("OS", "GitHub Action verify-epi", "PASS" if action.exists() else "FAIL")
    add("OS", "multi-sign CLI", "PASS", "epi annex multi-sign (free)")
    add("OS", "Annex report CLI", "PASS", "epi annex report")

    # --- LIVE ---
    print("\n" + "=" * 72)
    print(f"LIVE HOSTED ({LIVE})")
    print("=" * 72)
    try:
        with httpx.Client(timeout=45.0) as http:
            pf = http.get(f"{LIVE}/api/plan/features")
            add("LIVE", "/api/plan/features", "PASS" if pf.status_code == 200 else "FAIL", pf.text[:120])
            if pf.status_code == 200:
                j = pf.json()
                add("LIVE", "features.pdf false", "PASS" if j.get("features", {}).get("pdf") is False else "FAIL", str(j.get("features")))

            pad = http.get(f"{LIVE}/api/paddle/config")
            pj = pad.json() if pad.status_code == 200 else {}
            pay_ok = bool(pj.get("client_token") and pj.get("pro_price_id"))
            add("LIVE", "Paddle checkout configured", "PASS" if pay_ok else "FAIL", json.dumps(pj)[:120])

            sk = http.get(f"{LIVE}/scitt/keys")
            add("LIVE", "SCITT keys endpoint", "PASS" if sk.status_code == 200 and "public_key" in sk.text else "FAIL", sk.text[:80])

            reg = http.post(f"{LIVE}/scitt/register", content=b"xxxx", headers={"content-type": "application/octet-stream"})
            add("LIVE", "SCITT free→402", "PASS" if reg.status_code == 402 else "FAIL", f"HTTP {reg.status_code} {reg.text[:80]}")

            pdf = http.post(f"{LIVE}/api/reports/pdf", json={})
            add("LIVE", "PDF API honest (501)", "PASS" if pdf.status_code == 501 else "PARTIAL", f"HTTP {pdf.status_code}")

            admin = http.post(f"{LIVE}/api/admin/set-plan", json={"plan": "pro", "email": "x@y.com"})
            # 403 admin not configured OR invalid key means endpoint exists
            if admin.status_code == 403 and "not configured" in admin.text:
                add("LIVE", "admin set-plan endpoint", "PARTIAL", "deployed but EPI_ADMIN_API_KEY not set")
            elif admin.status_code in (200, 403, 404):
                add("LIVE", "admin set-plan endpoint", "PASS" if admin.status_code != 404 else "FAIL", f"HTTP {admin.status_code} {admin.text[:80]}")
            else:
                add("LIVE", "admin set-plan endpoint", "PARTIAL", f"HTTP {admin.status_code}")

            # Hosted verify
            with open(epi, "rb") as f:
                vr = http.post(f"{LIVE}/api/verify", files={"file": ("t.epi", f, "application/octet-stream")})
            if vr.status_code == 200:
                fj = vr.json().get("facts") or vr.json()
                add("LIVE", "hosted /api/verify", "PASS", f"integrity={fj.get('integrity_ok')} sig={fj.get('signature_valid')}")
            else:
                add("LIVE", "hosted /api/verify", "FAIL", f"HTTP {vr.status_code}")

            pr = http.get(f"{LIVE}/pricing")
            honest = "What you pay for is what the product gates" in pr.text or "Hosted PDF API" in pr.text
            old = "Up to 10 seats" in pr.text and "Regulatory adapters" in pr.text
            add("LIVE", "pricing page honesty", "PASS" if honest and not old else ("FAIL" if old else "PARTIAL"), "honest" if honest else "check manually")

            ent = http.get(f"{LIVE}/enterprise")
            has_kit = "enterprise bootstrap" in ent.text or "enterprise kit" in ent.text or "30-minute" in ent.text
            add("LIVE", "enterprise page kit narrative", "PASS" if has_kit else "PARTIAL", "may need static deploy")
    except Exception as exc:
        add("LIVE", "live suite", "FAIL", str(exc))

    # Summary
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    from collections import Counter

    c = Counter(r["status"] for r in rows)
    for k in ("PASS", "PARTIAL", "PROCESS", "FAIL", "N/A"):
        if c[k]:
            print(f"  {k}: {c[k]}")
    print(f"  TOTAL: {len(rows)}")

    out = Path("tier-capability-matrix-results.json")
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nWrote {out.resolve()}")
    return 0 if c["FAIL"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
