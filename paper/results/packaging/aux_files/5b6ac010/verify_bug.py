import re
import packaging.utils

# Test the actual behavior
print("Testing is_normalized_name with consecutive dashes:")
test_cases = [
    ('a-b', True),      # Single dash - should pass
    ('a--b', False),    # Double dash - should fail
    ('a---b', False),   # Triple dash - should fail
    ('0--0', False),    # Double dash - should fail
    ('foo--bar', False), # Double dash - should fail
]

print("\nExpected vs Actual:")
for name, expected in test_cases:
    actual = packaging.utils.is_normalized_name(name)
    status = "✓" if actual == expected else "✗ BUG"
    print(f"  {name:10} Expected: {expected:5}  Actual: {actual:5}  {status}")

# The issue appears to be with the regex pattern
print("\n\nThe regex pattern: ^([a-z0-9]|[a-z0-9]([a-z0-9-](?!--))*[a-z0-9])$")
print("\nThe negative lookahead (?!--) is checking if a character is NOT followed by '--'")
print("But for '0--0', when matching the first dash:")
print("  - The first '-' is followed by '-0' (not '--'), so it passes the lookahead")
print("  - The second '-' is followed by '0' (not '--'), so it also passes")
print("\nThis allows consecutive dashes when the pattern clearly shouldn't!")

# Demonstrate the specific issue
print("\n\nDetailed trace for '0--0':")
pattern = r'^([a-z0-9]|[a-z0-9]([a-z0-9-](?!--))*[a-z0-9])$'
text = '0--0'
print(f"Text: {text!r}")
print(f"Pattern: {pattern}")

# This is the actual bug: the regex accepts strings with consecutive dashes
# when they're followed by an alphanumeric character
print("\nThe regex incorrectly accepts:")
incorrect_accepts = ['0--0', 'a--b', '1--2', 'x--y']
for test in incorrect_accepts:
    result = packaging.utils.is_normalized_name(test)
    print(f"  {test!r}: {result} (should be False)")