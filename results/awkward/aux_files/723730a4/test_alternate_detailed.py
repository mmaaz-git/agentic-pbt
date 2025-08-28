#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward.prettyprint as pp

# Let's trace through the alternate function for small inputs
print("=== Testing alternate() function behavior ===\n")

for length in range(1, 8):
    print(f"length={length}, half={pp.half(length)}")
    result = list(pp.alternate(length))
    indices = [idx for _, idx in result]
    directions = [direction for direction, _ in result]
    print(f"  Result: {result}")
    print(f"  Indices order: {indices}")
    print(f"  All indices present: {sorted(indices) == list(range(length))}")
    print()

# Test edge case with length=0
print("Edge case: length=0")
result = list(pp.alternate(0))
print(f"  Result: {result}")
print(f"  Length: {len(result)}")
print()

# Let's understand the pattern better
print("\n=== Understanding the alternation pattern ===")
for length in [10, 11]:
    print(f"\nlength={length}, half={pp.half(length)}")
    for i, (direction, index) in enumerate(pp.alternate(length)):
        direction_str = "forward" if direction else "backward"
        print(f"  Step {i}: {direction_str:8} -> index {index}")