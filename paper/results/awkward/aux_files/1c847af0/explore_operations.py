#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import inspect
import awkward as ak

# Check main awkward module for functions
functions = []
for name in dir(ak):
    if not name.startswith('_'):
        obj = getattr(ak, name)
        if callable(obj) and not inspect.isclass(obj):
            functions.append(name)

print("Functions in main awkward module (that may have interesting properties):")
print("=" * 60)

# Group by potential property patterns
roundtrip_candidates = []
invariant_candidates = []
other_functions = []

for func_name in sorted(functions):
    if any(x in func_name for x in ['from_', 'to_']):
        roundtrip_candidates.append(func_name)
    elif any(x in func_name for x in ['sort', 'flatten', 'mask', 'drop', 'zip', 'unzip', 'concatenate']):
        invariant_candidates.append(func_name)
    else:
        other_functions.append(func_name)

print("\nPotential round-trip properties:")
for name in roundtrip_candidates[:20]:
    print(f"  - {name}")

print("\nPotential invariant properties:")
for name in invariant_candidates[:20]:
    print(f"  - {name}")

print("\nOther operations (first 30):")
for name in other_functions[:30]:
    print(f"  - {name}")

# Let's specifically look at Array class methods
print("\n\nArray class key operations:")
print("=" * 60)
array_cls = ak.Array

# Let's explore some specific functions
print("\nExploring specific functions for properties:")
print("-" * 60)

# Test if we can create arrays
print("\nTesting Array creation:")
test_array = ak.Array([1, 2, 3])
print(f"  Simple array: {test_array}")
print(f"  Type: {test_array.type}")

# Check nested arrays
nested = ak.Array([[1, 2], [], [3, 4, 5]])
print(f"  Nested array: {nested}")
print(f"  Type: {nested.type}")

# Check record arrays
records = ak.Array([{"x": 1, "y": 2}, {"x": 3, "y": 4}])
print(f"  Record array: {records}")
print(f"  Type: {records.type}")