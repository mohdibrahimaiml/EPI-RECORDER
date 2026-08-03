from pathlib import Path

root = Path(__file__).resolve().parents[2]
idx = root / "website" / "index.html"
t = idx.read_text(encoding="utf-8")
t = t.replace("home-verify.js?v=34", "home-verify.js?v=35")
t = t.replace("epi-verify-core.js?v=33", "epi-verify-core.js?v=34")
idx.write_text(t, encoding="utf-8", newline="\n")

vp = root / "website" / "verify" / "index.html"
vt = vp.read_text(encoding="utf-8")
old = 'id="dropZone" class="drop-zone"'
new = 'id="dropZone" class="drop-zone" role="button" tabindex="0" aria-label="Drop or choose a .epi file"'
if old in vt and "role=" not in vt[vt.find("dropZone") : vt.find("dropZone") + 80]:
    vt = vt.replace(old, new, 1)
vp.write_text(vt, encoding="utf-8", newline="\n")
print("index home-verify", "v=35" in idx.read_text(encoding="utf-8"))
print("verify emdash", vp.read_text(encoding="utf-8").count("\u2014"))
print("verify Pro Team", "Pro / Team" in vp.read_text(encoding="utf-8"))
