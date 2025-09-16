"""Minimal reproduction of title validation bug in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.kms as kms

# Test 1: Unicode alphanumeric characters that Python's isalnum() accepts
# but the regex ^[a-zA-Z0-9]+$ doesn't
test_chars = ['²', 'ª', '¹', '³', 'º', 'µ']

for char in test_chars:
    print(f"Testing character: {char}")
    print(f"  Python isalnum(): {char.isalnum()}")
    
    try:
        # This should raise ValueError according to the regex validation
        # but passes the Python isalnum() check in test
        key = kms.Key(char)
        print(f"  Created Key with title '{char}' - should have failed!")
        # This is a bug - Unicode alphanumerics bypass validation
    except ValueError as e:
        print(f"  Correctly rejected: {e}")
    print()

# Test 2: Empty string handling
print("Testing empty string:")
try:
    # Empty string should be rejected but might not be
    key = kms.Key('')
    print("  Created Key with empty title - this is a bug!")
except ValueError as e:
    print(f"  Correctly rejected: {e}")

# Test 3: Demonstrate the inconsistency in test vs actual validation
print("\nDemonstrating test vs actual validation mismatch:")
title = "ª"  # Unicode superscript feminine ordinal indicator
print(f"Character: {title}")
print(f"Python isalnum() check (used in test): {title.isalnum()}")
print(f"Expected by test to fail: {title and all(c.isalnum() for c in title)}")

# The actual validation happens here
try:
    alias = kms.Alias(title, AliasName="alias/test", TargetKeyId="key-123")
    print(f"BUG: Created Alias with title '{title}' - validation failed to catch Unicode!")
except ValueError as e:
    print(f"Correctly caught by actual validation: {e}")