from epi_core.container import EPIContainer
from epi_core.trust import verify_embedded_manifest_signature
from pathlib import Path
import re, json

epi = Path("epi-recordings/demo_refund.epi")
m = EPIContainer.read_manifest(epi)

# 1. What does the real verification say?
sig_ok, name, msg = verify_embedded_manifest_signature(m)
with open("_verify_output.txt", "w") as out:
    out.write("=== REAL ED25519 VERIFICATION ===\n")
    out.write(f"  valid: {sig_ok}\n")
    out.write(f"  name: {name}\n")
    out.write(f"  msg: {msg}\n\n")
    
    # 2. What does the baked viewer store?
    html = EPIContainer._create_embedded_viewer(epi, m)
    tag = re.search(r'epi-preloaded-cases[^>]*>([^<]+)', html)
    if tag:
        data = json.loads(tag.group(1))
        case = data["cases"][0]
        sig = case.get("signature", {})
        man = case.get("manifest", {})
        
        out.write("=== BAKED VIEWER DATA ===\n")
        out.write(f"  signature.valid: {sig.get('valid')}\n")
        out.write(f"  signature.reason: {sig.get('reason', '')[:100]}\n")
        out.write(f"  manifest.signature present: {bool(man.get('signature'))}\n\n")
        
        # 3. What would the header pill show?
        sig_valid = sig.get('valid')
        if sig_valid == None:
            pill = "SIGNATURE NOT VERIFIED"
        elif sig_valid == True:
            pill = "SIGNATURE VALID"
        else:
            pill = "SIGNATURE INVALID"
        out.write("=== HEADER PILL ===\n")
        out.write(f"  Would show: {pill}\n\n")
        
        # 4. What would the #ind-signature show?
        if sig_valid == True:
            indicator = "VALID"
        elif sig_valid == False and not man.get('signature'):
            indicator = "UNSIGNED"
        elif sig_valid == False:
            indicator = "INVALID"
        else:
            indicator = "NOT VERIFIED"
        out.write("=== #ind-signature ===\n")
        out.write(f"  Would show: {indicator}\n\n")
        
        # 5. What does caseData.files contain?
        files = case.get("files", {})
        out.write("=== caseData.files ===\n")
        out.write(f"  keys: {sorted(files.keys())}\n")
        out.write(f"  manifest.json: {'PRESENT' if 'manifest.json' in files else 'MISSING'}\n")
        if 'manifest.json' in files:
            import base64
            manifest_bytes = base64.b64decode(files['manifest.json'])
            manifest_obj = json.loads(manifest_bytes)
            out.write(f"  manifest.json has signature: {bool(manifest_obj.get('signature'))}\n")
            out.write(f"  manifest.json has public_key: {bool(manifest_obj.get('public_key'))}\n")

print("done - check _verify_output.txt")
