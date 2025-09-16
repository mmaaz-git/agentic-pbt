#!/usr/bin/env python3
"""Direct inline test of awkward.types properties."""

import sys
import os

# Set up the path
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

# Change to the working directory
os.chdir('/root/hypothesis-llm/worker_/6')

# Import awkward
import awkward as ak

print("Testing awkward.types properties directly...")
print("-" * 60)

# Test 1: Basic from_datashape round-trip
print("\n1. Testing from_datashape round-trip:")
failures = []

# Simple test case
t = ak.types.NumpyType("int32")
s = str(t)
print(f"   Original type: {t}")
print(f"   String repr:   '{s}'")

try:
    parsed = ak.types.from_datashape(s, highlevel=False)
    print(f"   Parsed back:   {parsed}")
    if t.is_equal_to(parsed):
        print("   ✓ Round-trip successful")
    else:
        print("   ❌ Round-trip FAILED - types not equal!")
        failures.append(("Round-trip", t, s, parsed))
except Exception as e:
    print(f"   ❌ Parsing failed: {e}")
    failures.append(("Parsing", t, s, str(e)))

# Test complex nested type
print("\n   Testing nested type:")
nested = ak.types.ListType(ak.types.OptionType(ak.types.NumpyType("float64")))
nested_str = str(nested)
print(f"   Original: {nested}")
print(f"   String:   '{nested_str}'")

try:
    parsed_nested = ak.types.from_datashape(nested_str, highlevel=False)
    print(f"   Parsed:   {parsed_nested}")
    if nested.is_equal_to(parsed_nested):
        print("   ✓ Nested round-trip successful")
    else:
        print("   ❌ Nested round-trip FAILED!")
        failures.append(("Nested round-trip", nested, nested_str, parsed_nested))
except Exception as e:
    print(f"   ❌ Parsing failed: {e}")
    failures.append(("Nested parsing", nested, nested_str, str(e)))

# Test 2: UnionType order invariance
print("\n2. Testing UnionType order invariance:")
u1 = ak.types.UnionType([ak.types.NumpyType("int32"), ak.types.NumpyType("float64")])
u2 = ak.types.UnionType([ak.types.NumpyType("float64"), ak.types.NumpyType("int32")])

print(f"   Union 1: {u1}")
print(f"   Union 2: {u2}")

if u1.is_equal_to(u2):
    print("   ✓ Unions are equal (order-invariant)")
else:
    print("   ❌ Unions are NOT equal - BUG FOUND!")
    failures.append(("UnionType order", u1, u2, "Not equal"))

# Test 3: RecordType field order
print("\n3. Testing RecordType field-order independence:")
r1 = ak.types.RecordType([ak.types.NumpyType("int32"), ak.types.NumpyType("float64")], ["a", "b"])
r2 = ak.types.RecordType([ak.types.NumpyType("float64"), ak.types.NumpyType("int32")], ["b", "a"])

print(f"   Record 1: {r1}")
print(f"   Record 2: {r2}")

if r1.is_equal_to(r2):
    print("   ✓ Records are equal (field-order independent)")
else:
    print("   ❌ Records are NOT equal - BUG FOUND!")
    failures.append(("RecordType field order", r1, r2, "Not equal"))

# Test 4: RecordType field/index conversion
print("\n4. Testing RecordType field/index conversion:")
rec = ak.types.RecordType([ak.types.NumpyType("int32"), ak.types.NumpyType("float64")], ["x", "y"])

for i in range(2):
    field = rec.index_to_field(i)
    back = rec.field_to_index(field)
    if back == i:
        print(f"   ✓ Index {i} -> field '{field}' -> index {back}")
    else:
        print(f"   ❌ Index {i} -> field '{field}' -> index {back} (expected {i})")
        failures.append(("Field/index conversion", i, field, back))

# Test 5: Type copy
print("\n5. Testing Type copy equality:")
original = ak.types.ListType(ak.types.NumpyType("int32"), parameters={"test": 123})
copied = original.copy()

print(f"   Original: {original}")
print(f"   Copy:     {copied}")

if original.is_equal_to(copied):
    print("   ✓ Copy is equal to original")
else:
    print("   ❌ Copy is NOT equal - BUG FOUND!")
    failures.append(("Type copy", original, copied, "Not equal"))

# Summary
print("\n" + "=" * 60)
print("RESULTS SUMMARY")
print("=" * 60)

if failures:
    print(f"\n❌ Found {len(failures)} failure(s):\n")
    for i, (test, *details) in enumerate(failures, 1):
        print(f"{i}. {test}:")
        for detail in details:
            print(f"   {detail}")
    print("\nPotential bugs detected!")
else:
    print("\n✅ All tests passed! No bugs found.")

# Return status
sys.exit(0 if not failures else 1)