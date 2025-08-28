#!/usr/bin/env python3
"""
Test alternate() function with negative lengths to see if this is intended behavior
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward.prettyprint as pp

print("Testing alternate() with edge cases:")
print()

# Test negative lengths
for length in [-5, -1, 0, 1, 5]:
    result = list(pp.alternate(length))
    print(f"alternate({length:2}) -> {result}")

print()
print("Checking the implementation...")

# Look at what half() does with negative numbers
for n in [-5, -1, 0, 1, 5]:
    print(f"half({n:2}) = {pp.half(n)}")

print()
print("Analysis:")
print("- alternate() silently accepts negative lengths and returns empty list")
print("- This could mask programming errors where negative length is passed accidentally")
print("- Most Python functions that take a length/size parameter raise ValueError for negative")

# Compare with standard library behavior
print("\nComparison with Python builtins:")
try:
    range(-5)
    print("range(-5) succeeded")
except Exception as e:
    print(f"range(-5) raised: {type(e).__name__}")

try:
    list(range(5, 0))  # Valid but empty
    print("range(5, 0) succeeded (empty range is valid)")
except Exception as e:
    print(f"range(5, 0) raised: {type(e).__name__}")