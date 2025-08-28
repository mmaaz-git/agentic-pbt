#!/usr/bin/env python3
"""
Analyze the split_buffers function for potential bugs
"""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages")

# Let's trace through the split_buffers logic
def split_buffers(buffers: dict) -> tuple[dict, dict]:
    """Original implementation from awkward._connect.jax.trees"""
    data_buffers, other_buffers = {}, {}
    for key, buf in buffers.items():
        _, attr = key.rsplit("-", 1)  # BUG POTENTIAL: What if there's no "-" in key?
        if attr == "data":
            data_buffers[key] = buf
        else:
            other_buffers[key] = buf
    return data_buffers, other_buffers

# Test case 1: Key with no dash
print("Testing key with no dash...")
try:
    result = split_buffers({"nodash": b"test"})
    print(f"Result: {result}")
except ValueError as e:
    print(f"BUG FOUND: ValueError when key has no dash: {e}")

# Test case 2: Empty key
print("\nTesting empty key...")
try:
    result = split_buffers({"": b"test"})
    print(f"Result: {result}")
except ValueError as e:
    print(f"BUG FOUND: ValueError with empty key: {e}")

# Test case 3: Key that is just "data"
print("\nTesting key 'data'...")
try:
    result = split_buffers({"data": b"test"})
    print(f"Result: {result}")
except ValueError as e:
    print(f"BUG FOUND: ValueError with key 'data': {e}")

# Test case 4: Multiple dashes
print("\nTesting key with multiple dashes...")
try:
    data, other = split_buffers({"a-b-c-data": b"test", "x-y-z": b"test2"})
    print(f"'a-b-c-data' in data: {'a-b-c-data' in data}")
    print(f"'x-y-z' in other: {'x-y-z' in other}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*50)
print("ANALYSIS COMPLETE")