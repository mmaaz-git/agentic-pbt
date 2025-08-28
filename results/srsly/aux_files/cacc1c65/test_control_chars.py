#!/usr/bin/env python3
"""Test various control characters for round-trip issues."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

from srsly._yaml_api import yaml_dumps, yaml_loads

# Test various Unicode control characters
control_chars = [
    ('\x85', 'U+0085 (Next Line)'),
    ('\xa0', 'U+00A0 (Non-breaking space)'),
    ('\u2028', 'U+2028 (Line Separator)'),
    ('\u2029', 'U+2029 (Paragraph Separator)'),
]

print("Testing control characters in dictionary keys:\n")

bugs_found = []

for char, description in control_chars:
    test_key = f'test{char}'
    data = {test_key: None}
    
    try:
        serialized = yaml_dumps(data)
        deserialized = yaml_loads(serialized)
        
        if list(data.keys())[0] != list(deserialized.keys())[0]:
            print(f"❌ BUG FOUND with {description}:")
            print(f"   Original key: {repr(list(data.keys())[0])}")
            print(f"   Deserialized: {repr(list(deserialized.keys())[0])}")
            bugs_found.append((char, description))
        else:
            print(f"✓ OK: {description}")
    except Exception as e:
        print(f"⚠ Error with {description}: {e}")

print(f"\n\nTotal bugs found: {len(bugs_found)}")
if bugs_found:
    print("Affected characters:")
    for char, desc in bugs_found:
        print(f"  - {desc}")