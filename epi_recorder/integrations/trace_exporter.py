"""
TRACE exporter — convert a sealed .epi into a Level 0 log-import TRACE Trust Record.

Uses ONLY shipped TRACE v0.2 fields (tool_transcript, origin log-import,
enforcement_mode declared, software-only). Validated via agentrust_trace.iter_errors
before signing.

Spec: trace-v0.2.json
"""
from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any, Dict, Optional

from epi_core.container import EPIContainer


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _epi_file_hash(epi_path: Path) -> str:
    h = hashlib.sha256()
    with open(epi_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _count_steps(epi_path: Path) -> int:
    try:
        return EPIContainer.count_steps(epi_path)
    except Exception:
        try:
            return len(list(EPIContainer.read_steps(epi_path)))
        except Exception:
            return 0


def epi_to_trace_record(
    epi_path: Path | str,
    transcript_uri: Optional[str] = None,
    *,
    subject: Optional[str] = None,
    model_provider: str = "epi-recorder",
    model_id: Optional[str] = None,
    data_class: str = "internal",
    extra_transparency: str = "https://epilabs.org/transparency/receipt",
    appraiser: str = "https://epilabs.org/verifier",
) -> Dict[str, Any]:
    """
    Build an unsigned TRACE v0.2 Trust Record from a sealed .epi.

    The .epi file is the transcript; tool_transcript.hash commits to it.
    Caller must sign via agentrust_trace.sign_record before distribution.
    """
    epi_path = Path(epi_path)
    if not epi_path.exists():
        raise FileNotFoundError(f".epi not found: {epi_path}")

    manifest = EPIContainer.read_manifest(epi_path)
    # Derive fields from manifest
    workflow_id = str(getattr(manifest, "workflow_id", ""))
    # model_id fallback to workflow_name or file stem
    if model_id is None:
        model_id = getattr(manifest, "workflow_name", None) or epi_path.stem or "4.4.1"
    if subject is None:
        # SPIFFE or DID URI required — use spiffe with artifact UUID
        subject = f"spiffe://epilabs.org/epi-recorder/{workflow_id}" if workflow_id else "spiffe://epilabs.org/epi-recorder/unknown"

    # Data classification: prefer governance.data_class if present
    gov = getattr(manifest, "governance", None) or {}
    if isinstance(gov, dict) and gov.get("data_class"):
        data_class = str(gov["data_class"])

    now = int(time.time())
    digest_zero = "sha256:" + "00" * 32
    epi_hash = _epi_file_hash(epi_path)
    call_count = _count_steps(epi_path)
    # Transcript URI: require explicit for production; default is a placeholder that warns
    if transcript_uri is None:
        # Use manifest governance URL if available, else placeholder (caller should pass real hosted URL)
        transcript_uri = f"https://epilabs.org/artifacts/{epi_path.name}"
        # Placeholder — CLI will warn that this does not resolve until hosted

    # Bundle hash: hash the actual policy block if present, not zeros
    bundle_hash = digest_zero
    try:
        # Prefer policy.json (authored policy) over policy_evaluation.json
        for candidate in ("policy.json", "policy_evaluation.json"):
            try:
                pol_bytes = EPIContainer.read_member_bytes(epi_path, candidate)
                if pol_bytes and len(pol_bytes) > 10:
                    bundle_hash = f"sha256:{hashlib.sha256(pol_bytes).hexdigest()}"
                    break
            except Exception:
                continue
    except Exception:
        pass

    # Transparency: prefer SCITT receipt URL if artifact has one, else require explicit
    # If governance.scitt.service_url exists, use it; else use placeholder that CLI warns about
    transparency_uri = extra_transparency
    try:
        gov_scitt = (getattr(manifest, "governance", None) or {}).get("scitt") if isinstance(getattr(manifest, "governance", None), dict) else None
        if gov_scitt and isinstance(gov_scitt, dict) and gov_scitt.get("service_url"):
            transparency_uri = gov_scitt["service_url"]
            if gov_scitt.get("entry_id"):
                transparency_uri = f"{transparency_uri.rstrip('/')}/{gov_scitt['entry_id']}"
    except Exception:
        pass

    record: Dict[str, Any] = {
        "eat_profile": "tag:agentrust-io.com,2026:trace-v0.2",
        "iat": now,
        "subject": subject,
        "model": {
            "provider": model_provider,
            "model_id": str(model_id)[:128],
        },
        "runtime": {
            "platform": "software-only",
            "measurement": digest_zero,
        },
        "policy": {
            "bundle_hash": bundle_hash,
            "enforcement_mode": "declared",
        },
        "data_class": data_class,
        "tool_transcript": {
            "hash": epi_hash,
            "call_count": int(call_count),
            "transcript_uri": transcript_uri,
        },
        "origin": {
            "kind": "log-import",
            "producer": f"epi-recorder/{manifest.spec_version if hasattr(manifest, 'spec_version') else '4.4.1'}",
            "source_event_id": workflow_id or epi_path.name,
            "ingested_at": now,
        },
        "build_provenance": {
            "slsa_level": 0,
            "digest": digest_zero,
        },
        "appraisal": {
            "status": "none",
            "verifier": appraiser,
        },
        "transparency": transparency_uri,
        "cnf": {
            # Placeholder — sign_record will replace with real JWK
            "jwk": {"kty": "OKP", "crv": "Ed25519", "x": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"},
        },
    }
    # Attach warnings for placeholder URLs so CLI can surface them
    record["_epi_warnings"] = []
    if "artifacts" in transcript_uri and "epilabs.org/artifacts" in transcript_uri:
        record["_epi_warnings"].append(
            f"transcript_uri is placeholder {transcript_uri} — pass --transcript-uri with the real hosted .epi URL"
        )
    if transparency_uri == "https://epilabs.org/transparency/receipt":
        record["_epi_warnings"].append(
            "transparency is placeholder — no SCITT receipt bound; point at your SCITT log entry or TSA receipt"
        )
    return record


def _find_sealing_private_key(manifest) -> tuple[object, str] | None:
    """Find the local private key that matches the manifest's sealing public key.

    Returns (private_key, key_name) or None if not found (caller should use ephemeral).
    """
    pub_hex = getattr(manifest, "public_key", None)
    if not pub_hex:
        return None
    try:
        from epi_core.keys import KeyManager

        km = KeyManager()
        want = pub_hex.strip().lower()
        for info in km.list_keys():
            name = info.get("name") or ""
            try:
                raw = km.load_public_key(name)
                if raw.hex().lower() == want:
                    priv = km.load_private_key(name)
                    return priv, name
            except Exception:
                continue
    except Exception:
        return None
    return None
