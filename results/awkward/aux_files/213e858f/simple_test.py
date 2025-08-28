#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
from hypothesis import given, strategies as st, settings

print("Testing basic type functionality...")

# Create a simple type
t1 = ak.types.NumpyType("int32")
print(f"Created type: {t1}")
print(f"String representation: {str(t1)}")

# Test round-trip
type_str = str(t1)
parsed = ak.types.from_datashape(type_str, highlevel=False)
print(f"Parsed type: {parsed}")
print(f"Are they equal? {t1.is_equal_to(parsed)}")

# Test UnionType order invariance
u1 = ak.types.UnionType([ak.types.NumpyType("int32"), ak.types.NumpyType("float64")])
u2 = ak.types.UnionType([ak.types.NumpyType("float64"), ak.types.NumpyType("int32")])
print(f"\nUnion 1: {u1}")
print(f"Union 2: {u2}")
print(f"Are they equal? {u1.is_equal_to(u2)}")

# Test RecordType field order
r1 = ak.types.RecordType([ak.types.NumpyType("int32"), ak.types.NumpyType("float64")], ["a", "b"])
r2 = ak.types.RecordType([ak.types.NumpyType("float64"), ak.types.NumpyType("int32")], ["b", "a"])
print(f"\nRecord 1: {r1}")
print(f"Record 2: {r2}")
print(f"Are they equal? {r1.is_equal_to(r2)}")

print("\nBasic tests complete!")