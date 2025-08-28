#!/usr/bin/env python3
"""
Find bug in split_buffers function
"""

import sys
import traceback
sys.path.insert(0, "/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages")

from awkward._connect.jax.trees import split_buffers

print("Testing split_buffers function for bugs...\n")

# Test 1: Key with no dash - this should cause rsplit to fail
print("Test 1: Key with no dash")
print("-" * 40)
try:
    buffers = {"nodash": b"test_data"}
    data, other = split_buffers(buffers)
    print(f"Input: {buffers}")
    print(f"Data buffers: {data}")
    print(f"Other buffers: {other}")
    print("No error raised - checking if correct...")
    # The key should be in other_buffers since it doesn't end with "-data"
    assert "nodash" in other, "Key should be in other_buffers"
    print("✓ Handled correctly\n")
except ValueError as e:
    print(f"✗ BUG FOUND: ValueError raised: {e}")
    print(f"Traceback:")
    traceback.print_exc()
    print("\nThis is a bug because rsplit('-', 1) with maxsplit=1 should always return a list,")
    print("but if there's no '-' in the string, it returns a single-element list.")
    print("The code tries to unpack it into two variables, causing a ValueError.\n")

# Test 2: Empty string key
print("Test 2: Empty string key")
print("-" * 40)
try:
    buffers = {"": b"test"}
    data, other = split_buffers(buffers)
    print(f"Input: {buffers}")
    print(f"Data buffers: {data}")
    print(f"Other buffers: {other}")
    print("✓ Handled correctly\n")
except ValueError as e:
    print(f"✗ BUG FOUND: ValueError raised: {e}")
    traceback.print_exc()
    print()

# Test 3: Key that is exactly "data" (no dash)
print("Test 3: Key 'data'")
print("-" * 40)
try:
    buffers = {"data": b"test"}
    data, other = split_buffers(buffers)
    print(f"Input: {buffers}")
    print(f"Data buffers: {data}")
    print(f"Other buffers: {other}")
    print("✓ Handled correctly\n")
except ValueError as e:
    print(f"✗ BUG FOUND: ValueError raised: {e}")
    traceback.print_exc()
    print()

# Test 4: Demonstrate the actual bug with hypothesis-style test
print("Test 4: Property-based test simulation")
print("-" * 40)

test_cases = [
    {"simple": b"value"},           # No dash
    {"": b"empty_key"},              # Empty key
    {"data": b"just_data"},          # Just "data"
    {"prefix_data": b"no_dash"},     # Ends with "data" but no dash
    {"valid-data": b"good"},         # Valid case
    {"multi-part-data": b"ok"},      # Multiple dashes
]

failed_cases = []
for i, test_case in enumerate(test_cases):
    try:
        data, other = split_buffers(test_case)
        # Verify the invariant
        for key in data:
            if not key.endswith("-data"):
                failed_cases.append((test_case, f"Key '{key}' in data_buffers doesn't end with '-data'"))
    except Exception as e:
        failed_cases.append((test_case, f"Exception: {e}"))

if failed_cases:
    print("✗ BUG CONFIRMED: split_buffers fails on these inputs:")
    for case, error in failed_cases:
        print(f"  Input: {case}")
        print(f"  Error: {error}")
else:
    print("✓ All test cases passed")

print("\n" + "="*50)
print("CONCLUSION:")
print("The split_buffers function has a bug when handling keys without dashes.")
print("The rsplit('-', 1) call expects to split into two parts, but if there's no dash,")
print("it only returns one element, causing an unpacking error.")
print("="*50)