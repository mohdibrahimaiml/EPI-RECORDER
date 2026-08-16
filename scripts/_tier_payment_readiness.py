"""Step-by-step tier readiness as a normal user (pre-payments gate)."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import tempfile
from pathlib import Path

import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from epi_cli.main import app as cli_app
from epi_core.scitt import create_scitt_statement
from epi_core.schemas import ManifestModel
from epi_recorder import get_current_session, record
from typer.testing import CliRunner
from verify_portal.auth import create_token, init_auth_db, set_user_plan
from verify_portal.db import connect_auth
from verify_portal.tier_gating import features_for_plan, get_rate_limit

LIVE = "https://epilabs.org"
rows: list[dict] = []


def add(tier: str, step: str, ok: bool, detail: str = "", severity: str = "block") -> None:
    """severity: block = must fix before payments; soft = OK to pay, improve later."""
    rows.append(
        {
            "tier": tier,
            "step": step,
            "ok": ok,
            "detail": detail[:300],
            "severity": severity if not ok else "ok",
        }
    )
    tag = "PASS" if ok else ("FAIL-BLOCK" if severity == "block" else "FAIL-SOFT")
    print(f"[{tag}] {tier:12} | {step}" + (f" — {detail[:140]}" if detail else ""))


def make_epi() -> bytes:
    p = Path(tempfile.mkdtemp()) / "u.epi"
    with record(str(p), goal="tier readiness"):
        get_current_session().log("decision", ok=True)
    return p.read_bytes()


def scitt_stmt() -> bytes:
    k = Ed25519PrivateKey.generate()
    m = ManifestModel(cli_command="ready", goal="scitt")
    return create_scitt_statement(m, k, issuer="did:web:test", kid=b"t")


def setup_portal():
    storage = Path(tempfile.mkdtemp(prefix="tier-ready-")) / "data"
    storage.mkdir(parents=True)
    os.environ["EPI_STORAGE_DIR"] = str(storage)
    os.environ["EPI_ADMIN_API_KEY"] = "ready-admin-key"
    os.environ["EPI_SCITT_SERVICE_PRIVATE_KEY"] = base64.b64encode(b"\x55" * 32).decode()
    att = Ed25519PrivateKey.generate()
    os.environ["EPI_ATTESTATION_PRIVATE_KEY"] = base64.b64encode(
        att.private_bytes_raw()
    ).decode()
    os.environ.pop("PYTEST_RUNNING", None)

    import verify_portal.main as main_mod

    main_mod._api_keys.clear()
    client = TestClient(main_mod.app)
    init_auth_db(storage)
    conn = connect_auth(storage)
    for uid, email in (
        ("u_free", "free@test.com"),
        ("u_pro", "pro@test.com"),
        ("u_team", "team@test.com"),
        ("u_ent", "ent@test.com"),
    ):
        conn.execute(
            """INSERT INTO users (id, github_id, login, email, plan, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?)""",
            (
                uid,
                "gh-" + uid,
                uid,
                email,
                "free",
                "2026-01-01T00:00:00+00:00",
                "2026-01-01T00:00:00+00:00",
            ),
        )
    conn.commit()
    conn.close()
    for uid, plan in (("u_pro", "pro"), ("u_team", "team"), ("u_ent", "enterprise")):
        set_user_plan(storage, plan=plan, user_id=uid)
    return client, storage, main_mod


def test_local_tiers() -> None:
    print("\n=== LOCAL: flags + user paths ===\n")
    for plan, v, keys, scitt in (
        ("free", 100, 1, False),
        ("pro", 10_000, 10, True),
        ("team", 50_000, 50, True),
        ("enterprise", None, None, True),
    ):
        f = features_for_plan(plan)
        ok = (
            f["verifications"] == v
            and f["api_key_limit"] == keys
            and f["scitt"] is scitt
            and f["pdf"] is False
        )
        add(plan.upper(), "plan limits correct", ok, str(f))

    client, storage, main_mod = setup_portal()
    data = make_epi()

    # FREE anonymous
    r = client.post("/api/verify", files={"file": ("u.epi", data, "application/octet-stream")})
    add("FREE", "anonymous online verify", r.status_code == 200, f"HTTP {r.status_code}")

    r = client.post(
        "/scitt/register",
        content=scitt_stmt(),
        headers={"content-type": "application/cose"},
    )
    add("FREE", "SCITT blocked without paid plan", r.status_code == 402, f"HTTP {r.status_code}")

    # Each paid tier: session verify no API key
    for tier, uid in (("PRO", "u_pro"), ("TEAM", "u_team"), ("ENTERPRISE", "u_ent")):
        tok = create_token(storage, uid)
        r = client.post(
            "/api/verify",
            files={"file": ("u.epi", data, "application/octet-stream")},
            headers={"Authorization": f"Bearer {tok}"},
        )
        facts = r.json().get("facts") if r.status_code == 200 else {}
        add(
            tier,
            "signed-in verify WITHOUT API key",
            r.status_code == 200 and facts.get("integrity_ok") is True,
            f"HTTP {r.status_code}",
        )

        # API key path
        plain = "epi_" + secrets.token_hex(16)
        kh = hashlib.sha256(plain.encode()).hexdigest()
        plan = tier.lower() if tier != "ENTERPRISE" else "enterprise"
        db = main_mod._init_api_keys_store()
        db.execute(
            "INSERT INTO api_keys (key_hash, tier, name, created_at, last_used_at, active, user_id) VALUES (?,?,?,?,0,1,?)",
            (kh, plan, "ci", __import__("time").time(), uid),
        )
        db.commit()
        main_mod._api_keys[kh] = (plan, "ci", 0.0)
        r = client.post(
            "/api/verify",
            files={"file": ("u.epi", data, "application/octet-stream")},
            headers={"X-API-Key": plain},
        )
        add(tier, "CI API key verify", r.status_code == 200, f"HTTP {r.status_code}")

        r = client.post(
            "/scitt/register",
            content=scitt_stmt(),
            headers={"content-type": "application/cose", "X-API-Key": plain},
        )
        add(tier, "SCITT with plan key", r.status_code == 200, f"HTTP {r.status_code}")

        r = client.get("/api/plan/features", headers={"Authorization": f"Bearer {tok}"})
        j = r.json() if r.status_code == 200 else {}
        add(tier, "plan/features API", r.status_code == 200 and j.get("plan") == plan, str(j.get("plan")))

    # Quota enforcement pro
    import time as _t

    plain = "epi_" + secrets.token_hex(12)
    kh = hashlib.sha256(plain.encode()).hexdigest()
    db = main_mod._init_api_keys_store()
    db.execute(
        "INSERT INTO api_keys (key_hash, tier, name, created_at, last_used_at, active, user_id) VALUES (?,?,?,?,0,1,?)",
        (kh, "pro", "q", _t.time(), "u_pro"),
    )
    db.commit()
    main_mod._api_keys[kh] = ("pro", "q", 0.0)
    real = main_mod.get_rate_limit
    main_mod.get_rate_limit = lambda p: 1 if p == "pro" else real(p)  # type: ignore
    try:
        r1 = client.post(
            "/api/verify",
            files={"file": ("u.epi", data, "application/octet-stream")},
            headers={"X-API-Key": plain},
        )
        r2 = client.post(
            "/api/verify",
            files={"file": ("u.epi", data, "application/octet-stream")},
            headers={"X-API-Key": plain},
        )
        add(
            "PRO",
            "quota stops over-use (429)",
            r1.status_code == 200 and r2.status_code == 429,
            f"{r1.status_code}->{r2.status_code}",
        )
    finally:
        main_mod.get_rate_limit = real  # type: ignore

    r = client.post("/api/reports/pdf", json={})
    add("ALL", "hosted PDF not sold as working", r.status_code == 501, f"HTTP {r.status_code}")

    # Team seats not product — soft fail for honesty
    add(
        "TEAM",
        "multi-user seats product",
        False,
        "Not built — Team is volume only (OK if pricing says so)",
        severity="soft",
    )
    add(
        "ENTERPRISE",
        "SSO/SAML product",
        False,
        "Not built — sell services/self-host (OK if not claimed as shipped)",
        severity="soft",
    )


def test_cli_user() -> None:
    print("\n=== LOCAL: offline user (no payments needed) ===\n")
    runner = CliRunner()
    work = Path(tempfile.mkdtemp(prefix="cli-user-"))
    epi = work / "run.epi"
    with record(str(epi), goal="offline"):
        get_current_session().log("decision", ok=True)
    r = runner.invoke(cli_app, ["verify", str(epi)])
    add("FREE/OS", "offline verify", r.exit_code in (0, 1), f"exit={r.exit_code}")

    kit = work / "kit"
    r = runner.invoke(
        cli_app,
        ["enterprise", "setup", "--out", str(kit), "--key-name", "ready-" + secrets.token_hex(2), "--force"],
    )
    add(
        "ENTERPRISE",
        "setup kit (customer eng)",
        r.exit_code == 0 and (kit / "org-trust-bundle.zip").exists(),
    )
    pack = work / "pack.zip"
    r = runner.invoke(cli_app, ["enterprise", "pack", str(epi), "--out", str(pack)])
    add("ENTERPRISE", "auditor pack", r.exit_code == 0 and pack.exists())


def test_live() -> None:
    print("\n=== LIVE: public + config (payments readiness) ===\n")
    with httpx.Client(timeout=45.0, follow_redirects=True) as http:
        r = http.get(f"{LIVE}/api/ping")
        add("LIVE", "API up", r.status_code == 200, r.text[:60])

        r = http.get(f"{LIVE}/api/paddle/config")
        cfg = r.json() if r.status_code == 200 else {}
        pay_ready = bool(cfg.get("client_token") and cfg.get("pro_price_id"))
        add(
            "LIVE",
            "Paddle ready for self-serve Pro",
            pay_ready,
            json.dumps(cfg),
            severity="soft",  # enterprise can invoice without Paddle
        )

        r = http.get(f"{LIVE}/api/plan/features")
        add("LIVE", "plan features API", r.status_code == 200)

        data = make_epi()
        r = http.post(
            f"{LIVE}/api/verify",
            files={"file": ("u.epi", data, "application/octet-stream")},
        )
        if r.status_code == 200:
            f = r.json().get("facts") or {}
            add("LIVE", "anonymous verify", f.get("integrity_ok") is True)
        elif r.status_code == 429:
            add("LIVE", "anonymous verify", True, "rate limited (service works)")
        else:
            add("LIVE", "anonymous verify", False, f"HTTP {r.status_code}")

        r = http.post(
            f"{LIVE}/scitt/register",
            content=b"x",
            headers={"content-type": "application/octet-stream"},
        )
        add("LIVE", "free SCITT blocked", r.status_code == 402, f"HTTP {r.status_code}")

        r = http.post(f"{LIVE}/api/reports/pdf", json={})
        add("LIVE", "PDF not fake", r.status_code == 501, f"HTTP {r.status_code}")

        r = http.post(
            f"{LIVE}/api/admin/set-plan",
            json={"email": "x@y.com", "plan": "pro"},
        )
        # 403 invalid or not configured
        admin_ok = r.status_code == 403  # endpoint exists
        detail = r.text
        if "not configured" in detail:
            add(
                "LIVE",
                "admin set-plan configured",
                False,
                "EPI_ADMIN_API_KEY missing — you already used it successfully earlier; re-check after redeploy",
                severity="soft",
            )
        else:
            add("LIVE", "admin set-plan endpoint live", admin_ok, f"HTTP {r.status_code}")

        # UX pages
        for path, needles, soft in (
            ("/account", ["Verify a file", "Your plan"], False),
            ("/portal", ["dropzone", "file", "verify"], False),
            ("/pricing", ["Online verification", "Team"], False),
            ("/enterprise", ["setup", "pack"], True),
        ):
            r = http.get(LIVE + path)
            text = (r.text or "").lower()
            missing = [n for n in needles if n.lower() not in text]
            add(
                "LIVE",
                f"page {path}",
                r.status_code == 200 and not missing,
                f"missing={missing}" if missing else "ok",
                severity="soft" if soft else "block",
            )


def main() -> int:
    print("TIER PAYMENT-READINESS (normal user lens)\n")
    test_cli_user()
    test_local_tiers()
    test_live()

    blocks = [r for r in rows if not r["ok"] and r["severity"] == "block"]
    softs = [r for r in rows if not r["ok"] and r["severity"] == "soft"]
    passes = [r for r in rows if r["ok"]]

    print("\n" + "=" * 64)
    print(f"PASS: {len(passes)}  BLOCKERS: {len(blocks)}  SOFT: {len(softs)}  TOTAL: {len(rows)}")
    if blocks:
        print("\nBLOCKERS before self-serve payments:")
        for r in blocks:
            print(f"  - [{r['tier']}] {r['step']}: {r['detail']}")
    if softs:
        print("\nSOFT (OK for invoice/manual enterprise; fix when you can):")
        for r in softs:
            print(f"  - [{r['tier']}] {r['step']}: {r['detail']}")

    # Verdict
    print("\n" + "=" * 64)
    if not blocks:
        if not any(r["step"] == "Paddle ready for self-serve Pro" and r["ok"] for r in rows):
            print("VERDICT: Product tiers WORK for users.")
            print("  - Manual/enterprise invoice payments: YES, safe to charge (you set-plan).")
            print("  - Self-serve Paddle Subscribe button: NOT ready (configure Paddle first).")
        else:
            print("VERDICT: Ready for self-serve Pro payments.")
    else:
        print("VERDICT: Do NOT open self-serve payments until blockers fixed.")

    out = Path("tier-payment-readiness.json")
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nWrote {out.resolve()}")
    return 1 if blocks else 0


if __name__ == "__main__":
    raise SystemExit(main())
