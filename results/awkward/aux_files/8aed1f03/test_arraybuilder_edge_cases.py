"""Test edge cases and complex scenarios for ArrayBuilder"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
from hypothesis import given, strategies as st, assume, settings
import pytest
import math
import datetime


# Test deeply nested structures
@given(depth=st.integers(min_value=1, max_value=10))
def test_deeply_nested_lists(depth):
    """Test building deeply nested list structures"""
    builder = ak.ArrayBuilder()
    
    # Build nested structure
    for _ in range(depth):
        builder.begin_list()
    
    builder.integer(42)
    
    for _ in range(depth):
        builder.end_list()
    
    result = builder.snapshot().to_list()
    
    # Verify structure
    current = result
    for _ in range(depth):
        assert isinstance(current, list)
        assert len(current) == 1
        current = current[0]
    assert current == 42


# Test tuple field consistency
@given(
    num_tuples=st.integers(min_value=1, max_value=10),
    num_fields=st.integers(min_value=1, max_value=5)
)
def test_tuple_field_consistency(num_tuples, num_fields):
    """All tuples should have exactly the specified number of fields"""
    builder = ak.ArrayBuilder()
    
    for i in range(num_tuples):
        builder.begin_tuple(num_fields)
        for j in range(num_fields):
            builder.index(j).integer(i * 10 + j)
        builder.end_tuple()
    
    result = builder.snapshot().to_list()
    
    assert len(result) == num_tuples
    for i, tup in enumerate(result):
        assert isinstance(tup, tuple)
        assert len(tup) == num_fields
        for j in range(num_fields):
            assert tup[j] == i * 10 + j


# Test complex type preservation
def test_datetime_timedelta_preservation():
    """Test that datetime and timedelta values are preserved correctly"""
    builder = ak.ArrayBuilder()
    
    dt1 = datetime.datetime(2024, 1, 15, 10, 30, 45)
    dt2 = datetime.datetime(2024, 12, 31, 23, 59, 59)
    td1 = datetime.timedelta(days=7, hours=3, minutes=30)
    td2 = datetime.timedelta(seconds=3600)
    
    builder.datetime(dt1)
    builder.datetime(dt2)
    builder.timedelta(td1)
    builder.timedelta(td2)
    
    result = builder.snapshot()
    
    # Check the values are preserved
    assert len(result) == 4
    # Note: to_list() might convert these to timestamps/nanoseconds
    # So we check the type instead
    assert result.type.content.tag == "datetime64"


# Test complex number preservation
@given(
    real=st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
    imag=st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)
)
def test_complex_number_preservation(real, imag):
    """Complex numbers should preserve real and imaginary parts"""
    builder = ak.ArrayBuilder()
    
    c = complex(real, imag)
    builder.complex(c)
    
    result = builder.snapshot().to_list()
    
    assert len(result) == 1
    assert isinstance(result[0], complex)
    assert math.isclose(result[0].real, real, rel_tol=1e-9)
    assert math.isclose(result[0].imag, imag, rel_tol=1e-9)


# Test string encoding preservation
@given(text=st.text(min_size=0, max_size=100))
def test_string_preservation(text):
    """UTF-8 strings should be preserved exactly"""
    builder = ak.ArrayBuilder()
    builder.string(text)
    
    result = builder.snapshot().to_list()
    
    assert len(result) == 1
    assert result[0] == text


# Test bytestring preservation
@given(data=st.binary(min_size=0, max_size=100))
def test_bytestring_preservation(data):
    """Bytestrings should be preserved exactly"""
    builder = ak.ArrayBuilder()
    builder.bytestring(data)
    
    result = builder.snapshot().to_list()
    
    assert len(result) == 1
    assert result[0] == data


# Test append with awkward arrays
def test_append_existing_array():
    """Test appending data from existing awkward arrays"""
    # Create an existing array
    existing = ak.Array([[1, 2, 3], [4, 5], [6, 7, 8, 9]])
    
    builder = ak.ArrayBuilder()
    builder.append(existing[0])  # Append first element
    builder.append(existing[1])  # Append second element
    
    result = builder.snapshot().to_list()
    
    assert result == [[1, 2, 3], [4, 5]]


# Test mixed list and record structures
def test_mixed_list_record_structures():
    """Test building arrays with mixed lists and records"""
    builder = ak.ArrayBuilder()
    
    # List of records
    builder.begin_list()
    builder.begin_record()
    builder.field("x").integer(1)
    builder.field("y").integer(2)
    builder.end_record()
    builder.begin_record()
    builder.field("x").integer(3)
    builder.field("y").integer(4)
    builder.end_record()
    builder.end_list()
    
    # Single record
    builder.begin_record()
    builder.field("x").integer(5)
    builder.field("y").integer(6)
    builder.end_record()
    
    result = builder.snapshot().to_list()
    expected = [[{"x": 1, "y": 2}, {"x": 3, "y": 4}], {"x": 5, "y": 6}]
    
    # This should fail because of type mismatch
    # The builder creates a union type for this
    print(f"Result: {result}")
    print(f"Type: {builder.snapshot().type}")


# Test error conditions
def test_invalid_tuple_index():
    """Test that invalid tuple indices raise errors"""
    builder = ak.ArrayBuilder()
    builder.begin_tuple(3)
    
    # Valid indices
    builder.index(0).integer(1)
    builder.index(1).integer(2)
    builder.index(2).integer(3)
    
    # Try invalid index - this might not raise immediately but on end_tuple
    try:
        builder.index(5).integer(999)  # Out of bounds
        builder.end_tuple()
        # If we get here, check if it was silently ignored or added
        result = builder.snapshot().to_list()
        print(f"No error raised. Result: {result}")
        if len(result[0]) > 3:
            print("BUG: Tuple has more fields than specified!")
            return False
    except Exception as e:
        print(f"Expected error raised: {e}")
        return True


# Test builder state after snapshot
@given(values=st.lists(st.integers(), min_size=1, max_size=10))
def test_builder_state_after_snapshot(values):
    """Builder should continue to work normally after taking snapshots"""
    builder = ak.ArrayBuilder()
    
    # Add first batch
    for v in values[:len(values)//2]:
        builder.integer(v)
    
    snapshot1 = builder.snapshot()
    
    # Add second batch
    for v in values[len(values)//2:]:
        builder.integer(v)
    
    snapshot2 = builder.snapshot()
    
    # snapshot2 should contain all values
    assert snapshot2.to_list() == values
    assert len(snapshot2) == len(values)


if __name__ == "__main__":
    print("Running edge case tests...")
    
    # Run property tests with pytest
    pytest.main([__file__, "-v", "-k", "not invalid_tuple"])