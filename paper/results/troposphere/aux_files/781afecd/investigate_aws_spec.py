#!/usr/bin/env python3
"""Investigate the intended behavior and documentation."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Check the actual regex pattern and error message
import re
from troposphere import valid_names

print("Troposphere validation details:")
print(f"Regex pattern: {valid_names.pattern}")
print(f"Error message in code: 'Name \"%s\" not alphanumeric'")

print("\nIssue Summary:")
print("-" * 60)
print("The error message claims the name is 'not alphanumeric', but:")
print("1. Python's isalnum() returns True for characters like 'ª', 'º', '²'")
print("2. The actual regex pattern [a-zA-Z0-9]+ only accepts ASCII alphanumerics")
print("3. This creates a misleading error message")

print("\nPossible fixes:")
print("1. Change error message to: 'Name \"%s\" must contain only ASCII letters and numbers'")
print("2. Or update regex to match Python's isalnum() behavior")
print("3. Or document clearly that only ASCII alphanumerics are allowed")

# Check if there's any Unicode category support
import unicodedata

test_chars = ['ª', 'a', '5', '²', 'µ', 'α', '中']
print("\nCharacter analysis:")
for char in test_chars:
    category = unicodedata.category(char)
    name = unicodedata.name(char, 'UNKNOWN')
    print(f"'{char}': category={category}, name={name}, isalnum={char.isalnum()}")