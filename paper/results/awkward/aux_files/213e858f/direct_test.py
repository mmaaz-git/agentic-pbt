import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
from hypothesis import given, strategies as st, settings, example
import traceback

# Test 1: from_datashape round-trip
print("=" * 60)
print("Testing Property 1: from_datashape round-trip")
print("=" * 60)

test_cases = [
    ak.types.NumpyType("int32"),
    ak.types.NumpyType("float64"),
    ak.types.ListType(ak.types.NumpyType("int32")),
    ak.types.RegularType(ak.types.NumpyType("float64"), 10),
    ak.types.OptionType(ak.types.NumpyType("int32")),
    ak.types.RecordType([ak.types.NumpyType("int32"), ak.types.NumpyType("float64")], None),  # Tuple
    ak.types.RecordType([ak.types.NumpyType("int32"), ak.types.NumpyType("float64")], ["x", "y"]),  # Record
    ak.types.UnionType([ak.types.NumpyType("int32"), ak.types.NumpyType("float64")]),
]

failures = []
for i, test_type in enumerate(test_cases, 1):
    try:
        type_str = str(test_type)
        parsed = ak.types.from_datashape(type_str, highlevel=False)
        if not test_type.is_equal_to(parsed):
            failures.append(f"Test case {i} FAILED: {test_type} -> '{type_str}' -> {parsed}")
            print(f"❌ Test case {i}: {test_type.__class__.__name__} - FAILED")
            print(f"   Original: {test_type}")
            print(f"   String:   '{type_str}'")
            print(f"   Parsed:   {parsed}")
        else:
            print(f"✓ Test case {i}: {test_type.__class__.__name__} - passed")
    except Exception as e:
        failures.append(f"Test case {i} ERROR: {test_type} raised {e}")
        print(f"❌ Test case {i}: {test_type.__class__.__name__} - ERROR")
        print(f"   Error: {e}")

# Test 2: UnionType equality is order-invariant
print("\n" + "=" * 60)
print("Testing Property 2: UnionType equality is order-invariant")
print("=" * 60)

u1 = ak.types.UnionType([ak.types.NumpyType("int32"), ak.types.NumpyType("float64")])
u2 = ak.types.UnionType([ak.types.NumpyType("float64"), ak.types.NumpyType("int32")])

if u1.is_equal_to(u2):
    print("✓ UnionType order invariance: PASSED")
else:
    print("❌ UnionType order invariance: FAILED")
    failures.append(f"UnionType order invariance failed: {u1} != {u2}")

# Test with 3 types
u3 = ak.types.UnionType([ak.types.NumpyType("int32"), ak.types.NumpyType("float64"), ak.types.NumpyType("bool")])
u4 = ak.types.UnionType([ak.types.NumpyType("bool"), ak.types.NumpyType("int32"), ak.types.NumpyType("float64")])

if u3.is_equal_to(u4):
    print("✓ UnionType order invariance (3 types): PASSED")
else:
    print("❌ UnionType order invariance (3 types): FAILED")
    failures.append(f"UnionType order invariance (3 types) failed: {u3} != {u4}")

# Test 3: RecordType equality for records is field-order independent
print("\n" + "=" * 60)
print("Testing Property 3: RecordType field-order independence")
print("=" * 60)

r1 = ak.types.RecordType([ak.types.NumpyType("int32"), ak.types.NumpyType("float64")], ["a", "b"])
r2 = ak.types.RecordType([ak.types.NumpyType("float64"), ak.types.NumpyType("int32")], ["b", "a"])

if r1.is_equal_to(r2):
    print("✓ RecordType field order independence: PASSED")
else:
    print("❌ RecordType field order independence: FAILED")
    print(f"   Record 1: {r1}")
    print(f"   Record 2: {r2}")
    failures.append(f"RecordType field order independence failed: {r1} != {r2}")

# Test 4: RecordType field_to_index and index_to_field are inverses
print("\n" + "=" * 60)
print("Testing Property 4: RecordType field/index conversion")
print("=" * 60)

# Test with named record
r = ak.types.RecordType([ak.types.NumpyType("int32"), ak.types.NumpyType("float64"), ak.types.NumpyType("bool")], 
                         ["x", "y", "z"])

inverse_ok = True
for i in range(3):
    field = r.index_to_field(i)
    recovered_index = r.field_to_index(field)
    if recovered_index != i:
        print(f"❌ Index {i} -> field '{field}' -> index {recovered_index} (expected {i})")
        failures.append(f"RecordType index/field inverse failed at index {i}")
        inverse_ok = False

for field in ["x", "y", "z"]:
    index = r.field_to_index(field)
    recovered_field = r.index_to_field(index)
    if recovered_field != field:
        print(f"❌ Field '{field}' -> index {index} -> field '{recovered_field}' (expected '{field}')")
        failures.append(f"RecordType field/index inverse failed at field '{field}'")
        inverse_ok = False

if inverse_ok:
    print("✓ RecordType field/index inverses: PASSED")

# Test with tuple
t = ak.types.RecordType([ak.types.NumpyType("int32"), ak.types.NumpyType("float64")], None)

tuple_ok = True
for i in range(2):
    field = t.index_to_field(i)
    recovered_index = t.field_to_index(field)
    if recovered_index != i:
        print(f"❌ Tuple index {i} -> field '{field}' -> index {recovered_index} (expected {i})")
        failures.append(f"RecordType tuple index/field inverse failed at index {i}")
        tuple_ok = False

if tuple_ok:
    print("✓ RecordType tuple field/index inverses: PASSED")

# Test 5: Type copy() creates equal objects
print("\n" + "=" * 60)
print("Testing Property 5: Type copy() creates equal objects")
print("=" * 60)

copy_test_cases = [
    ak.types.NumpyType("int32", parameters={"test": 123}),
    ak.types.ListType(ak.types.NumpyType("float64"), parameters={"array": "list"}),
    ak.types.RegularType(ak.types.NumpyType("int32"), 5, parameters={"regular": True}),
    ak.types.OptionType(ak.types.NumpyType("bool"), parameters={"nullable": True}),
    ak.types.RecordType([ak.types.NumpyType("int32")], ["field"], parameters={"record": "test"}),
    ak.types.UnionType([ak.types.NumpyType("int32"), ak.types.NumpyType("float64")], parameters={"union": 1}),
]

copy_ok = True
for test_type in copy_test_cases:
    copied = test_type.copy()
    if not test_type.is_equal_to(copied):
        print(f"❌ Copy failed for {test_type.__class__.__name__}: {test_type} != {copied}")
        failures.append(f"Copy failed for {test_type.__class__.__name__}")
        copy_ok = False
    if not test_type.is_equal_to(copied, all_parameters=True):
        print(f"❌ Copy failed (all_parameters) for {test_type.__class__.__name__}: {test_type} != {copied}")
        failures.append(f"Copy failed (all_parameters) for {test_type.__class__.__name__}")
        copy_ok = False

if copy_ok:
    print("✓ Type copy() equality: PASSED")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

if failures:
    print(f"Found {len(failures)} failure(s):")
    for failure in failures:
        print(f"  - {failure}")
else:
    print("✅ All tests passed!")