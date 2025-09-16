"""Minimal reproduction of title validation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.guardduty import Detector

# Test 1: Unicode superscript character
test_char = '¹'
print(f"Testing character: {test_char!r}")
print(f"Python isalnum(): {test_char.isalnum()}")

try:
    detector = Detector(test_char, Enable=True)
    print("Detector created successfully")
except ValueError as e:
    print(f"Detector creation failed: {e}")

# Test 2: Feminine ordinal indicator
test_char2 = 'ª'
print(f"\nTesting character: {test_char2!r}")
print(f"Python isalnum(): {test_char2.isalnum()}")

try:
    detector = Detector(test_char2, Enable=True)
    print("Detector created successfully")
except ValueError as e:
    print(f"Detector creation failed: {e}")

# Test 3: Regular alphanumeric
test_char3 = 'Test123'
print(f"\nTesting string: {test_char3!r}")
print(f"Python isalnum(): {test_char3.isalnum()}")

try:
    detector = Detector(test_char3, Enable=True)
    print("Detector created successfully")
except ValueError as e:
    print(f"Detector creation failed: {e}")

# Show the regex pattern
import re
valid_names = re.compile(r"^[a-zA-Z0-9]+$")
print(f"\nRegex pattern matches '¹': {bool(valid_names.match('¹'))}")
print(f"Regex pattern matches 'ª': {bool(valid_names.match('ª'))}")
print(f"Regex pattern matches 'Test123': {bool(valid_names.match('Test123'))}")

# This demonstrates the inconsistency between Python's isalnum() and the regex