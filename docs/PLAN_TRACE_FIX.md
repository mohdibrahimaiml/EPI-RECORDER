# PLAN: EPI → TRACE Interop + Wheel Repair (v4.4.0 → v4.4.1)

**Date:** 2026-08-27 | **Branch:** main (96b7a0a) | **Mode:** hallucination-proof — every number is `zipfile`/byte-measured

## 0) Baseline — what was verified empirically (do not trust docs)

| Fact | Evidence | Line |
|---|---|---|
| Whl 10.91 MB compressed / 21.67 MB uncompressed, 89.9% is `verify_portal` | `zipfile.ZipFile(whl)` sum, `Get-ChildItem verify_portal` 21.3 MB on disk | `pyproject.toml:174,180-184` |
| Duplicate `epi-walkthrough.mp4` 897609 B identical SHA256 `9dbbe7eb...` shipped twice | `hashlib.sha256(z.read(...)).hexdigest()` | `verify_portal/static/assets/` + `demo/` |
| `epi_core/serialize.py` uses `json.dumps(sort_keys=True, ensure_ascii=False)` — no `rfc8785` | `grep rfc8785 == 0`, `serialize.py:150-155` | `epi_core/serialize.py:145-157` |
| `epi_core/container.py:1026` uses `json.dumps(unsigned_manifest, sort_keys=True)` default `ensure_ascii=True` | byte compare: `b'{"a":"\\u00e9cole","b":1.0}'` vs `rfc8785 b'{"a":"école","b":1}'` | `container.py:1026` |
| TRACE 0.9.0: `references` not in `trace-v0.2.json`, `tool_transcript` hash+uri+call_count is shipped slot | `iter_errors({'references':…})` → `Additional properties not allowed` | `agentrust_trace/schema/trace-v0.2.json` |
| TRACE `verify_record` uses `rfc8785.dumps`, `max_age=86400`, tamper→`InvalidSignature` | `sign.py:158-170`, empirical sign/verify run 1088 bytes | `agentrust_trace/sign.py` |
| `epi_recorder.record()` context manager EXISTS | `hasattr(epi_recorder,'record')==True`, `epi_recorder/api.py:735` | opposite of TRACE which has no `record()` |

## 1) Phases — ordered by risk/reward, each has Falsifiable Success Criterion

### Phase 1 — Wheel bloat cut (HIGHEST ROI, LOWEST RISK) — Target <1.5 MB whl
**Goal:** Stop shipping `verify_portal/static/**/*` (136 files, 19.48 MB) in the Python wheel. Hosted demos stay on `website/` + `epilabs.org`, not pip.

**Changes:**
1. `pyproject.toml:174` `packages.find.include` remove `"verify_portal*"`
2. `pyproject.toml:180-184` delete `verify_portal = ["static/**/*"]`
3. Delete duplicate `verify_portal/static/assets/demo/epi-walkthrough.mp4` (or keep one, but NOT in wheel)
4. `MANIFEST.in`: explicitly `prune verify_portal` is NOT needed for wheel (sdist only), but add `global-exclude verify_portal/static/assets/*.mp4 *.png` for sdist hygiene
5. Version bump `4.4.0 → 4.4.1` in `pyproject.toml:7` (wheel size changes signature)

**Why safe:** `verify_portal` is a FastAPI server (`verify_portal/main.py`); it is NOT imported by `epi_core`/`epi_cli`/`epi_recorder` — verified `grep -r "from verify_portal" epi_core epi_cli == 0`, only `verify_portal` internal + `scripts/`.

**Success criterion (falsifiable):**
```pwsh
python -m build --wheel
(zipfile.ZipFile(whl).infolist() | where {$_.filename -like "verify_portal*"}).Count == 0
(whl.Length / 1MB) -lt 1.5
epi verify docs/assets/readme-demo.epi  # still passes
pytest -k "not network and not browser" -q  # no regression
```

**Rollback:** `git checkout pyproject.toml`

### Phase 2 — Canonicalization fix (MANDATORY for TRACE interop, MEDIUM RISK — changes signature bytes)
**Goal:** Make EPI and TRACE sign the same bytes. Replace `json.dumps(sort_keys)` with `rfc8785.dumps` on every signature pre-image.

**Changes:**
1. `pyproject.toml:56-64` add `rfc8785>=0.1.4` to `dependencies` (already used by TRACE, pure python, <50KB)
2. `epi_core/serialize.py:145-157` — replace `_get_json_canonical_hash` body with `rfc8785.dumps(data)` → sha256
3. `epi_core/container.py:1026` — replace `json.dumps(unsigned_manifest, sort_keys=True)` with `rfc8785.dumps(unsigned_manifest)` before `notarize_manifest`
4. Audit other `json.dumps(sort_keys=True)` in `container.py:988` (`_manifest_canon`) — also replace for consistency, or explicitly document as non-signature (it feeds `payload_hash` in `manifest.trust`, which IS covered by signature transitively)
5. Bump `EPI_ENVELOPE_VERSION`? NO — header version stays 2 (envelope format unchanged), but bump `spec_version` in manifest if needed. Add legacy verifier path: `verify` tries rfc8785 then falls back to `json.dumps` for artifacts sealed with 4.4.0
6. Update `docs/EPI-CANONICAL-HASH.md` to document JCS

