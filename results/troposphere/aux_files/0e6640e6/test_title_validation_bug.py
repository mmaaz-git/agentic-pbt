#!/usr/bin/env python3
"""Focused test for title validation bug in troposphere."""

import sys
import re

# Add the virtual environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.opensearchserverless as oss

# Test various Unicode characters that Python considers alphanumeric
test_cases = [
    '¹',  # Superscript 1
    '²',  # Superscript 2
    '³',  # Superscript 3
    '₁',  # Subscript 1
    '₂',  # Subscript 2
    'α',  # Greek alpha
    'β',  # Greek beta
    'Ω',  # Greek omega
    '一',  # Chinese character for "one"
    '二',  # Chinese character for "two"
    'ñ',  # Spanish n with tilde
    'ä',  # German a with umlaut
    'é',  # French e with accent
    'א',  # Hebrew aleph
    'ا',  # Arabic alif
    '१',  # Devanagari digit 1
    '२',  # Devanagari digit 2
]

# The regex used by troposphere
valid_names = re.compile(r"^[a-zA-Z0-9]+$")

print("Testing discrepancy between Python's isalnum() and troposphere's validation:")
print("-" * 70)

for char in test_cases:
    python_isalnum = char.isalnum()
    troposphere_accepts = bool(valid_names.match(char))
    
    if python_isalnum != troposphere_accepts:
        print(f"Character: '{char}'")
        print(f"  Python isalnum(): {python_isalnum}")
        print(f"  Troposphere accepts: {troposphere_accepts}")
        print(f"  DISCREPANCY FOUND!")
        
        # Try to create a resource with this title
        try:
            ap = oss.AccessPolicy(
                title=char,
                Name="test",
                Policy="{}",
                Type="data"
            )
            print(f"  Resource creation: SUCCESS (title accepted)")
        except ValueError as e:
            print(f"  Resource creation: FAILED ({e})")
        print()

print("-" * 70)
print("\nConclusion:")
print("There is a semantic inconsistency between Python's isalnum() method and")
print("troposphere's title validation. Python's isalnum() accepts Unicode")
print("alphanumeric characters, while troposphere only accepts ASCII [a-zA-Z0-9].")
print("\nThis could lead to confusion for users who might expect Unicode support")
print("based on Python's standard library behavior.")