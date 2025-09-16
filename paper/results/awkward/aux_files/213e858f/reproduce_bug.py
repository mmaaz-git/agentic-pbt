#!/usr/bin/env python3
"""
Minimal reproduction script to test potential bugs in awkward.types.

This script demonstrates issues found through property-based testing analysis.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak

def test_recordtype_field_order_bug():
    """
    Test whether RecordType equality is truly field-order independent.
    
    According to the code (recordtype.py lines 204-211), records with same fields 
    but different orders should be equal.
    """
    print("Testing RecordType field-order independence...")
    
    # Create two records with same fields and types but different order
    r1 = ak.types.RecordType(
        [ak.types.NumpyType("int32"), ak.types.NumpyType("float64")], 
        ["a", "b"]
    )
    
    r2 = ak.types.RecordType(
        [ak.types.NumpyType("float64"), ak.types.NumpyType("int32")], 
        ["b", "a"]
    )
    
    print(f"Record 1: {r1}")
    print(f"Record 2: {r2}")
    
    # According to the implementation, these should be equal
    result = r1.is_equal_to(r2)
    print(f"Are they equal? {result}")
    
    if result:
        print("✓ Field-order independence works as expected")
    else:
        print("❌ BUG: Field-order independence not working!")
        print("\nDetailed analysis:")
        print(f"  r1 fields: {r1.fields}")
        print(f"  r2 fields: {r2.fields}")
        print(f"  r1 contents: {r1.contents}")
        print(f"  r2 contents: {r2.contents}")
        
        # Manually check what should happen
        print("\nManual check:")
        print(f"  Fields sets equal? {set(r1.fields) == set(r2.fields)}")
        
        # Check each field mapping
        for field in r1.fields:
            r1_type = r1.content(field)
            r2_type = r2.content(field)
            print(f"  Field '{field}':")
            print(f"    r1 type: {r1_type}")
            print(f"    r2 type: {r2_type}")
            print(f"    Equal? {r1_type.is_equal_to(r2_type)}")
    
    return result


def test_from_datashape_round_trip():
    """
    Test whether from_datashape(str(type)) == type holds.
    
    This is explicitly documented in the from_datashape docstring.
    """
    print("\nTesting from_datashape round-trip property...")
    
    test_cases = [
        # Simple types
        ak.types.NumpyType("int32"),
        ak.types.NumpyType("float64"),
        
        # Nested types
        ak.types.ListType(ak.types.NumpyType("int32")),
        ak.types.OptionType(ak.types.NumpyType("float64")),
        ak.types.RegularType(ak.types.NumpyType("int32"), 10),
        
        # Complex types
        ak.types.RecordType([ak.types.NumpyType("int32")], ["x"]),
        ak.types.UnionType([ak.types.NumpyType("int32"), ak.types.NumpyType("float64")]),
        
        # Nested complex types
        ak.types.ListType(ak.types.OptionType(ak.types.NumpyType("int32"))),
        ak.types.RecordType(
            [ak.types.ListType(ak.types.NumpyType("int32")), ak.types.NumpyType("float64")],
            ["list_field", "float_field"]
        ),
    ]
    
    failures = []
    for type_obj in test_cases:
        type_str = str(type_obj)
        try:
            parsed = ak.types.from_datashape(type_str, highlevel=False)
            if not type_obj.is_equal_to(parsed):
                failures.append((type_obj, type_str, parsed))
                print(f"❌ Round-trip failed for {type_obj.__class__.__name__}")
                print(f"   Original: {type_obj}")
                print(f"   String:   '{type_str}'")
                print(f"   Parsed:   {parsed}")
        except Exception as e:
            failures.append((type_obj, type_str, str(e)))
            print(f"❌ Parsing failed for {type_obj.__class__.__name__}")
            print(f"   Original: {type_obj}")
            print(f"   String:   '{type_str}'")
            print(f"   Error:    {e}")
    
    if not failures:
        print("✓ All round-trip tests passed")
    else:
        print(f"\n{len(failures)} round-trip failures found!")
    
    return len(failures) == 0


def test_union_type_order_invariance():
    """
    Test whether UnionType equality is order-invariant.
    
    According to uniontype.py lines 107-113, it uses permutations to check equality.
    """
    print("\nTesting UnionType order invariance...")
    
    # Test with 2 types
    u1 = ak.types.UnionType([ak.types.NumpyType("int32"), ak.types.NumpyType("float64")])
    u2 = ak.types.UnionType([ak.types.NumpyType("float64"), ak.types.NumpyType("int32")])
    
    result1 = u1.is_equal_to(u2)
    print(f"2-type union: {u1} == {u2}? {result1}")
    
    # Test with 3 types
    u3 = ak.types.UnionType([
        ak.types.NumpyType("int32"), 
        ak.types.NumpyType("float64"),
        ak.types.NumpyType("bool")
    ])
    u4 = ak.types.UnionType([
        ak.types.NumpyType("bool"),
        ak.types.NumpyType("int32"), 
        ak.types.NumpyType("float64")
    ])
    
    result2 = u3.is_equal_to(u4)
    print(f"3-type union: {u3} == {u4}? {result2}")
    
    if result1 and result2:
        print("✓ UnionType order invariance works as expected")
    else:
        print("❌ BUG: UnionType order invariance not working!")
    
    return result1 and result2


def main():
    """Run all tests and report findings."""
    print("=" * 60)
    print("AWKWARD TYPES BUG HUNTING")
    print("=" * 60)
    
    bugs_found = []
    
    # Test 1: RecordType field order
    if not test_recordtype_field_order_bug():
        bugs_found.append("RecordType field-order independence")
    
    # Test 2: from_datashape round-trip
    if not test_from_datashape_round_trip():
        bugs_found.append("from_datashape round-trip")
    
    # Test 3: UnionType order invariance
    if not test_union_type_order_invariance():
        bugs_found.append("UnionType order invariance")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if bugs_found:
        print(f"❌ Found {len(bugs_found)} potential bug(s):")
        for bug in bugs_found:
            print(f"  - {bug}")
        return 1
    else:
        print("✅ No bugs found in the tested properties.")
        return 0


if __name__ == "__main__":
    sys.exit(main())