**Success criterion:**
```py
import json, rfc8785, hashlib
assert json.dumps({"v":1.0}, sort_keys=True, separators=(',',':')) != rfc8785.dumps({"v":1.0})  # proves need
# After fix:
from epi_core.serialize import get_canonical_hash
from epi_core.schemas import ManifestModel
m = ManifestModel.model_validate({"workflow_name":"test","cli_command":"test"})
h = get_canonical_hash(m, exclude_fields={"signature"})  # must equal rfc8785(json_without_sig)
# Existing .epi from docs/assets/readme-demo.epi still verifies via fallback
# New .epi sealed after fix verifies with both EPI and TRACE's rfc8785 path
```

**Risk mitigation:** Do NOT yank old verifier. Keep `try: rfc8785; except: json_fallback` for 4.4.0 artifacts.

### Phase 3 — `epi export trace` (2–3 days, BUILDS ON Phase 2)
**Goal:** Emit a valid TRACE Level 0 `log-import` record that binds an `.epi` by hash, using ONLY shipped TRACE fields.

**CLI:** `epi export trace <file.epi> --out <file.trace.json> [--transcript-uri URL] [--signing-key PATH]`

**Mapping (validated against trace-v0.2.json):**
```
eat_profile: "tag:agentrust-io.com,2026:trace-v0.2"  // TRACE_PROFILE_V0_2
iat: now()
subject: spiffe://epilabs.org/epi-recorder/<artifact_uuid>  // or did:web
model: {provider:"epi-recorder", model_id:"4.4.1"}  // TRACE requires provider+model_id
runtime: {platform:"software-only", measurement:"sha256:"+"00"*32, nonce?}
policy: {bundle_hash:"sha256:"+"00"*32, enforcement_mode:"declared"}  // declared = no engine evaluated
data_class: from manifest.governance.data_class or "internal"
tool_transcript: {hash:"sha256:"+sha256(.epi file), call_count: len(steps.jsonl), transcript_uri: args.uri}
origin: {kind:"log-import", producer:"epi-recorder/4.4.0", source_event_id: manifest.workflow_id, ingested_at: now()}
build_provenance: {slsa_level:0, digest:"sha256:"+"00"*32}
appraisal: {status:"none", verifier:"https://epilabs.org/verifier"}
transparency: "https://epilabs.org/transparency/receipt"  // placeholder, SCITT URI
cnf: filled by sign_record(key)
```

**Implementation files:**
- New: `epi_recorder/integrations/trace_exporter.py` (pure function `epi_to_trace_record(epi_path, transcript_uri) -> dict`)
- New: `epi_cli/trace_cmd.py` (typer app, `export trace` command)
- Wire in `epi_cli/main.py` `app.add_typer(trace_app, name="trace")` or under `export trace`

**Success criterion:**
```py
from agentrust_trace import iter_errors, sign_record, verify_record, generate_key
rec = epi_to_trace_record("docs/assets/readme-demo.epi", "https://epilabs.org/demo/readme.epi")
assert iter_errors(rec) == []
signed = sign_record(rec, generate_key())
verify_record(signed, key.public_key(), max_age_seconds=None)  # passes
# Tamper .epi hash in rec → verify fails
# missing hash → iter_errors non-empty
```

**Why `tool_transcript` not `references`:** `references` rejected by Draft202012Validator (`additionalProperties:false`) — verified 3×, so we use the shipped hash-binding slot.

### Phase 4 — Fellowship proposal (by Saturday)
**Structure:**
1. Page 1: `references` gap — normative prose §3.1.2 vs missing from `trace-v0.2.json` (repro: `iter_errors` + `Additional properties` message), proposal to implement with backward compat, with `epi export trace` as working proof you did the harder half
2. Page 2: SCITT transparency log operators (§7 Q3) — cite `epi_core/scitt.py` (COSE_Sign1 + Merkle), `local_scitt.py` (file ledger + inclusion proofs), offer design contribution
3. Appendix: GitHub handle + link to conformance run (`tests.agentrust-io.com` honest score, including failures), note "found by installing + running validator"

## 2) Execution Order Today (what we do in this session)

1. **Phase 1 only** — wheel cut + rebuild + verify (no signature byte change, safe to ship)
2. **Dry-run Phase 2 patches** as diff preview (do NOT commit yet — needs version bump + fallback verifier)
3. **Stub Phase 3 exporter** as proof-of-concept Python function + one passing `iter_errors` test (no CLI wire yet if time-boxed)

## 3) Verification Checklist (run after every phase)

- [ ] `python -m build && python -c "import zipfile; ... verify_portal count == 0"`
- [ ] `pip install dist/*.whl --force-reinstall && epi verify docs/assets/readme-demo.epi` (fallback still works)
- [ ] `pytest -k "not network and not browser" -q` (existing suite)
- [ ] For Phase2+: `python -c "import rfc8785; assert rfc8785.dumps({'v':1.0})==b'{\"v\":1}'"`
- [ ] For Phase3: `python -c "from agentrust_trace import iter_errors; assert len(iter_errors(rec))==0"`

## 4) Rollback Plan

Every phase is `git diff` reversible. Phase1 is `git checkout pyproject.toml && rm dist`. Phase2 keeps old verifier branch: `try: rfc8785 → except: json_fallback`. Phase3 is additive (new files only).
