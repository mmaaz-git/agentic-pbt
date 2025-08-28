#!/usr/bin/env python3
"""Test for potential bug in strings_differ with empty strings."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.util import strings_differ
from hmac import compare_digest

print("Testing strings_differ implementation...")
print("=" * 60)

# The implementation from pyramid/util.py:
# def strings_differ(string1, string2):
#     len_eq = len(string1) == len(string2)
#     if len_eq:
#         invalid_bits = 0
#         left = string1
#     else:
#         invalid_bits = 1
#         left = string2    # <-- Potential issue here!
#     right = string2
#     
#     invalid_bits += not compare_digest(left, right)
#     return invalid_bits != 0

print("\nAnalyzing the strings_differ logic:")
print("When strings have different lengths:")
print("  - invalid_bits = 1")
print("  - left = string2")
print("  - right = string2")
print("  - compare_digest(string2, string2) will always return True")
print("  - invalid_bits += not True → invalid_bits += 0")
print("  - Result: invalid_bits = 1 (correct - strings differ)")

print("\nBut this reveals timing information!")
print("When len(s1) != len(s2), we compare string2 with itself.")
print("This takes time proportional to len(string2), not constant time!")

print("\nDemonstrating the issue:")

def analyze_strings_differ(s1, s2):
    """Analyze what strings_differ does internally."""
    print(f"\n  strings_differ({repr(s1)}, {repr(s2)})")
    
    len_eq = len(s1) == len(s2)
    print(f"    len_eq = {len_eq}")
    
    if len_eq:
        invalid_bits = 0
        left = s1
        print(f"    Same length: comparing s1 with s2")
    else:
        invalid_bits = 1
        left = s2
        print(f"    Different length: comparing s2 with s2 (!!!)")
    
    right = s2
    # compare_digest returns True if equal
    comparison = (left == right)  # Simulating compare_digest
    invalid_bits += not comparison
    
    print(f"    invalid_bits = {invalid_bits}")
    print(f"    Result: {invalid_bits != 0}")
    
    return invalid_bits != 0

# Test cases showing the issue
test_cases = [
    (b"short", b"much_longer_string"),
    (b"much_longer_string", b"short"),
    (b"", b"non_empty"),
    (b"same", b"same"),
    (b"diff", b"erent"),
]

print("\nTest cases:")
for s1, s2 in test_cases:
    result = analyze_strings_differ(s1, s2)
    # Verify against actual implementation
    from pyramid.util import strings_differ
    actual = strings_differ(s1, s2)
    if result != actual:
        print(f"    ERROR: Expected {result}, got {actual}")

print("\n" + "=" * 60)
print("ISSUE FOUND: strings_differ leaks timing information about string length!")
print("When lengths differ, it compares string2 with itself, taking time")
print("proportional to len(string2). This partially defeats the constant-time")
print("comparison goal, as an attacker could determine string length differences.")

print("\nHowever, this might be acceptable since:")
print("1. Length is less sensitive than content")
print("2. Full constant-time comparison with different lengths is complex")
print("3. The function still hides WHERE strings differ")