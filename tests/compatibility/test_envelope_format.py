"""
Lock the envelope-v2 binary header layout.
"""

import struct
import uuid
from datetime import datetime, timezone

import pytest

from epi_core.container import (
    EPIContainer,
    EPI_ENVELOPE_MAGIC,
    EPI_ENVELOPE_VERSION,
    EPI_PAYLOAD_FORMAT_ZIP_V1,
    EPI_ENVELOPE_HEADER_SIZE,
    EPI_CONTAINER_FORMAT_ENVELOPE,
    _EPI_ENVELOPE_HEADER_STRUCT,
)


def test_envelope_constants_are_frozen():
    assert EPI_ENVELOPE_MAGIC == b"<!--"
    assert EPI_ENVELOPE_VERSION == 2
    assert EPI_PAYLOAD_FORMAT_ZIP_V1 == 0x01
    assert EPI_ENVELOPE_HEADER_SIZE == 128


def test_header_struct_size_matches_constant():
    assert _EPI_ENVELOPE_HEADER_STRUCT.size == EPI_ENVELOPE_HEADER_SIZE


def test_header_layout_offsets():
    """Verify the struct unpack produces fields in expected order and sizes."""
    # Build a known header byte pattern
    magic = b"<!--"
    version = 2
    payload_format = 0x01
    flags = 0
    length = 12345
    artifact_uuid = uuid.UUID("550e8400-e29b-41d4-a716-446655440000").bytes
    created_at_micros = 1704067200000000  # 2024-01-01 00:00:00 UTC
    payload_sha256 = b"\xab" * 32
    reserved_tail = b"\x00" * 56

    header_bytes = _EPI_ENVELOPE_HEADER_STRUCT.pack(
        magic, version, payload_format, flags, length,
        artifact_uuid, created_at_micros, payload_sha256, reserved_tail,
    )

    assert len(header_bytes) == 128

    unpacked = _EPI_ENVELOPE_HEADER_STRUCT.unpack(header_bytes)
    assert unpacked[0] == magic          # offset 0, 4 bytes
    assert unpacked[1] == version        # offset 4, 1 byte
    assert unpacked[2] == payload_format # offset 5, 1 byte
    assert unpacked[3] == flags          # offset 6, 2 bytes
    assert unpacked[4] == length         # offset 8, 8 bytes
    assert unpacked[5] == artifact_uuid  # offset 16, 16 bytes
    assert unpacked[6] == created_at_micros  # offset 24, 8 bytes
    assert unpacked[7] == payload_sha256     # offset 32, 32 bytes
    assert unpacked[8] == reserved_tail      # offset 64, 56 bytes


def test_envelope_file_starts_with_magic():
    """Any envelope-v2 .epi file must start with the magic bytes."""
    from epi_core.schemas import ManifestModel
    from epi_core.trust import sign_manifest
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    manifest = ManifestModel(
        spec_version="4.0.1",
        file_manifest={"steps.jsonl": "a" * 64},
    )
    key = Ed25519PrivateKey.from_private_bytes(b"\x00" * 32)
    signed = sign_manifest(manifest, key, key_name="test")

    tmp_dir = EPIContainer._make_temp_dir("compat_test_")
    (tmp_dir / "steps.jsonl").write_text('{}\n', encoding="utf-8")

    epi_path = tmp_dir / "test.epi"
    EPIContainer.pack(
        source_dir=tmp_dir,
        manifest=signed,
        output_path=epi_path,
        container_format=EPI_CONTAINER_FORMAT_ENVELOPE,
        generate_analysis=False,
    )

    first_bytes = epi_path.read_bytes()[:4]
    assert first_bytes == EPI_ENVELOPE_MAGIC

    # Header size check
    header_bytes = epi_path.read_bytes()[:128]
    assert len(header_bytes) == 128

    # New packs seal outer polyglot viewer SHA-256 in reserved_tail[0:32]
    header = EPIContainer._read_envelope_header(epi_path)
    assert header.reserved_tail[32:] == b"\x00" * 24
    viewer_hash = header.reserved_tail[:32]
    assert viewer_hash != b"\x00" * 32  # must be set when viewer is embedded
    ok, detail = EPIContainer.verify_polyglot_viewer(epi_path)
    assert ok is True
    assert detail is None


def test_polyglot_viewer_tamper_fails_integrity(tmp_path):
    """Flipping bytes in the outer polyglot HTML must fail verify integrity."""
    from epi_core.schemas import ManifestModel
    from epi_core.trust import sign_manifest
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from epi_core.container import EPI_ZIP_MARKER

    manifest = ManifestModel(
        spec_version="4.0.1",
        file_manifest={"steps.jsonl": "a" * 64},
    )
    key = Ed25519PrivateKey.from_private_bytes(b"\x01" * 32)
    signed = sign_manifest(manifest, key, key_name="test")

    source = tmp_path / "src"
    source.mkdir()
    (source / "steps.jsonl").write_text("{}\n", encoding="utf-8")
    epi_path = tmp_path / "sealed.epi"
    EPIContainer.pack(
        source_dir=source,
        manifest=signed,
        output_path=epi_path,
        container_format=EPI_CONTAINER_FORMAT_ENVELOPE,
        generate_analysis=False,
    )

    ok_before, _ = EPIContainer.verify_integrity(epi_path)
    assert ok_before is True

    raw = bytearray(epi_path.read_bytes())
    marker = raw.find(EPI_ZIP_MARKER)
    assert marker > EPI_ENVELOPE_HEADER_SIZE
    # Flip a byte in the CSS/HTML region (after header + comment close)
    flip_at = EPI_ENVELOPE_HEADER_SIZE + 10
    assert flip_at < marker
    raw[flip_at] ^= 0xFF
    epi_path.write_bytes(bytes(raw))

    ok_after, mismatches = EPIContainer.verify_integrity(epi_path)
    assert ok_after is False
    assert "__polyglot_viewer__" in mismatches


def test_legacy_zero_viewer_hash_still_readable(tmp_path):
    """All-zero reserved_tail viewer hash = legacy; still opens (display not sealed)."""
    from epi_core.schemas import ManifestModel
    from epi_core.trust import sign_manifest
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    manifest = ManifestModel(
        spec_version="4.0.1",
        file_manifest={"steps.jsonl": "a" * 64},
    )
    key = Ed25519PrivateKey.from_private_bytes(b"\x02" * 32)
    signed = sign_manifest(manifest, key, key_name="test")

    source = tmp_path / "src"
    source.mkdir()
    (source / "steps.jsonl").write_text("{}\n", encoding="utf-8")
    epi_path = tmp_path / "legacy_style.epi"
    EPIContainer.pack(
        source_dir=source,
        manifest=signed,
        output_path=epi_path,
        container_format=EPI_CONTAINER_FORMAT_ENVELOPE,
        generate_analysis=False,
    )

    # Zero out viewer hash to simulate a pre-fix artifact
    raw = bytearray(epi_path.read_bytes())
    # reserved_tail starts at offset 72 (magic4+ver1+fmt1+flags2+len8+uuid16+ts8+hash32 = 72)
    reserved_tail_off = 72
    raw[reserved_tail_off : reserved_tail_off + 32] = b"\x00" * 32
    epi_path.write_bytes(bytes(raw))

    header = EPIContainer._read_envelope_header(epi_path)
    assert header.reserved_tail[:32] == b"\x00" * 32
    ok, detail = EPIContainer.verify_polyglot_viewer(epi_path)
    assert ok is True
    assert detail is not None and "legacy" in detail
