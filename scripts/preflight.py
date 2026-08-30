#!/usr/bin/env python3
"""
epi_preflight.py — independent pre-submission verification for epi-recorder.

RUN THIS IN A FRESH VENV WITH THE PUBLISHED WHEEL. NOT the editable install.

    python -m venv preflight && preflight/Scripts/activate   (Windows)
    python -m venv preflight && source preflight/bin/activate (Unix)
    pip install epi-recorder==4.4.3 agentrust-trace agentrust-trace-tests rfc8785 requests
    python epi_preflight.py --epi <path-to-a-real-artifact.epi>

Every check prints PASS / FAIL / SKIP with the evidence it used.
Exit code 1 if any FAIL.
"""
from __future__ import annotations
import argparse, base64, hashlib, importlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

FAILS: list[str] = []
REPO = "mohdibrahimaiml/epi-recorder"


def _repo_root() -> Path:
    here = Path(__file__).resolve().parent
    return here.parent if here.name == "scripts" else here


def _spec_tuple(spec: str) -> tuple[int, int, int]:
    parts: list[int] = []
    for p in str(spec).lstrip("v").split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    while len(parts) < 3:
        parts.append(0)
    return (parts[0], parts[1], parts[2])


def check_legacy_signature_preimage() -> None:
    """Fail if a frozen pre-4.4.1 artifact does not verify signature_valid.

    Catches schema fields that silently change the Ed25519 preimage.
    """
    head("4a. LEGACY SIGNATURE PREIMAGE (pre-4.4.1 golden must stay valid)")
    golden = _repo_root() / "tests" / "goldens" / "legacy-spec-4.3.0.epi"
    if not golden.is_file():
        result(False, "pre-4.4.1 golden present", f"missing {golden}")
        return
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env["PYTHONPATH"] = ""
    cwd = "C:\\" if os.name == "nt" else "/"
    try:
        r = subprocess.run(
            [sys.executable, "-m", "epi_cli", "verify", str(golden), "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            cwd=cwd,
            timeout=180,
        )
    except Exception as e:
        result(False, "verify pre-4.4.1 golden", str(e))
        return
    text = (r.stdout or "") + (r.stderr or "")
    i, j = text.find("{"), text.rfind("}")
    if i < 0:
        result(False, "verify pre-4.4.1 golden --json", text[-400:] or f"rc={r.returncode}")
        return
    rep = json.loads(text[i : j + 1])
    facts = rep.get("facts") or rep
    meta = rep.get("metadata") or {}
    spec = str(meta.get("spec_version") or "")
    sig = facts.get("signature_valid")
    result(
        _spec_tuple(spec) < (4, 4, 1),
        "golden spec_version is before 4.4.1",
        f"spec_version={spec}",
    )
    result(
        sig is True,
        "pre-4.4.1 signature_valid is True",
        f"signature_valid={sig} decision={rep.get('decision')}",
    )


def check_live_sample_epi() -> None:
    """Production must serve a downloadable sample that the CLI accepts."""
    head("4b. LIVE SAMPLE.EPI (https://epilabs.org/assets/sample.epi)")
    try:
        import requests
    except ImportError:
        return skip("live sample.epi", "pip install requests")
    url = "https://epilabs.org/assets/sample.epi"
    try:
        r = requests.get(url, timeout=30)
    except Exception as e:
        result(False, "GET live sample.epi", str(e))
        return
    result(r.status_code == 200, "GET /assets/sample.epi is HTTP 200", f"HTTP {r.status_code}")
    if r.status_code != 200:
        return
    tmp = Path(tempfile.gettempdir()) / "epilabs-org-sample.epi"
    tmp.write_bytes(r.content)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env["PYTHONPATH"] = ""
    cwd = "C:\\" if os.name == "nt" else "/"
    try:
        vr = subprocess.run(
            [sys.executable, "-m", "epi_cli", "verify", str(tmp), "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            cwd=cwd,
            timeout=180,
        )
    except Exception as e:
        result(False, "verify downloaded sample.epi", str(e))
        return
    text = (vr.stdout or "") + (vr.stderr or "")
    i, j = text.find("{"), text.rfind("}")
    if i < 0:
        result(False, "verify downloaded sample.epi --json", text[-400:] or f"rc={vr.returncode}")
        return
    rep = json.loads(text[i : j + 1])
    facts = rep.get("facts") or rep
    sig = facts.get("signature_valid")
    integ = facts.get("integrity_ok")
    result(
        integ is True and sig is True,
        "served sample.epi verifies (integrity + signature)",
        f"integrity_ok={integ} signature_valid={sig} decision={rep.get('decision')}",
    )


def check_live_verifier_js() -> None:
    """Live https://epilabs.org/js/epi-verify-core.js must match website/js/ (CRLF-normalized)."""
    head("4c-live. LIVE VERIFIER JS (epilabs.org matches website/js/)")
    try:
        import requests
    except ImportError:
        return skip("live verifier JS", "pip install requests")
    url = "https://epilabs.org/js/epi-verify-core.js"
    canon = _repo_root() / "website" / "js" / "epi-verify-core.js"
    if not canon.is_file():
        return result(False, "canonical website/js/epi-verify-core.js present", f"missing {canon}")
    try:
        r = requests.get(url, timeout=30)
    except Exception as e:
        return result(False, "GET live verifier JS", str(e))
    if r.status_code != 200:
        return result(False, "GET live verifier JS is HTTP 200", f"HTTP {r.status_code}")
    live_norm = r.content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    canon_norm = canon.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    lh = hashlib.sha256(live_norm).hexdigest()
    ch = hashlib.sha256(canon_norm).hexdigest()
    result(lh == ch, "live verifier matches website/js/epi-verify-core.js (CRLF-normalized)",
           f"live={lh[:12]} canon={ch[:12]} live_len={len(r.content)} canon_len={len(canon.read_bytes())}")


def check_browser_verifier_js() -> None:
    """Known-good golden must verify under the website JS (Node)."""
    head("4c. BROWSER VERIFIER JS (Node, known-good golden)")
    node = shutil.which("node")
    script = _repo_root() / "scripts" / "browser_verify_signature.mjs"
    golden = _repo_root() / "tests" / "goldens" / "spec-4.4.3.epi"
    if not node:
        return skip("browser verifier JS", "node not on PATH")
    if not script.is_file() or not golden.is_file():
        result(False, "browser verifier script + 4.4.3 golden present", f"{script} / {golden}")
        return
    try:
        r = subprocess.run(
            [node, str(script), str(golden)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(_repo_root()),
            timeout=60,
        )
    except Exception as e:
        result(False, "node browser_verify_signature.mjs", str(e))
        return
    if r.returncode != 0:
        result(False, "node browser verifier exit 0", (r.stdout or "") + (r.stderr or ""))
        return
    try:
        js = json.loads((r.stdout or "").strip().splitlines()[-1])
    except Exception as e:
        result(False, "browser verifier JSON", f"{e}: {(r.stdout or '')[:300]}")
        return
    result(
        js.get("signature_valid") is True and js.get("integrity_ok") is True,
        "browser JS signature_valid and integrity_ok on 4.4.3 golden",
        json.dumps(js),
    )


def check_embedded_viewer() -> None:
    """Seal a fresh .epi and assert its embedded viewer.html contains current verifier logic.

    A test that only checks files on disk misses the seventh copy — the template
    baked into every artifact at seal time via epi_viewer_static/crypto.js.
    """
    head("4d. EMBEDDED VIEWER (pack-time viewer.html contains current verifier)")
    try:
        from epi_core.container import EPIContainer, EPI_ZIP_MARKER
        from epi_core.schemas import ManifestModel
    except Exception as e:
        return skip("embedded viewer", str(e))
    td = Path(tempfile.mkdtemp(prefix="preflight-embedded-"))
    epi_path = td / "embedded-check.epi"
    try:
        # Minimal workspace: steps.jsonl + manifest
        (td / "steps.jsonl").write_text('{"index":0,"kind":"session.start","content":{"workflow_name":"preflight-embedded"}}\n', encoding="utf-8")
        manifest = ManifestModel()
        # Use default packing (generates viewer.html via epi_viewer_static/crypto.js)
        EPIContainer.pack(td, manifest, epi_path)
        raw = epi_path.read_bytes()
        idx = raw.find(EPI_ZIP_MARKER)
        if idx == -1:
            return result(False, "embedded viewer marker found", "EPI_ZIP_MARKER not in artifact")
        # viewer is between header+comment and marker
        marker_off = raw.find(b"<!-- EPI_ZIP_PAYLOAD_START -->")
        # Extract viewer html bytes between header close and marker (best effort)
        viewer_bytes = raw[128:marker_off] if marker_off != -1 else b""
        # Also try extracting viewer.html from zip payload directly
        try:
            import zipfile, io
            payload = raw[idx + len(EPI_ZIP_MARKER):] if idx != -1 else raw
            # need to find actual zip start via EPIContainer logic; simpler: unpack and read file
            unpack = Path(tempfile.mkdtemp(prefix="preflight-unpack-"))
            EPIContainer.unpack(epi_path, unpack)
            viewer_text = (unpack / "viewer.html").read_text(encoding="utf-8", errors="ignore")
            shutil.rmtree(unpack, ignore_errors=True)
        except Exception:
            viewer_text = viewer_bytes.decode("utf-8", errors="ignore")
        has_pre = "isPreJcsSpec" in viewer_text
        has_prepare = "prepareManifestCopy" in viewer_text
        has_trunc = "content_truncated" in viewer_text
        ok = has_pre and has_prepare and has_trunc
        result(ok, "embedded viewer.html contains isPreJcsSpec + prepareManifestCopy + content_truncated",
               f"isPreJcsSpec={has_pre} prepareManifestCopy={has_prepare} content_truncated={has_trunc} viewer_len={len(viewer_text)}")
        # Also verify the freshly sealed artifact verifies (so embedded viewer not stale)
        try:
            env2 = dict(os.environ, PYTHONIOENCODING="utf-8")
            env2["PYTHONPATH"] = ""
            cwd2 = "C:\\" if os.name == "nt" else "/"
            r = subprocess.run([sys.executable, "-m", "epi_cli", "verify", str(epi_path), "--json"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", env=env2, cwd=cwd2, timeout=60)
            text = (r.stdout or "") + (r.stderr or "")
            i, j = text.find("{"), text.rfind("}")
            if i >= 0:
                rep = json.loads(text[i:j+1])
                facts = rep.get("facts") or rep
                sig = facts.get("signature_valid")
                integ = facts.get("integrity_ok")
                # Fresh seal in preflight may be unsigned (no key in fresh venv) — integrity must be true, sig must not be False (invalid)
                ok2 = integ is True and sig is not False
                result(ok2, "freshly sealed artifact verifies (integrity_ok, sig not invalid)", f"integrity_ok={integ} signature_valid={sig}")
        except Exception as e:
            skip("fresh seal verify", str(e))
    except Exception as e:
        result(False, "embedded viewer check", str(e))
    finally:
        shutil.rmtree(td, ignore_errors=True)


def result(ok, name, detail=""):
    tag = "PASS" if ok else "FAIL"
    if not ok:
        FAILS.append(name)
    print(f"  [{tag}] {name}" + (f"\n         {detail}" if detail else ""))
    return ok


def skip(name, why):
    print(f"  [SKIP] {name}\n         {why}")


def head(t):
    print(f"\n=== {t} ===")


# ---------------------------------------------------------------- 1. EXTERNAL
def check_external(shas):
    head("1. EXTERNAL STATE (unauthenticated, from the internet)")
    try:
        import requests
    except ImportError:
        return skip("external checks", "pip install requests")

    # 1a. purged blobs must be gone
    for sha in shas:
        url = (f"https://raw.githubusercontent.com/{REPO}/{sha}"
               f"/contact_submissions/20260809_110256_T.json")
        try:
            r = requests.get(url, timeout=20)
            result(r.status_code == 404, f"blob purged at {sha}",
                   f"HTTP {r.status_code} <- {url}")
        except Exception as e:
            result(False, f"blob purged at {sha}", f"request error: {e}")

    # 1b. forks hold their own copies; Support cannot purge them
    try:
        r = requests.get(f"https://api.github.com/repos/{REPO}", timeout=20)
        if r.status_code == 200:
            d = r.json()
            n = d.get("forks_count", "?")
            print(f"  [INFO] forks={n} stars={d.get('stargazers_count')} "
                  f"default_branch={d.get('default_branch')}")
            if isinstance(n, int) and n > 0:
                print("         -> check each fork manually; Support cannot purge them")
        else:
            skip("repo metadata", f"HTTP {r.status_code} (rate limit?)")
    except Exception as e:
        skip("repo metadata", str(e))

    # 1c. PyPI must serve the version you think you shipped
    try:
        r = requests.get("https://pypi.org/pypi/epi-recorder/json", timeout=20)
        if r.status_code == 200:
            d = r.json()
            v = d["info"]["version"]
            files = d["releases"].get(v, [])
            whl = [f["size"] for f in files if f["filename"].endswith(".whl")]
            sdist = [f["size"] for f in files if f["filename"].endswith(".tar.gz")]
            for label, sizes in (("wheel", whl), ("sdist", sdist)):
                if sizes:
                    mb = max(sizes) / 1_048_576
                    result(mb < 1.5, f"published {label} under 1.5 MB", f"{mb:.2f} MB")
        else:
            skip("PyPI", f"HTTP {r.status_code}")
    except Exception as e:
        skip("PyPI", str(e))


# ------------------------------------------------------------- 2. INSTALLATION
def check_install():
    head("2. INSTALLED PACKAGE (must be the wheel, not editable)")
    try:
        import epi_core
    except ImportError as e:
        return result(False, "epi_core importable", str(e))

    p = Path(epi_core.__file__).resolve()
    editable = "site-packages" not in str(p)
    result(not editable, "installed from wheel, not editable", f"loaded from {p}")

    try:
        from importlib.metadata import version, requires
        v = version("epi-recorder")
        print(f"  [INFO] epi-recorder version = {v}")
        reqs = requires("epi-recorder") or []
        result(any("rfc8785" in r for r in reqs),
               "rfc8785 declared as hard dependency",
               f"{[r for r in reqs if 'rfc8785' in r] or 'ABSENT'}")
    except Exception as e:
        skip("metadata", str(e))

    # verify_portal must NOT ship
    try:
        importlib.import_module("verify_portal")
        result(False, "verify_portal excluded from wheel", "it imported = still shipped")
    except ImportError:
        result(True, "verify_portal excluded from wheel", "ImportError as expected")


# ---------------------------------------------------- 3. CANONICALIZATION
def check_canonicalization():
    head("3. CANONICALIZATION (the fix that could silently break signatures)")
    try:
        import rfc8785
        from epi_core.serialize import _get_json_canonical_hash
    except Exception as e:
        return result(False, "canonical hash importable", str(e))

    # 3a. must equal rfc8785 exactly, on the cases that diverge
    cases = [{"v": 1.0}, {"a": "\u00e9cole", "b": 1.0}, {"k": "caf\u00e9\u00a0x"}]
    all_ok = True
    for c in cases:
        expect = hashlib.sha256(rfc8785.dumps(c)).hexdigest()
        got = _get_json_canonical_hash(c)
        ok = expect == got
        all_ok &= ok
        if not ok:
            print(f"         diverged on {c}: got {got[:16]} want {expect[:16]}")
    result(all_ok, "matches rfc8785 byte-for-byte on divergent cases",
           f"{len(cases)} vectors incl. float 1.0 and non-ASCII keys")

    # 3b. must NOT match naive json.dumps (proves the old path is really gone)
    naive = hashlib.sha256(
        json.dumps({"v": 1.0}, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    result(_get_json_canonical_hash({"v": 1.0}) != naive,
           "no longer equals naive json.dumps", "1.0 must canonicalize to 1")

    # 3c. hard fail, not silent fallback
    code = (
        "import sys; sys.modules['rfc8785']=None\n"
        "from epi_core.serialize import _get_json_canonical_hash as h\n"
        "try:\n"
        "    h({'v':1}); print('SILENT_FALLBACK')\n"
        "except Exception as e: print('RAISED', type(e).__name__)\n"
    )
    try:
        sub_env = dict(os.environ, PYTHONIOENCODING="utf-8")
        out = subprocess.run([sys.executable, "-c", code], capture_output=True,
                             text=True, encoding="utf-8", errors="replace", env=sub_env, timeout=60).stdout.strip()
        result("RAISED" in out, "hard-fails when rfc8785 missing", f"subprocess said: {out}")
    except Exception as e:
        skip("hard-fail check", str(e))


# ------------------------------------------------------------- 4. ARTIFACTS
def check_artifacts(paths):
    head("4. ARTIFACT VERIFICATION (old and new must both verify)")
    if not paths:
        return skip("artifact verify", "pass --epi <file> (repeatable)")
    for p in paths:
        p = Path(p).resolve()
        if not p.exists():
            result(False, f"verify {p.name}", "file not found")
            continue
        try:
            sub_env = dict(os.environ, PYTHONIOENCODING="utf-8")
            sub_env["PYTHONPATH"] = ""
            cwd = "C:\\" if os.name == "nt" else "/"
            r = subprocess.run(
                [sys.executable, "-m", "epi_cli", "verify", str(p), "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=sub_env,
                cwd=cwd,
                timeout=180,
            )
            out = (r.stdout or "") + (r.stderr or "")
            i, j = out.find("{"), out.rfind("}")
            if i < 0:
                result(False, f"verify {p.name}", out[-400:] or f"rc={r.returncode}")
                continue
            rep = json.loads(out[i : j + 1])
            facts = rep.get("facts") or rep
            dec = rep.get("decision") or {}
            status = dec.get("status") if isinstance(dec, dict) else dec
            sig = facts.get("signature_valid")
            ok = sig is True and str(status).upper() != "FAIL"
            result(
                ok,
                f"verify {p.name}",
                f"signature_valid={sig} decision={status} (WARN identity is allowed)",
            )
            # Negative control: corrupt inside ZIP member the verifier hashes
            try:
                import tempfile
                import shutil
                tmp = Path(tempfile.gettempdir()) / f"preflight-corrupt-{p.name}"
                shutil.copy(p, tmp)
                # Corrupt a byte inside a ZIP member (steps.jsonl) — not outer HTML padding
                # Handle envelope-v2 polyglot: find ZIP payload after marker, or plain ZIP
                data = bytearray(tmp.read_bytes())
                # Try to find ZIP member to corrupt via EPIContainer, else flip inside payload
                corrupted = False
                try:
                    from epi_core.container import EPIContainer, EPI_ZIP_MARKER
                    # If envelope, find marker and flip inside ZIP payload
                    marker = EPI_ZIP_MARKER
                    idx = data.find(marker)
                    if idx != -1:
                        # Flip 500 bytes into ZIP payload (past HTML, inside ZIP)
                        pos = idx + len(marker) + 500
                        if pos < len(data):
                            data[pos] ^= 0x01
                            corrupted = True
                    else:
                        # Plain ZIP or legacy: find steps.jsonl via zipfile and corrupt
                        import zipfile
                        import io
                        # Try to corrupt steps.jsonl member directly
                        with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
                            if "steps.jsonl" in zf.namelist():
                                # Read original, flip, and rewrite member
                                orig = zf.read("steps.jsonl")
                                if len(orig) > 10:
                                    corrupted_data = bytearray(orig)
                                    corrupted_data[5] ^= 0x01
                                    # Rebuild ZIP with corrupted member
                                    out_buf = io.BytesIO()
                                    with zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as out_zf:
                                        for info in zf.infolist():
                                            content = zf.read(info.filename)
                                            if info.filename == "steps.jsonl":
                                                content = bytes(corrupted_data)
                                            out_zf.writestr(info, content)
                                    # For envelope, need to rebuild envelope; for plain ZIP, just write
                                    if idx != -1:
                                        # Envelope: keep header + marker + new payload
                                        header = data[: idx + len(marker)]
                                        new_payload = out_buf.getvalue()
                                        # Update header payload length/hash is not needed for negative test — just corrupt outer
                                        data = bytearray(header + new_payload + data[idx + len(marker) + len(out_buf.getvalue()):])
                                    else:
                                        data = bytearray(out_buf.getvalue())
                                    corrupted = True
                except Exception:
                    pass
                if not corrupted:
                    # Fallback: flip byte in middle of file (may be HTML, but try)
                    mid = len(data) // 2
                    data[mid] ^= 0x01
                tmp.write_bytes(data)
                rn = subprocess.run([sys.executable, "-m", "epi_cli", "verify", str(tmp)],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace", env=sub_env, timeout=180)
                nout = ((rn.stdout or "") + (rn.stderr or ""))
                is_fail = rn.returncode != 0 or "FAIL" in nout.upper()
                # Match actual verdict line, not trailing warning
                keys = ("VERIFIED", "INTEGRITY", "SIGNATURE VALID", "FAIL", "DECISION")
                matching_fail = next((l.strip() for l in nout.splitlines() if any(k in l.upper() for k in keys)), "")
                detail = matching_fail or (nout.strip().splitlines()[-1][:500] if nout.strip() else f"rc={rn.returncode} (no output — verifier did not reject)")
                result(is_fail, f"negative control {p.name} (tampered must FAIL)", detail)
                if not is_fail:
                    print("         [INFO] Tampered file still PASSED — verifier coverage gap!")
                tmp.unlink(missing_ok=True)
            except Exception as e:
                result(False, f"negative control {p.name}", str(e))
        except Exception as e:
            result(False, f"verify {p.name}", str(e))


# ---------------------------------------------------------- 5. TRACE EXPORT
def check_trace(epi_path):
    head("5. TRACE EXPORT (validated by THEIR library, not yours)")
    if not epi_path:
        return skip("trace export", "pass --epi <file>")
    try:
        from agentrust_trace import iter_errors, verify_record, TRACE_PROFILE_V0_2
    except ImportError:
        return skip("trace export", "pip install agentrust-trace")

    outp = Path(tempfile.gettempdir()) / "preflight.trace.json"
    try:
        sub_env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run(
            [sys.executable, "-m", "epi_cli", "export", "trace", str(epi_path),
             "--out", str(outp), "--transcript-uri",
             f"https://github.com/{REPO}/releases/latest"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", env=sub_env, timeout=180)
        if not outp.exists():
            return result(False, "export trace produced a file",
                          ((r.stdout or "") + (r.stderr or ""))[-400:])
    except Exception as e:
        return result(False, "export trace ran", str(e))

    rec = json.loads(outp.read_text())

    errs = iter_errors(rec)
    result(not errs, "schema-valid per agentrust-trace 0.9.0",
           errs[0].message[:150] if errs else "iter_errors() empty")

    result(rec.get("eat_profile") == TRACE_PROFILE_V0_2,
           "eat_profile matches shipped constant", str(rec.get("eat_profile")))

    # signature verifies against the EMBEDDED key
    try:
        verify_record(rec, allow_embedded_key=True)
        result(True, "signature verifies", "verify_record() ok")
    except Exception as e:
        result(False, "signature verifies", f"{type(e).__name__}: {e}")

    # tamper must break it
    t = dict(rec); t["data_class"] = "public"
    try:
        verify_record(t, allow_embedded_key=True)
        result(False, "tamper detected", "MODIFIED RECORD STILL VERIFIED")
    except Exception as e:
        result(True, "tamper detected", type(e).__name__)

    # tool_transcript.hash must equal the real file digest
    want = "sha256:" + hashlib.sha256(Path(epi_path).read_bytes()).hexdigest()
    got = (rec.get("tool_transcript") or {}).get("hash")
    result(got == want, "tool_transcript.hash == sha256(.epi)",
           f"record={got}\n         actual={want}")

    # honesty checks
    pol = (rec.get("policy") or {}).get("bundle_hash", "")
    result(pol and set(pol.split(":")[-1]) != {"0"},
           "policy.bundle_hash is real, not all-zero", pol)

    origin = rec.get("origin") or {}
    result(origin.get("kind") == "log-import"
           and rec.get("runtime", {}).get("platform") == "software-only",
           "origin=log-import + platform=software-only",
           f"{origin.get('kind')} / {rec.get('runtime',{}).get('platform')}")

    for field, val in (("transparency", rec.get("transparency")),
                       ("transcript_uri",
                        (rec.get("tool_transcript") or {}).get("transcript_uri"))):
        if isinstance(val, str) and val.startswith("http"):
            try:
                import requests
                code = requests.head(val, timeout=20, allow_redirects=True).status_code
                result(code < 400, f"{field} URL resolves", f"HTTP {code} <- {val}")
            except Exception as e:
                skip(f"{field} URL", str(e))

    # sealer-key continuity: cnf.jwk.x must be the .epi's public key
    try:
        x = (rec.get("cnf") or {}).get("jwk", {}).get("x")
        if x:
            raw = base64.urlsafe_b64decode(x + "=" * (-len(x) % 4)).hex()
            print(f"  [INFO] cnf.jwk.x (hex) = {raw}")
            print("         -> compare against the .epi manifest public_key BY EYE.")
            print("            If they differ, the exporter used an ephemeral key.")
    except Exception as e:
        skip("cnf.jwk decode", str(e))


# ------------------------------------------------------------------- MAIN
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epi", action="append", default=[],
                    help="path to a .epi artifact (repeatable; mix old + new)")
    ap.add_argument("--sha", action="append",
                    default=["928e4c3", "3d2e684"],
                    help="commit SHAs that must no longer serve purged blobs")
    a = ap.parse_args()

    print("epi-recorder PRE-SUBMISSION PREFLIGHT")
    print(f"python: {sys.executable}")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    check_external(a.sha)
    check_install()
    check_canonicalization()
    check_legacy_signature_preimage()
    check_live_sample_epi()
    check_live_verifier_js()
    check_browser_verifier_js()
    check_embedded_viewer()
    check_artifacts(a.epi)
    check_trace(a.epi[0] if a.epi else None)

    head("SUMMARY")
    if FAILS:
        print(f"  {len(FAILS)} FAILED: " + ", ".join(FAILS))
        print("  Do not submit until these are green or consciously accepted.")
        sys.exit(1)
    print("  All executed checks passed.")


if __name__ == "__main__":
    main()
