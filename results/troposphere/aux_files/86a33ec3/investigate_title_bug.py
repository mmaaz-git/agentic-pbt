"""Investigate the title validation bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.frauddetector as fd
import re

# Test the regex pattern used in troposphere
valid_names = re.compile(r"^[a-zA-Z0-9]+$")

# Test cases
test_cases = [
    "ValidName123",  # Should pass
    "¹",  # Superscript 1 - should fail but seems to pass
    "test_name",  # Underscore - should fail
    "test-name",  # Hyphen - should fail  
    "test name",  # Space - should fail
    "123test",  # Starting with number - should pass
    "²³⁴",  # More superscripts
    "Test",  # Simple valid name
    "",  # Empty string - should fail
    "αβγ",  # Greek letters - should fail
]

print("Testing title validation:")
print("-" * 50)

for title in test_cases:
    print(f"\nTesting title: {repr(title)}")
    print(f"  Regex match: {bool(valid_names.match(title))}")
    print(f"  isalnum(): {title.isalnum() if title else False}")
    
    try:
        entity = fd.EntityType(title, Name="test")
        print(f"  ✓ Created successfully")
    except ValueError as e:
        print(f"  ✗ Failed: {e}")

# Now let's check what specific character '¹' is
print("\n" + "=" * 50)
print("Character analysis for '¹':")
print(f"  Unicode name: {ord('¹')}")
print(f"  Is digit: {('¹').isdigit()}")
print(f"  Is numeric: {('¹').isnumeric()}")
print(f"  Is alphanumeric: {('¹').isalnum()}")
print(f"  Is decimal: {('¹').isdecimal()}")

# Test the actual regex
print("\n" + "=" * 50)
print("Regex testing:")
import string
print(f"Regex pattern: {valid_names.pattern}")
print(f"Does '¹' match [a-zA-Z0-9]+? {valid_names.match('¹')}")
print(f"Does 'A' match? {valid_names.match('A')}")
print(f"Does '1' match? {valid_names.match('1')}")