from pathlib import Path

root = Path(".")
count = 0
files = []
for f in root.rglob("*.html"):
    try:
        t = f.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue  # binary-ish file, skip
    n = t.replace("epi-verify-core.js?v=33", "epi-verify-core.js?v=34")
    if n != t:
        f.write_text(n, encoding="utf-8")
        count += 1
        files.append(f.as_posix())
print("updated", count, "files:")
for name in files:
    print(" ", name)

# also update sw.js precache entry
sw = root / "sw.js"
if sw.exists():
    t = sw.read_text(encoding="utf-8")
    n = t.replace("epi-verify-core.js?v=33", "epi-verify-core.js?v=34")
    if n != t:
        sw.write_text(n, encoding="utf-8")
        print("sw.js updated")
