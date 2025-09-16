#!/usr/bin/env python3
"""Minimal reproduction of the title validation bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import re
import troposphere.elasticbeanstalk as eb

# Test case that reveals the bug
test_char = 'ª'  # Ordinal indicator character

print(f"Testing character: '{test_char}'")
print(f"Python isalnum(): {test_char.isalnum()}")

# The regex pattern used in troposphere
valid_names = re.compile(r"^[a-zA-Z0-9]+$")
print(f"Troposphere regex match: {bool(valid_names.match(test_char))}")

print("\nAttempting to create Application with this title...")
try:
    app = eb.Application(test_char)
    print("✓ Application created successfully")
except ValueError as e:
    print(f"✗ ValueError raised: {e}")

print("\n--- Additional problematic characters ---")
# Test more characters that Python considers alphanumeric
problematic_chars = ['ª', 'º', '²', '³', '¹', 'µ']

for char in problematic_chars:
    is_alnum = char.isalnum()
    regex_match = bool(valid_names.match(char))
    print(f"'{char}': isalnum={is_alnum}, regex_match={regex_match}, mismatch={is_alnum != regex_match}")
    
    if is_alnum != regex_match:
        try:
            app = eb.Application(char)
            print(f"  → Created successfully (but shouldn't according to docs)")
        except ValueError:
            print(f"  → Rejected (but Python says it's alphanumeric!)")