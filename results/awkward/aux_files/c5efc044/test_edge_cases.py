#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import copy
import numpy as np
import awkward as ak
from hypothesis import given, strategies as st, assume, settings
import math


# Test for edge cases and potential bugs

def test_deep_copy_independence():
    """Test that deep copy creates truly independent objects."""
    print("Testing deep copy independence...")
    
    # Create a record
    array = ak.contents.RecordArray(
        [ak.contents.NumpyArray(np.array([1, 2, 3]))],
        fields=["x"]
    )
    record = ak.record.Record(array, 1)
    
    # Deep copy
    record_copy = copy.deepcopy(record)
    
    # Modify the original array's data (if possible)
    # This tests if deep copy is truly independent
    original_x_value = record["x"]
    copy_x_value = record_copy["x"]
    
    print(f"  Original x: {original_x_value}")
    print(f"  Copy x: {copy_x_value}")
    
    # They should be equal but not the same object
    assert original_x_value == copy_x_value
    assert record_copy.array is not record.array
    print("  ✓ Deep copy creates independent arrays")


def test_to_list_with_nested_structures():
    """Test to_list with more complex nested structures."""
    print("\nTesting to_list with nested structures...")
    
    # Create nested arrays
    inner1 = ak.contents.NumpyArray(np.array([1.0, 2.0, 3.0]))
    inner2 = ak.contents.NumpyArray(np.array([4.0, 5.0, 6.0]))
    
    # Create a record array with nested content
    array = ak.contents.RecordArray(
        [inner1, inner2],
        fields=["a", "b"]
    )
    
    record = ak.record.Record(array, 0)
    result = record.to_list()
    
    print(f"  to_list result: {result}")
    assert result == {"a": 1.0, "b": 4.0}
    print("  ✓ to_list handles nested structures correctly")


def test_field_access_with_special_characters():
    """Test field names with special characters."""
    print("\nTesting field names with special characters...")
    
    # Field names that might cause issues
    special_fields = ["field-with-dash", "field.with.dots", "field_with_underscore", "0numeric"]
    
    array = ak.contents.RecordArray(
        [ak.contents.NumpyArray(np.array([1, 2, 3])) for _ in special_fields],
        fields=special_fields
    )
    
    record = ak.record.Record(array, 1)
    
    for field in special_fields:
        value = record[field]
        print(f"  Field '{field}': {value}")
        assert value == 2
    
    print("  ✓ Special characters in field names work correctly")


def test_parameters_inheritance():
    """Test that parameters are properly inherited from array."""
    print("\nTesting parameters inheritance...")
    
    # Create array with parameters
    array = ak.contents.RecordArray(
        [ak.contents.NumpyArray(np.array([1, 2, 3]))],
        fields=["x"],
        parameters={"test_param": "test_value"}
    )
    
    record = ak.record.Record(array, 1)
    
    assert record.parameters == {"test_param": "test_value"}
    assert record.parameter("test_param") == "test_value"
    print("  ✓ Parameters are inherited from array")


def test_record_with_nan_and_inf():
    """Test Record with NaN and infinity values."""
    print("\nTesting with NaN and infinity...")
    
    data_with_special = np.array([1.0, float('nan'), float('inf'), -float('inf'), 2.0])
    array = ak.contents.RecordArray(
        [ak.contents.NumpyArray(data_with_special)],
        fields=["values"]
    )
    
    # Test with NaN
    record_nan = ak.record.Record(array, 1)
    value = record_nan["values"]
    assert math.isnan(value)
    print(f"  NaN value: {value} (isnan: {math.isnan(value)})")
    
    # Test with inf
    record_inf = ak.record.Record(array, 2)
    value = record_inf["values"]
    assert math.isinf(value) and value > 0
    print(f"  Inf value: {value}")
    
    # Test with -inf
    record_neginf = ak.record.Record(array, 3)
    value = record_neginf["values"]
    assert math.isinf(value) and value < 0
    print(f"  -Inf value: {value}")
    
    # Test to_list with special values
    result = record_nan.to_list()
    assert math.isnan(result["values"])
    
    print("  ✓ NaN and infinity values handled correctly")


def test_getitem_with_empty_tuple():
    """Test that record[()] returns self."""
    print("\nTesting getitem with empty tuple...")
    
    array = ak.contents.RecordArray(
        [ak.contents.NumpyArray(np.array([1, 2, 3]))],
        fields=["x"]
    )
    record = ak.record.Record(array, 1)
    
    # According to line 159-160 in record.py, record[()] should return self
    result = record[()]
    assert result is record
    print("  ✓ record[()] returns self")


def test_getitem_field_chains():
    """Test chained field access."""
    print("\nTesting chained field access...")
    
    # Create nested record structure
    inner_array = ak.contents.RecordArray(
        [ak.contents.NumpyArray(np.array([10, 20, 30]))],
        fields=["inner_field"]
    )
    
    # This might not work as expected, but let's test the tuple syntax from line 165-166
    array = ak.contents.RecordArray(
        [ak.contents.NumpyArray(np.array([1, 2, 3]))],
        fields=["x"]
    )
    record = ak.record.Record(array, 1)
    
    # Test single field in tuple
    result = record[("x",)]
    assert result == 2
    print(f"  record[('x',)] = {result}")
    
    print("  ✓ Field access with tuples works")


def test_validity_error():
    """Test validity_error method."""
    print("\nTesting validity_error method...")
    
    array = ak.contents.RecordArray(
        [ak.contents.NumpyArray(np.array([1, 2, 3]))],
        fields=["x"]
    )
    record = ak.record.Record(array, 1)
    
    # validity_error should return None if valid
    error = record.validity_error()
    print(f"  Validity error: {error}")
    assert error is None or error == ""
    print("  ✓ validity_error returns expected value")


def test_to_packed():
    """Test to_packed method."""
    print("\nTesting to_packed method...")
    
    array = ak.contents.RecordArray(
        [ak.contents.NumpyArray(np.array([1, 2, 3]))],
        fields=["x"]
    )
    record = ak.record.Record(array, 1)
    
    packed = record.to_packed()
    assert isinstance(packed, ak.record.Record)
    assert packed.at == record.at or packed.at == 0  # Depending on implementation
    print(f"  Packed record at: {packed.at}")
    print("  ✓ to_packed returns Record")


# Run all edge case tests
if __name__ == "__main__":
    tests = [
        test_deep_copy_independence,
        test_to_list_with_nested_structures,
        test_field_access_with_special_characters,
        test_parameters_inheritance,
        test_record_with_nan_and_inf,
        test_getitem_with_empty_tuple,
        test_getitem_field_chains,
        test_validity_error,
        test_to_packed,
    ]
    
    print("Running edge case tests for awkward.record.Record...")
    print("=" * 50)
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("Edge case testing complete!")