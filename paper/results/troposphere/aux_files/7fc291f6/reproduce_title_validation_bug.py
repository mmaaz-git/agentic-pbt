#!/usr/bin/env python3
"""
Minimal reproduction of the title validation bug in troposphere.iotanalytics
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import iotanalytics

# Test various Unicode characters that Python considers alphanumeric
test_cases = [
    '¹',  # Superscript 1 - isalnum() returns True
    '²',  # Superscript 2
    '³',  # Superscript 3
    'α',  # Greek letter alpha
    'β',  # Greek letter beta
    '一',  # Chinese character for "one"
    '二',  # Chinese character for "two"
    'א',  # Hebrew letter aleph
    'ب',  # Arabic letter baa
    'ñ',  # Spanish n with tilde
    'ü',  # German u with umlaut
    'é',  # French e with acute
    '①',  # Circled digit one
    'Ⅰ',  # Roman numeral one
    '𝟏',  # Mathematical bold digit one
]

print("Testing troposphere title validation vs Python's isalnum():\n")

for char in test_cases:
    print(f"Character: '{char}'")
    print(f"  Python isalnum(): {char.isalnum()}")
    
    try:
        # Try to create a Channel with this character as title
        channel = iotanalytics.Channel(char)
        print(f"  Troposphere: ACCEPTED")
    except ValueError as e:
        print(f"  Troposphere: REJECTED ({e})")
    
    print()

# Demonstrate the inconsistency
print("\n=== BUG DEMONSTRATION ===")
print("The character '¹' (superscript 1):")
print(f"  - Python's isalnum() returns: {'¹'.isalnum()}")
print("  - But troposphere rejects it as 'not alphanumeric'")
print("\nThis is inconsistent because troposphere claims to validate 'alphanumeric'")
print("characters but uses a regex that only matches ASCII [a-zA-Z0-9]")
print("instead of properly checking for Unicode alphanumeric characters.")