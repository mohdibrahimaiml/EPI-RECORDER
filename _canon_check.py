"""Verify the fix: compute canonical hash from raw manifest text vs JS re-serialization."""
import json, hashlib, zipfile, base64
from pathlib import Path
from epi_core.container import EPIContainer
from epi_core.serialize import get_canonical_hash

epi = Path("epi-recordings/demo_refund.epi")

# Python canonical hash
m = EPIContainer.read_manifest(epi)
py_hash = get_canonical_hash(m, exclude_fields={"signature"})
print(f"Python canonical hash: {py_hash}")

# Simulate: raw manifest text from archive
with zipfile.ZipFile(epi) as zf:
    raw_text = zf.read("manifest.json").decode("utf-8")
raw_obj = json.loads(raw_text)
del raw_obj["signature"]
canonical_raw = json.dumps(raw_obj, sort_keys=True, separators=(",", ":"))
raw_hash = hashlib.sha256(canonical_raw.encode("utf-8")).hexdigest()
print(f"Raw-text canonical hash: {raw_hash}")
print(f"Match: {py_hash == raw_hash}")
print(f"Raw has 900.0: {'900.0' in canonical_raw}")

# Simulate: JS re-serialization (what crypto.js used to do)
md = m.model_dump(mode="json")
md.pop("signature", None)
canonical_js = json.dumps(md, sort_keys=True, separators=(",", ":"))
js_hash = hashlib.sha256(canonical_js.encode("utf-8")).hexdigest()
print(f"Model-dump canonical hash: {js_hash}")
print(f"Match: {py_hash == js_hash}")
print(f"Model-dump has 900.0: {'900.0' in canonical_js}")

# The raw text fix produces the same hash as Python
# The model-dump approach also preserves floats because Python keeps 900.0
# The issue is when JS JSON.parse strips .0 before re-serializing
# So the raw text approach is correct - it passes the actual bytes through
print()
print("Fix approach: pass raw manifest text (base64) to verifyManifestSignature")
print("so canonical JSON preserves .0 from original Python output")
