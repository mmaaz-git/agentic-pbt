#!/usr/bin/env python3
"""Investigate which Unicode characters trigger the bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import re

# Examples of Unicode alphanumeric characters that Python considers alphanumeric
# but the troposphere regex rejects
test_chars = [
    '¹', '²', '³',  # Superscript numbers
    'α', 'β', 'γ',  # Greek letters
    'Ⅰ', 'Ⅱ', 'Ⅲ',  # Roman numerals
    '①', '②', '③',  # Circled numbers
    'À', 'É', 'Ñ',  # Accented letters
]

valid_names = re.compile(r"^[a-zA-Z0-9]+$")

print("Character | Python isalnum() | Troposphere regex")
print("-" * 50)
for char in test_chars:
    python_result = char.isalnum()
    regex_result = bool(valid_names.match(char))
    mismatch = "❌ MISMATCH" if python_result != regex_result else ""
    print(f"{char:^10} | {python_result:^16} | {regex_result:^16} {mismatch}")