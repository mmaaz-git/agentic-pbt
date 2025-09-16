#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import copy
import numpy as np
import awkward as ak
from hypothesis import given, strategies as st, assume, settings
import math


# More complex property tests looking for bugs

@st.composite  
def complex_record_strategy(draw):
    """Generate records with more complex data types."""
    length = draw(st.integers(min_value=1, max_value=20))
    n_fields = draw(st.integers(min_value=1, max_value=5))
    
    contents = []
    for _ in range(n_fields):
        # Mix different array types
        array_type = draw(st.sampled_from(["int", "float", "bool", "complex"]))
        
        if array_type == "int":
            data = np.array(draw(st.lists(
                st.integers(min_value=-2**31, max_value=2**31-1),
                min_size=length, max_size=length
            )), dtype=np.int32)
        elif array_type == "float":
            data = np.array(draw(st.lists(
                st.floats(allow_nan=True, allow_infinity=True),
                min_size=length, max_size=length
            )), dtype=np.float64)
        elif array_type == "bool":
            data = np.array(draw(st.lists(
                st.booleans(),
                min_size=length, max_size=length
            )), dtype=bool)
        else:  # complex
            real_parts = draw(st.lists(
                st.floats(min_value=-100, max_value=100, allow_nan=False),
                min_size=length, max_size=length
            ))
            imag_parts = draw(st.lists(
                st.floats(min_value=-100, max_value=100, allow_nan=False),
                min_size=length, max_size=length
            ))
            data = np.array([complex(r, i) for r, i in zip(real_parts, imag_parts)])
        
        contents.append(ak.contents.NumpyArray(data))
    
    fields = [f"f{i}" for i in range(n_fields)] if draw(st.booleans()) else None
    array = ak.contents.RecordArray(contents, fields=fields)
    at = draw(st.integers(min_value=0, max_value=length-1))
    
    return ak.record.Record(array, at)


@given(complex_record_strategy())
def test_to_list_type_preservation(record):
    """Test that to_list preserves types correctly."""
    result = record.to_list()
    
    if record.is_tuple:
        assert isinstance(result, tuple)
        for i, val in enumerate(result):
            original = record.contents[i]
            if hasattr(original, 'item'):
                original = original.item()
            
            # Check type preservation
            if isinstance(original, (np.integer, int)):
                assert isinstance(val, (int, np.integer))
            elif isinstance(original, (np.floating, float)) and not np.isnan(original):
                if not np.isnan(val):  # NaN comparison is special
                    assert isinstance(val, (float, np.floating))
            elif isinstance(original, (np.bool_, bool)):
                assert isinstance(val, (bool, np.bool_))
            elif isinstance(original, (np.complexfloating, complex)):
                assert isinstance(val, (complex, np.complexfloating))
    else:
        assert isinstance(result, dict)


@given(complex_record_strategy())
def test_slicing_field_subset(record):
    """Test slicing with field subsets."""
    if record.fields and len(record.fields) > 1:
        # Try to slice multiple fields
        subset = list(record.fields[:2])
        try:
            sliced = record[subset]
            # Should return something with those fields
            if hasattr(sliced, 'fields'):
                assert set(sliced.fields) == set(subset)
            elif hasattr(sliced, 'to_list'):
                result = sliced.to_list()
                if isinstance(result, dict):
                    assert set(result.keys()) == set(subset)
        except (TypeError, KeyError, AttributeError):
            # Some field subset operations might not be supported
            pass


@given(complex_record_strategy())
def test_double_copy_identity(record):
    """Test that copying twice gives equivalent results."""
    copy1 = record.copy()
    copy2 = copy1.copy()
    
    assert copy2.at == record.at
    assert copy2.array is record.array
    
    # Contents should be identical
    for i in range(len(record.contents)):
        assert np.array_equal(copy2.contents[i], record.contents[i])


@given(complex_record_strategy())
def test_to_packed_invariants(record):
    """Test invariants of to_packed method."""
    packed = record.to_packed()
    
    # Should still be a Record
    assert isinstance(packed, ak.record.Record)
    
    # Should have same fields
    assert packed.fields == record.fields
    assert packed.is_tuple == record.is_tuple
    
    # Contents should be equivalent
    original_list = record.to_list()
    packed_list = packed.to_list()
    
    if record.is_tuple:
        assert len(original_list) == len(packed_list)
        for o, p in zip(original_list, packed_list):
            if isinstance(o, float) and math.isnan(o):
                assert math.isnan(p)
            else:
                assert o == p or np.array_equal(o, p)
    else:
        assert original_list.keys() == packed_list.keys()
        for key in original_list:
            o = original_list[key]
            p = packed_list[key]
            if isinstance(o, float) and math.isnan(o):
                assert math.isnan(p)
            else:
                assert o == p or np.array_equal(o, p)


