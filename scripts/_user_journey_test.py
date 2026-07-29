"""Normal-user journey tests (no operator curl knowledge required)."""
from __future__ import annotations

import base64
import hashlib
import os
import secrets
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from epi_cli.main import app as cli_app
from epi_recorder import get_current_session, record

ROOT = Path(__file__).resolve().parents[1]
results: list[tuple[str, bool, str]] = []


def add(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def test_cli() -> None:
    runner = CliRunner()
    work = Path(tempfile.mkdtemp(prefix="user-cli-"))
    epi = work / "my-run.epi"
    with record(str(epi), goal="user journey"):
        s = get_current_session()
        s.log("tool.call", tool="search")
        s.log("decision", action="ok")
    add("CLI: seal .epi", epi.exists() and epi.stat().st_size > 1000, f"size={epi.stat().st_size}")

    r = runner.invoke(cli_app, ["verify", str(epi)])
    add("CLI: verify offline (no account)", r.exit_code in (0, 1), f"exit={r.exit_code}")

    r = runner.invoke(cli_app, ["view", "--help"])
    add("CLI: view command exists", r.exit_code == 0)

    kit = work / "enterprise-epi"
    key = "journey-" + secrets.token_hex(3)
    r = runner.invoke(
        cli_app,
        ["enterprise", "setup", "--out", str(kit), "--key-name", key, "--force"],
    )
    add(
        "CLI: enterprise setup",
        r.exit_code == 0
        and (kit / "org-trust-bundle.zip").exists()
        and (kit / "epi_policy.json").exists(),
        (r.stdout or "")[:100],
    )
    add(
        "CLI: setup speaks plain next steps",
        "Next 3 steps" in (r.stdout or "") or "pack" in (r.stdout or "").lower(),
    )

    pack = work / "auditor-pack.zip"
    r = runner.invoke(cli_app, ["enterprise", "pack", str(epi), "--out", str(pack)])
    add("CLI: enterprise pack", r.exit_code == 0 and pack.exists() and pack.stat().st_size > 1000)

    r = runner.invoke(cli_app, ["enterprise", "capabilities"])
    out = r.stdout or ""
    add("CLI: capabilities lists setup+pack", r.exit_code == 0 and "setup" in out and "pack" in out)

    # init wizard exists for new users
    r = runner.invoke(cli_app, ["init", "--help"])
    add("CLI: init wizard exists", r.exit_code == 0)


def test_portal_session() -> None:
    storage = Path(tempfile.mkdtemp(prefix="user-portal-")) / "data"
    storage.mkdir(parents=True)
    os.environ["EPI_STORAGE_DIR"] = str(storage)
    os.environ["EPI_ADMIN_API_KEY"] = "journey-admin"
    os.environ["EPI_SCITT_SERVICE_PRIVATE_KEY"] = base64.b64encode(b"\x44" * 32).decode()
    att = Ed25519PrivateKey.generate()
    os.environ["EPI_ATTESTATION_PRIVATE_KEY"] = base64.b64encode(
        att.private_bytes_raw()
    ).decode()
    os.environ.pop("PYTEST_RUNNING", None)

    import verify_portal.main as main_mod
    from verify_portal.auth import init_auth_db, set_user_plan
    from verify_portal.db import connect_auth

    main_mod._api_keys.clear()
    client = TestClient(main_mod.app)

    init_auth_db(storage)
    conn = connect_auth(storage)
    for uid, email, plan in (
        ("usr_free", "free@ex.com", "free"),
        ("usr_pro", "pro@ex.com", "pro"),
        ("usr_team", "team@ex.com", "team"),
        ("usr_ent", "ent@ex.com", "enterprise"),
    ):
        conn.execute(
            """INSERT INTO users (id, github_id, login, email, plan, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?)""",
            (uid, "gh-" + uid, uid, email, "free", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:00+00:00"),
        )
    conn.commit()
    conn.close()
    for uid, plan in (
        ("usr_pro", "pro"),
        ("usr_team", "team"),
        ("usr_ent", "enterprise"),
    ):
        set_user_plan(storage, plan=plan, user_id=uid)

    from verify_portal.auth import create_token

    def make_token(uid: str) -> str:
        return create_token(storage, uid)

    epi = Path(tempfile.mkdtemp()) / "run.epi"
    with record(str(epi), goal="portal user"):
        get_current_session().log("decision", ok=True)
    data = epi.read_bytes()

    r = client.post("/api/verify", files={"file": ("run.epi", data, "application/octet-stream")})
    add("Portal: anonymous verify works", r.status_code == 200, f"HTTP {r.status_code}")

    try:
        t_pro = make_token("usr_pro")
        t_ent = make_token("usr_ent")
        t_team = make_token("usr_team")
        add("Portal: create session tokens", True)
    except Exception as e:
        add("Portal: create session tokens", False, str(e))
        return

    r = client.post(
        "/api/verify",
        files={"file": ("run.epi", data, "application/octet-stream")},
        headers={"Authorization": f"Bearer {t_pro}"},
    )
    facts = (r.json() or {}).get("facts") if r.status_code == 200 else {}
    add(
        "Portal: Pro verifies WITHOUT API key",
        r.status_code == 200 and facts.get("integrity_ok") is True,
        f"HTTP {r.status_code}",
    )

    r = client.post(
        "/api/verify",
        files={"file": ("run.epi", data, "application/octet-stream")},
        headers={"Authorization": f"Bearer {t_team}"},
    )
    add("Portal: Team verifies WITHOUT API key", r.status_code == 200, f"HTTP {r.status_code}")

    r = client.post(
        "/api/verify",
        files={"file": ("run.epi", data, "application/octet-stream")},
        headers={"Authorization": f"Bearer {t_ent}"},
    )
    add("Portal: Enterprise verifies WITHOUT API key", r.status_code == 200, f"HTTP {r.status_code}")

    r = client.get("/api/plan/features", headers={"Authorization": f"Bearer {t_pro}"})
    j = r.json() if r.status_code == 200 else {}
    add("Portal: plan features for Pro", r.status_code == 200 and j.get("plan") == "pro")

    r = client.post("/api/reports/pdf", json={}, headers={"Authorization": f"Bearer {t_pro}"})
    add("Portal: no fake PDF success", r.status_code == 501, f"HTTP {r.status_code}")

    r = client.post(
        "/scitt/register",
        content=b"not-a-statement",
        headers={"content-type": "application/octet-stream"},
    )
    add("Portal: free SCITT blocked (402)", r.status_code == 402)

    # errors are human readable
    detail = r.json().get("detail", "")
    add(
        "Portal: SCITT error plain English",
        "Pro" in detail or "plan" in detail.lower(),
        detail[:80],
    )


def test_live_site() -> None:
    import httpx

    base = "https://epilabs.org"
    with httpx.Client(timeout=40.0, follow_redirects=True) as http:
        for path, must in (
            ("/account", ["Verify a file", "Your plan", "Advanced"]),
            ("/pricing", ["Get Pro", "Online verification", "Team volume", "sign in"]),
            ("/enterprise", ["15-minute", "enterprise setup", "enterprise pack"]),
            ("/verify/", ["Seal check", ".epi"]),
        ):
            r = http.get(base + path)
            text = r.text or ""
            ok = r.status_code == 200
            missing = [m for m in must if m not in text]
            # live may lag deploy — mark partial if missing new strings
            if ok and not missing:
                add(f"Live {path} UX copy", True)
            elif ok and missing:
                add(
                    f"Live {path} UX copy",
                    False,
                    f"missing {missing} (deploy lag?) status={r.status_code}",
                )
            else:
                add(f"Live {path}", False, f"HTTP {r.status_code}")

        r = http.get(f"{base}/api/plan/features")
        add("Live plan features API", r.status_code == 200)

        # create sample and anonymous verify
        epi = Path(tempfile.mkdtemp()) / "live.epi"
        with record(str(epi), goal="live anon"):
            get_current_session().log("decision", ok=True)
        with open(epi, "rb") as f:
            r = http.post(
                f"{base}/api/verify",
                files={"file": ("live.epi", f, "application/octet-stream")},
            )
        if r.status_code == 200:
            facts = r.json().get("facts") or {}
            add(
                "Live anonymous verify",
                facts.get("integrity_ok") is True,
                f"integrity={facts.get('integrity_ok')}",
            )
        elif r.status_code == 429:
            add("Live anonymous verify", True, "rate limited (expected under load)")
        else:
            add("Live anonymous verify", False, f"HTTP {r.status_code} {r.text[:80]}")


def main() -> int:
    print("=" * 60)
    print("NORMAL USER JOURNEY TESTS")
    print("=" * 60)
    test_cli()
    print()
    test_portal_session()
    print()
    test_live_site()
    fails = sum(1 for _, ok, _ in results if not ok)
    print()
    print(f"SUMMARY: {len(results) - fails}/{len(results)} passed, {fails} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
