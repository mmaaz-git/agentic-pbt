#!/usr/bin/env python3
"""Direct testing for limits.limits bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from limits.limits import safe_string, RateLimitItemPerSecond
from limits import parse

print("Testing limits.limits for bugs...")
print("=" * 60)

# Bug 1: safe_string with invalid UTF-8
print("\n1. Testing safe_string with invalid UTF-8 bytes...")
try:
    invalid_utf8 = b'\xff\xfe\x00\x01'  # Invalid UTF-8 sequence
    result = safe_string(invalid_utf8)
    print(f"ERROR: safe_string succeeded with invalid UTF-8!")
    print(f"Result type: {type(result)}")
    print(f"Result repr: {repr(result)}")
except UnicodeDecodeError as e:
    print(f"BUG FOUND: safe_string crashes on invalid UTF-8!")
    print(f"Error: {e}")

# Bug 2: safe_string with more invalid bytes
print("\n2. Testing safe_string with another invalid UTF-8 sequence...")
try:
    invalid_utf8 = b'\x80\x81\x82\x83'  # Another invalid UTF-8 sequence
    result = safe_string(invalid_utf8)
    print(f"ERROR: safe_string succeeded with invalid UTF-8!")
    print(f"Result: {repr(result)}")
except UnicodeDecodeError as e:
    print(f"BUG FOUND: safe_string crashes on invalid UTF-8!")
    print(f"Error: {e}")

# Bug 3: safe_string with high bytes
print("\n3. Testing safe_string with high bytes...")
try:
    high_bytes = bytes([255, 254, 253, 252])
    result = safe_string(high_bytes)
    print(f"ERROR: safe_string succeeded with high bytes!")
    print(f"Result: {repr(result)}")
except UnicodeDecodeError as e:
    print(f"BUG FOUND: safe_string crashes on non-UTF-8 bytes!")
    print(f"Error: {e}")

# Bug 4: Parse with zero amount
print("\n4. Testing parse with zero amount...")
try:
    result = parse("0/second")
    print(f"Parsed successfully: {result}")
    print(f"Amount: {result.amount}")
    if result.amount == 0:
        print("ISSUE: Allows rate limit with amount=0 (might be intentional)")
except ValueError as e:
    print(f"Correctly rejected: {e}")

# Bug 5: Parse with negative amount
print("\n5. Testing parse with negative amount...")
try:
    result = parse("-5/second")
    print(f"Parsed successfully: {result}")
    print(f"Amount: {result.amount}")
    if result.amount < 0:
        print("ISSUE: Accepts negative amounts")
except ValueError as e:
    print(f"Correctly rejected: {e}")

print("\n" + "=" * 60)
print("Testing complete!")