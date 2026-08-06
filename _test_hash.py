"""
Test: does the raw-text canonical hash approach produce the same SHA-256
as Python's get_canonical_hash for the demo artifact?
"""
import json, hashlib, base64, re
from pathlib import Path
from epi_core.schemas import ManifestModel
from epi_core.serialize import get_canonical_hash

epi = Path("epi-recordings/demo_refund.epi")

# 1. Python canonical hash (what was signed)
m = ManifestModel.__pydantic_validator__.validate_json(epi.read_bytes() and "")

# Load manifest the standard way
from epi_core.container import EPIContainer
m = EPIContainer.read_manifest(epi)
py_hash = get_canonical_hash(m, exclude_fields={"signature"})
print(f"Python canonical hash: {py_hash}")

# 2. Raw text approach (what the browser should produce)
raw_manifest = None
for enc in ["utf-8"]:
    with zipfile.ZipFile(epi) as zf:
        raw_manifest = zf.read("manifest.json").decode(enc)
        break
manifest_obj = json.loads(raw_manifest)
del manifest_obj["signature"]
# Python canonical of parsed raw text
canonical_from_raw = json.dumps(manifest_obj, sort_keys=True, separators=(",", ":"))
raw_hash = hashlib.sha256(canonical_from_raw.encode("utf-8")).hexdigest()
print(f"Raw-text canonical hash: {raw_hash}")
print(f"Match: {py_hash == raw_hash}")