@given(complex_record_strategy(), st.integers(min_value=-10, max_value=10))
def test_copy_with_invalid_at_rejection(record, delta):
    """Test that copy properly rejects invalid 'at' values."""
    new_at = record.at + delta
    
    if 0 <= new_at < record.array.length:
        # Should succeed
        new_record = record.copy(at=new_at)
        assert new_record.at == new_at
    else:
        # Should fail
        try:
            new_record = record.copy(at=new_at)
            assert False, f"Should have rejected at={new_at} for array length {record.array.length}"
        except ValueError:
            pass  # Expected


@given(complex_record_strategy())
def test_materialize_idempotence(record):
    """Test that materialize is idempotent."""
    mat1 = record.materialize()
    mat2 = mat1.materialize()
    
    # Should be equivalent
    assert mat1.at == mat2.at
    assert mat1.fields == mat2.fields
    assert mat1.to_list() == mat2.to_list()


@given(complex_record_strategy())
def test_backend_consistency(record):
    """Test backend operations maintain consistency."""
    original_backend = record.backend
    
    # to_backend(None) should return same object
    none_result = record.to_backend(None)
    assert none_result is record
    
    # to_backend with same backend should return same object
    same_result = record.to_backend(original_backend)
    assert same_result is record


@settings(max_examples=200)
@given(complex_record_strategy())
def test_intensive_property_combinations(record):
    """Intensive test combining multiple operations."""
    # Chain multiple operations
    try:
        r1 = record.copy()
        r2 = r1.to_tuple()
        r3 = r2.materialize()
        r4 = r3.to_packed()
        
        # All should maintain the same position
        assert r4.at == record.at or (record.array.length == 1 and r4.at == 0)
        
        # to_list should give equivalent results (accounting for tuple conversion)
        original = record.to_list()
        final = r4.to_list()
        
        if not record.is_tuple and r4.is_tuple:
            # Converted to tuple, so compare values
            assert isinstance(final, tuple)
            if isinstance(original, dict):
                assert len(final) == len(original)
        
    except Exception as e:
        # Log unexpected errors for investigation
        print(f"Unexpected error in property combination: {e}")
        raise


# Look for specific edge cases that might reveal bugs

def test_zero_length_contents_edge_case():
    """Test Record with zero-length contents array."""
    print("Testing zero-length contents...")
    
    # Create RecordArray with no fields
    try:
        array = ak.contents.RecordArray([], fields=[], length=5)
        record = ak.record.Record(array, 2)
        
        assert record.fields == []
        assert record.contents == []
        assert record.to_list() == {}
        print("  ✓ Zero-length contents handled correctly")
    except Exception as e:
        print(f"  ✗ Failed with: {e}")


def test_field_name_collision():
    """Test fields with names that could collide with methods."""
    print("Testing field name collision...")
    
    # Use field names that match Record methods
    dangerous_fields = ["array", "at", "fields", "contents", "copy", "to_list"]
    
    contents = [ak.contents.NumpyArray(np.array([1, 2, 3])) for _ in dangerous_fields]
    array = ak.contents.RecordArray(contents, fields=dangerous_fields)
    record = ak.record.Record(array, 1)
    
    # These should access fields, not methods
    for field in dangerous_fields:
        value = record[field]
        assert value == 2
    
    # Methods should still work
    assert callable(record.copy)
    assert callable(record.to_list)
    
    print("  ✓ Field names don't collide with methods")


def test_unicode_field_names():
    """Test Unicode characters in field names."""
    print("Testing Unicode field names...")
    
    unicode_fields = ["字段", "поле", "フィールド", "🔥", "field_😀"]
    
    contents = [ak.contents.NumpyArray(np.array([10, 20, 30])) for _ in unicode_fields]
    array = ak.contents.RecordArray(contents, fields=unicode_fields)
    record = ak.record.Record(array, 1)
    
    for field in unicode_fields:
        value = record[field]
        assert value == 20
        
    result = record.to_list()
    assert set(result.keys()) == set(unicode_fields)
    
    print("  ✓ Unicode field names work correctly")


if __name__ == "__main__":
    print("Running advanced property tests...")
    print("=" * 50)
    
    # Run hypothesis tests
    print("\nRunning property-based tests...")
    test_funcs = [
        test_to_list_type_preservation,
        test_slicing_field_subset,
        test_double_copy_identity,
        test_to_packed_invariants,
        test_copy_with_invalid_at_rejection,
        test_materialize_idempotence,
        test_backend_consistency,
        test_intensive_property_combinations,
    ]
    
    for func in test_funcs:
        print(f"\n{func.__name__}:")
        try:
            func()
            print(f"  ✓ Passed")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    # Run edge case tests
    print("\n" + "=" * 50)
    print("Running edge case tests...")
    
    test_zero_length_contents_edge_case()
    test_field_name_collision()
    test_unicode_field_names()
    
    print("\n" + "=" * 50)
    print("Testing complete!")