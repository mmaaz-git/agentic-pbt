#!/usr/bin/env python3
"""
Minimal reproduction of the bug in awkward._connect.jax.trees.split_buffers
"""

# The bug: split_buffers crashes when a buffer key doesn't contain a dash

def split_buffers_original(buffers: dict) -> tuple[dict, dict]:
    """Original implementation from awkward._connect.jax.trees"""
    data_buffers, other_buffers = {}, {}
    for key, buf in buffers.items():
        _, attr = key.rsplit("-", 1)  # BUG: Assumes key always has a dash
        if attr == "data":
            data_buffers[key] = buf
        else:
            other_buffers[key] = buf
    return data_buffers, other_buffers

# Reproduce the bug
try:
    # This will crash with ValueError: not enough values to unpack
    result = split_buffers_original({"nodash": b"test"})
    print(f"Result: {result}")
except ValueError as e:
    print(f"BUG REPRODUCED: {e}")
    print("\nThe issue is that rsplit('-', 1) returns a single-element list")
    print("when the string doesn't contain a dash, but the code tries to")
    print("unpack it into two variables (_, attr).")

# Show what rsplit actually returns
print("\nDemonstration:")
print(f"'has-dash'.rsplit('-', 1) = {'has-dash'.rsplit('-', 1)}")
print(f"'nodash'.rsplit('-', 1) = {'nodash'.rsplit('-', 1)}")
print("\nThe unpacking _, attr = 'nodash'.rsplit('-', 1) fails!")