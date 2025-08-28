#!/usr/bin/env python3
"""Demonstrate the real impact of the Unicode normalization bug."""

from fire.parser import DefaultParseValue

# Test various Unicode characters that might be affected
test_cases = [
    ('µ', 'MICRO SIGN (U+00B5)', 'Common in scientific units like µm, µs'),
    ('Ω', 'OHM SIGN (U+2126)', 'Used for electrical resistance'),
    ('K', 'KELVIN SIGN (U+212A)', 'Temperature unit'),
    ('Å', 'ANGSTROM SIGN (U+212B)', 'Length unit in physics'),
]

print("Testing Unicode normalization in fire.parser.DefaultParseValue:\n")
print("=" * 70)

bugs_found = []

for char, name, usage in test_cases:
    result = DefaultParseValue(char)
    is_changed = char != result
    
    print(f"Input:  '{char}' - {name}")
    print(f"        Unicode: U+{ord(char):04X}")
    print(f"Output: '{result}'")
    if is_changed:
        print(f"        Unicode: U+{ord(result):04X}")
        print(f"        ⚠️  CHARACTER CHANGED!")
        bugs_found.append((char, result, name))
    else:
        print(f"        ✓ Unchanged")
    print(f"Usage:  {usage}")
    print("-" * 70)

if bugs_found:
    print("\n🐛 BUG SUMMARY:")
    print("=" * 70)
    print("DefaultParseValue unexpectedly modifies the following Unicode characters:")
    for original, transformed, name in bugs_found:
        print(f"  • '{original}' (U+{ord(original):04X}) → '{transformed}' (U+{ord(transformed):04X}) - {name}")
    
    print("\nIMPACT:")
    print("  - Command-line arguments containing these characters will be silently modified")
    print("  - This violates the documented behavior that simple strings pass through unchanged")
    print("  - Scientific applications using units (µm, µs, Ω, Å) are affected")
    print("  - File paths or data containing these characters will be corrupted")
    
    # Demonstrate a concrete scenario
    print("\nCONCRETE EXAMPLE:")
    print("  If a user runs: fire my_script.py process_file 'data_10µm.csv'")
    print("  The function receives: 'data_10μm.csv' (different character!)")
    print("  Result: FileNotFoundError if the file uses the micro sign")
else:
    print("\n✅ All tested Unicode characters passed through unchanged")