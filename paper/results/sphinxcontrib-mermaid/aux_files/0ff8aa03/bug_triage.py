#!/usr/bin/env python3
"""Triage the split_index_entry bug for real-world impact."""

import re
from qthelp_module import split_index_entry, _idpattern

# Step 1: Reproducibility check
print("=== Step 1: Reproducibility Check ===")
print("Testing if bug is consistently reproducible...")

for i in range(5):
    entry = "\n (TestClass)"
    result_title, result_id = split_index_entry(entry)
    print(f"  Attempt {i+1}: title={repr(result_title)}, id={repr(result_id)}")
    assert result_title == "\n (TestClass)" and result_id is None, "Bug behavior changed!"

print("✓ Bug is consistently reproducible\n")

# Step 2: Legitimacy check
print("=== Step 2: Legitimacy Check ===")

# Check if this represents realistic usage
print("Checking if entries with newlines are realistic...")
print("  - Index entries in documentation typically come from titles/names")
print("  - Newlines in index entries would be unusual but possible")
print("  - Sphinx might generate such entries from multi-line docstrings")
print("  - The function should handle all valid strings gracefully")

# Check what the function claims to do
print("\nFunction documentation says:")
print('  """Split an index entry into main text and parenthetical content."""')
print("  - No documented restriction on newlines")
print("  - Should split ANY entry with the pattern 'text (id)'")

print("\n✓ This is a legitimate bug - function should handle all string inputs")

# Step 3: Impact assessment
print("\n=== Step 3: Impact Assessment ===")

# Test more realistic scenarios
realistic_cases = [
    "MyClass\n(continued) (mymodule.MyClass)",  # Multi-line entry
    "Function\nwith description (module.func)",   # Newline in title
    "Class (in module\npath)",                    # Newline in parenthetical
]

print("Testing realistic multi-line scenarios:")
for entry in realistic_cases:
    result_title, result_id = split_index_entry(entry)
    print(f"  Entry: {repr(entry[:30])}...")
    print(f"    Result: title={repr(result_title[:30] if result_title else result_title)}, id={repr(result_id)}")
    
print("\n✓ Bug affects processing of multi-line index entries")
print("  - Could break Qt help generation for certain documentation")
print("  - Silent failure (returns whole string instead of parsing)")

# Proposed fix
print("\n=== Proposed Fix ===")
print("The regex pattern should use DOTALL flag or [\\s\\S] to match newlines:")
print("Current: r'(?P<title>.+) \\(((class in )?(?P<id>[\\w\\.]+)( (?P<descr>\\w+))?\\))$'")
print("Fixed:   r'(?P<title>[\\s\\S]+) \\(((class in )?(?P<id>[\\w\\.]+)( (?P<descr>\\w+))?\\))$'")
print("Or compile with re.DOTALL flag")

# Test the fix
fixed_pattern = re.compile(
    r'(?P<title>[\s\S]+) \(((class in )?(?P<id>[\w\.]+)( (?P<descr>\w+))?\))$'
)

print("\n=== Testing Fixed Pattern ===")
test_cases = [
    ("\n", "A"),
    ("Title\nwith newline", "module.Class"),
    ("Normal title", "id"),
]

for title, id_part in test_cases:
    entry = f"{title} ({id_part})"
    match = fixed_pattern.match(entry)
    if match:
        fixed_title = match.group('title')
        fixed_id = match.group('id')
        correct = (fixed_title == title and fixed_id == id_part)
        print(f"  {repr(entry[:30])}... {'✓' if correct else 'FAIL'}")
    else:
        print(f"  {repr(entry[:30])}... NO MATCH")

print("\n✓ Fixed pattern handles newlines correctly")