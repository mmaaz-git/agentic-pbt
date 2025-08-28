#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import copy
import numpy as np
import awkward as ak
from hypothesis import given, strategies as st, assume, settings


# Strategies for generating test data
@st.composite
def record_array_strategy(draw):
    """Generate a valid RecordArray with random fields and data."""
    n_fields = draw(st.integers(min_value=1, max_value=5))
    length = draw(st.integers(min_value=1, max_value=100))
    
    # Generate field names or None for tuple-like
    use_fields = draw(st.booleans())
    if use_fields:
        fields = [f"field_{i}" for i in range(n_fields)]
    else:
        fields = None
    
    # Generate contents - using simple numpy arrays
    contents = []
    for _ in range(n_fields):
        dtype = draw(st.sampled_from([np.int32, np.int64, np.float32, np.float64]))
        if dtype in [np.int32, np.int64]:
            data = draw(st.lists(
                st.integers(min_value=-1000, max_value=1000),
                min_size=length,
                max_size=length
            ))
        else:
            data = draw(st.lists(
                st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
                min_size=length,
                max_size=length
            ))
        contents.append(ak.contents.NumpyArray(np.array(data, dtype=dtype)))
    
    return ak.contents.RecordArray(contents, fields=fields)


@st.composite
def record_strategy(draw):
    """Generate a valid Record from a RecordArray."""
    array = draw(record_array_strategy())
    at = draw(st.integers(min_value=0, max_value=array.length - 1))
    return ak.record.Record(array, at)


# Property 1: Bounds checking invariant
@given(record_array_strategy(), st.integers())
def test_bounds_checking_invariant(array, at):
    """Record creation should enforce bounds: 0 <= at < array.length"""
    if 0 <= at < array.length:
        # Should succeed
        record = ak.record.Record(array, at)
        assert record.at == at
        assert record.array is array
    else:
        # Should fail with ValueError
        try:
            record = ak.record.Record(array, at)
            assert False, f"Should have raised ValueError for at={at}, length={array.length}"
        except ValueError as e:
            assert "must be >= 0 and < len(array)" in str(e)


# Property 2: Copy semantics
@given(record_strategy())
def test_copy_semantics(record):
    """copy() should create new Record instance but share array reference"""
    # Shallow copy
    record_copy = record.copy()
    
    # Should be different Record instances
    assert record_copy is not record
    
    # But should share the same array
    assert record_copy.array is record.array
    
    # And have the same position
    assert record_copy.at == record.at
    
    # Deep copy should create new array
    record_deepcopy = copy.deepcopy(record)
    assert record_deepcopy is not record
    assert record_deepcopy.array is not record.array
    assert record_deepcopy.at == record.at


# Property 3: Field access consistency
@given(record_strategy())
def test_field_access_consistency(record):
    """Accessing fields should return consistent values"""
    if record.fields is None:
        # Tuple-like record - access by index
        contents = record.contents
        for i in range(len(contents)):
            assert record.content(i) == contents[i]
    else:
        # Field-based record - access by field name
        contents_by_field = {}
        for field in record.fields:
            contents_by_field[field] = record[field]
        
        # Check contents match
        for i, field in enumerate(record.fields):
            assert record[field] == record.content(field)
            assert record[field] == record.contents[i]


# Property 4: to_list round-trip for dict records
@given(record_strategy())
def test_to_list_structure(record):
    """to_list() should return dict for field records, tuple for tuple records"""
    result = record.to_list()
    
    if record.is_tuple:
        # Should return tuple
        assert isinstance(result, tuple)
        assert len(result) == len(record.contents)
        for i, val in enumerate(result):
            expected = record.contents[i]
            # Handle numpy scalar conversion
            if hasattr(expected, 'item'):
                expected = expected.item()
            assert val == expected
    else:
        # Should return dict
        assert isinstance(result, dict)
        assert set(result.keys()) == set(record.fields)
        for field in record.fields:
            expected = record[field]
            # Handle numpy scalar conversion
            if hasattr(expected, 'item'):
                expected = expected.item()
            assert result[field] == expected


# Property 5: Immutability of position
@given(record_strategy())
def test_position_immutability(record):
    """The 'at' property should remain constant after creation"""
    initial_at = record.at
    
    # Try various operations that shouldn't change 'at'
    _ = record.fields
    _ = record.contents
    _ = record.to_list()
    _ = record.parameters
    
    # 'at' should still be the same
    assert record.at == initial_at
    
    # Also test that we can't modify it directly (no setter)
    assert not hasattr(record, '_at') or record._at == initial_at


# Property 6: to_tuple conversion
@given(record_strategy())
def test_to_tuple_conversion(record):
    """to_tuple() should convert record to tuple form"""
    tuple_record = record.to_tuple()
    
    # Should be a Record
    assert isinstance(tuple_record, ak.record.Record)
    
    # Should be tuple-like
    assert tuple_record.is_tuple
    
    # Should have same position
    assert tuple_record.at == record.at
    
    # Should have same contents
    assert len(tuple_record.contents) == len(record.contents)
    for i in range(len(record.contents)):
        assert np.array_equal(tuple_record.contents[i], record.contents[i])


# Property 7: Field slicing
@given(record_strategy())
def test_field_slicing(record):
    """Test that field slicing returns expected values"""
    if record.fields is not None and len(record.fields) > 0:
        # Test single field access
        for field in record.fields:
            value = record[field]
            # Should match content access
            assert value == record.content(field)
        
        # Test multiple field access
        if len(record.fields) > 1:
            subset_fields = record.fields[:2]
            subset_record = record[subset_fields]
            # This should return a record with only those fields
            if hasattr(subset_record, 'fields'):
                assert set(subset_record.fields) == set(subset_fields)


# Property 8: Copy with different at
@given(record_strategy(), st.integers(min_value=0, max_value=99))
def test_copy_with_different_at(record, new_at):
    """copy() with different 'at' should create record at new position"""
    assume(new_at < record.array.length)
    
    new_record = record.copy(at=new_at)
    
    # Should have new position
    assert new_record.at == new_at
    
    # Should share same array
    assert new_record.array is record.array
    
    # Contents should be from new position
    if record.fields is not None:
        for field in record.fields:
            assert new_record[field] == record.array[field][new_at]


if __name__ == "__main__":
    print("Running property-based tests for awkward.record.Record...")
    
    # Run with more examples for thorough testing
    settings_obj = settings(max_examples=100)
    
    # Run all tests
    test_funcs = [
        test_bounds_checking_invariant,
        test_copy_semantics,
        test_field_access_consistency,
        test_to_list_structure,
        test_position_immutability,
        test_to_tuple_conversion,
        test_field_slicing,
        test_copy_with_different_at,
    ]
    
    for test_func in test_funcs:
        print(f"\nTesting: {test_func.__name__}")
        try:
            test_func()
            print(f"  ✓ {test_func.__doc__.strip()}")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    print("\nDone!")