"""
Script to fix Unicode encoding issues in CLI files by replacing
Unicode symbols with ASCII equivalents.
"""
from pathlib import Path

# Define replacements
replacements = [
    ("✅", "[OK]"),
    ("❌", "[FAIL]"),
    ("⚠️", "[WARN]"),
    ("ℹ️", "[INFO]"),
]

# Files to fix
files_to_fix = [
    "epi_cli/keys.py",
    "epi_cli/verify.py",
    "epi_cli/view.py",
    "epi_cli/record.py",
    "epi_cli/run.py",
    "epi_cli/main.py",
]

root = Path("c:/Users/dell/epi-recorder")

print("=" * 60)
print("FIXING UNICODE ISSUES IN CLI FILES")
print("="* 60)

total_replacements = 0

for file_path in files_to_fix:
    full_path = root / file_path
    
    if not full_path.exists():
        print(f"\n[SKIP] {file_path} - File not found")
        continue
    
    print(f"\n[PROCESSING] {file_path}")
    
    # Read file
    content = full_path.read_text(encoding='utf-8')
    original_content = content
    
    file_replacements = 0
    
    # Apply replacements
    for unicode_char, ascii_replacement in replacements:
        count = content.count(unicode_char)
        if count > 0:
            content = content.replace(unicode_char, ascii_replacement)
            file_replacements += count
            print(f"  - Replaced {count}x '{replacements.index((unicode_char, ascii_replacement))}' with '{ascii_replacement}'")
    
    # Write back if changed
    if content != original_content:
        full_path.write_text(content, encoding='utf-8')
        print(f"  [OK] Saved (Total: {file_replacements} replacements)")
        total_replacements += file_replacements
    else:
        print(f"  [OK] No changes needed")

print("\n" + "=" * 60)
print(f"COMPLETE: {total_replacements} total replacements made")
print("=" * 60)
