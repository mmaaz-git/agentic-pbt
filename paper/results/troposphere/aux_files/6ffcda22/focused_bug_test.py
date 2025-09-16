#!/usr/bin/env python
"""Focused bug testing for troposphere.finspace"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.finspace as finspace
import re

print("=== Focused Bug Testing ===\n")

# The regex from the source code
valid_names = re.compile(r"^[a-zA-Z0-9]+$")

# Test Case 1: Numeric-only titles (should be valid according to regex)
print("Test: Numeric-only titles")
numeric_titles = ["123", "0", "999999"]
for title in numeric_titles:
    try:
        env = finspace.Environment(title, Name="TestEnv") 
        if valid_names.match(title):
            print(f"  ✓ '{title}' correctly accepted")
        else:
            print(f"  BUG: '{title}' accepted but doesn't match regex")
    except ValueError as e:
        if valid_names.match(title):
            print(f"  BUG: '{title}' incorrectly rejected (matches regex)")
        else:
            print(f"  ✓ '{title}' correctly rejected")

# Test Case 2: Empty string (critical edge case)
print("\nTest: Empty string title")
try:
    env = finspace.Environment("", Name="TestEnv")
    if valid_names.match(""):
        print("  ✓ Empty string correctly accepted (matches regex)")
    else:
        print("  BUG: Empty string accepted but doesn't match regex!")
        print("  This is a validation bypass bug!")
except ValueError as e:
    if not valid_names.match(""):
        print(f"  ✓ Empty string correctly rejected")
    else:
        print(f"  BUG: Empty string incorrectly rejected")

# Test Case 3: Whitespace titles
print("\nTest: Whitespace-only titles")
whitespace_titles = [" ", "  ", "\t", "\n"]
for title in whitespace_titles:
    try:
        env = finspace.Environment(title, Name="TestEnv")
        print(f"  BUG: Whitespace title {repr(title)} accepted!")
    except ValueError:
        print(f"  ✓ Whitespace title {repr(title)} correctly rejected")

# Test Case 4: Mixed valid/invalid characters
print("\nTest: Mixed character titles")
mixed_titles = [
    "Test123",     # Should be valid
    "test",        # Should be valid
    "TEST",        # Should be valid
    "Test-123",    # Should be invalid (hyphen)
    "Test_123",    # Should be invalid (underscore)
    "Test.123",    # Should be invalid (dot)
]

for title in mixed_titles:
    expected_valid = valid_names.match(title) is not None
    try:
        env = finspace.Environment(title, Name="TestEnv")
        if expected_valid:
            print(f"  ✓ '{title}' correctly accepted")
        else:
            print(f"  BUG: '{title}' accepted but should be rejected (contains invalid chars)")
    except ValueError:
        if not expected_valid:
            print(f"  ✓ '{title}' correctly rejected")
        else:
            print(f"  BUG: '{title}' rejected but should be accepted")

# Test Case 5: Boundary length titles
print("\nTest: Title length boundaries")
# CloudFormation limit is 255 characters for resource names
long_valid = "A" * 255
very_long = "A" * 256

try:
    env = finspace.Environment(long_valid, Name="TestEnv")
    print(f"  ✓ 255-character title accepted")
except ValueError as e:
    print(f"  Issue: 255-character title rejected: {e}")

try:
    env = finspace.Environment(very_long, Name="TestEnv")
    print(f"  ✓ 256-character title accepted (no length validation)")
except ValueError as e:
    print(f"  ✓ 256-character title rejected: {e}")

# Test Case 6: Property validation with None
print("\nTest: None as title (important edge case)")
try:
    env = finspace.Environment(None, Name="TestEnv")
    print(f"  Environment created with title: {repr(env.title)}")
    
    # Try to use it
    try:
        d = env.to_dict()
        print(f"  BUG: None title passes to_dict validation!")
        print(f"  Result has Type: {d.get('Type')}")
    except Exception as e:
        print(f"  to_dict fails with: {e}")
        
except (ValueError, TypeError, AttributeError) as e:
    print(f"  ✓ None title causes error: {type(e).__name__}: {e}")

# Test Case 7: Special regex characters that might cause issues
print("\nTest: Regex special characters")
regex_chars = ["^", "$", ".", "*", "+", "?", "[", "]", "{", "}", "(", ")", "|", "\\"]
for char in regex_chars:
    title = f"Test{char}Name"
    try:
        env = finspace.Environment(title, Name="TestEnv")
        print(f"  BUG: Title with '{char}' accepted: {repr(title)}")
    except ValueError:
        print(f"  ✓ Title with '{char}' rejected: {repr(title)}")

print("\n=== Testing Complete ===")
print("\nKey findings to investigate:")
print("1. Check if empty string bypasses validation")
print("2. Check if None is handled properly") 
print("3. Verify numeric-only titles work as expected")
print("4. Confirm special characters are properly rejected")