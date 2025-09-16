#!/usr/bin/env python3
"""Investigate title validation bug."""

import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.oam as oam

# Test various characters
test_cases = [
    ('µ', 'Greek letter mu'),
    ('¹', 'Superscript 1'),
    ('test123', 'ASCII alphanumeric'),
    ('TEST', 'Uppercase ASCII'),
    ('123', 'Numbers only'),
    ('αβγ', 'Greek letters'),
    ('№', 'Numero sign'),
    ('Ⅲ', 'Roman numeral'),
]

print("Testing title validation...")
print("=" * 60)

# Check what Python's isalnum() says vs what troposphere accepts
valid_names = re.compile(r"^[a-zA-Z0-9]+$")

for title, description in test_cases:
    python_says = title.isalnum()
    regex_says = bool(valid_names.match(title))
    
    print(f"\nTitle: '{title}' ({description})")
    print(f"  Python isalnum(): {python_says}")
    print(f"  Troposphere regex: {regex_says}")
    
    if python_says != regex_says:
        print(f"  ⚠️  MISMATCH: Python says {python_says}, regex says {regex_says}")
    
    # Try to create an object
    try:
        link = oam.Link(title, ResourceTypes=['test'], SinkIdentifier='test')
        print(f"  ✓ Object created successfully")
    except ValueError as e:
        print(f"  ✗ Object creation failed: {e}")

print("\n" + "=" * 60)
print("\nConclusion:")
print("Python's isalnum() accepts Unicode alphanumeric characters,")
print("but troposphere only accepts ASCII [a-zA-Z0-9].")
print("This is the source of the test failures.")