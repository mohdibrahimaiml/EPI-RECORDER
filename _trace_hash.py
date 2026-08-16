"""Get the exact canonical string Python used for signing."""
import json, hashlib
from pathlib import Path
from epi_core.container import EPIContainer
from epi_core.serialize import get_canonical_hash
from epi_core.schemas import ManifestModel

epi = Path("epi-recordings/demo_refund.epi")
m = EPIContainer.read_manifest(epi)
py_hash = get_canonical_hash(m, exclude_fields={"signature"})
print("Python canonical hash:", py_hash)

# get_canonical_hash uses model_dump + _normalize_value
# Let me reproduce it step by step
md = m.model_dump(mode="json")
md.pop("signature", None)

# _normalize_value
from datetime import datetime, timezone
def normalize(v):
    if isinstance(v, datetime):
        if v.tzinfo is None:
            v = v.replace(microsecond=0, tzinfo=timezone.utc)
        else:
            v = v.astimezone(timezone.utc).replace(microsecond=0)
        return v.strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(v, dict):
        return {k2: normalize(v2) for k2, v2 in v.items()}
    if isinstance(v, list):
        return [normalize(x) for x in v]
    return v

# Actually the normalize function is more complex - let me just check what get_canonical_hash produces
# by importing the internal function
from epi_core.serialize import _normalize_value
def normalize_recursive(obj):
    if isinstance(obj, dict):
        return {k: normalize_recursive(_normalize_value(v)) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [normalize_recursive(_normalize_value(x)) for x in obj]
    return _normalize_value(obj)

normalized = normalize_recursive(md)
canonical = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
print("Step-by-step canonical hash:", h)
print("Match:", py_hash == h)

# Show differences between raw json.dumps and canonical
raw_canon = json.dumps(md, sort_keys=True, separators=(",", ":"))
# Find differences in a compact form
for key in sorted(md.keys()):
    raw_v = json.dumps(md[key], sort_keys=True, separators=(",", ":"))
    norm_v = json.dumps(normalized[key], sort_keys=True, separators=(",", ":"))
    if raw_v != norm_v:
        print(f"DIFF {key}:")
        print(f"  raw:  {raw_v[:100]}")
        print(f"  norm: {norm_v[:100]}")
