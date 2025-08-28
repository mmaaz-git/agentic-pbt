#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import copy
import numpy as np
import awkward as ak
from hypothesis import given, strategies as st, assume, settings
import pytest


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


# More advanced strategies for edge cases
@st.composite
def empty_record_array_strategy(draw):
    """Generate RecordArray with no fields (edge case)."""
    length = draw(st.integers(min_value=1, max_value=10))
    # Empty record array - this might be an edge case
    return ak.contents.RecordArray([], fields=[], length=length)


@st.composite
def nested_record_array_strategy(draw):
    """Generate nested RecordArrays."""
    length = draw(st.integers(min_value=1, max_value=10))
    
    # Create a nested structure with record arrays containing record arrays
    inner_array = draw(record_array_strategy())
    
    # Wrap in list array
    list_array = ak.contents.ListOffsetArray(
        ak.index.Index64(np.arange(length + 1)),
        inner_array
    )
    
    # Create outer record with the list
    return ak.contents.RecordArray(
        [list_array],
        fields=["nested"]
    )


# Additional property tests

@given(empty_record_array_strategy(), st.integers(min_value=0))
def test_empty_record_array(array, at):
    """Test Record with empty RecordArray (no fields)."""
    if at < array.length:
        record = ak.record.Record(array, at)
        assert record.fields == []
        assert record.contents == []
        assert record.to_list() == {}


@given(record_strategy())
def test_getitem_errors(record):
    """Test that invalid getitem operations raise appropriate errors."""
    # Integer indexing should fail
    with pytest.raises(IndexError, match="scalar Record cannot be sliced by an integer"):
        record[0]
    
    # Slice indexing should fail
    with pytest.raises(IndexError, match="scalar Record cannot be sliced by a range slice"):
        record[:]
    
    # newaxis should fail
    with pytest.raises(IndexError, match="scalar Record cannot be sliced by np.newaxis"):
        record[np.newaxis]
    
    # Ellipsis should fail
    with pytest.raises(IndexError, match="scalar Record cannot be sliced by an ellipsis"):
        record[...]


@given(record_strategy())
def test_type_validation(record):
    """Test type validation in Record constructor."""
    # Wrong type for array parameter
    with pytest.raises(TypeError, match="Record 'array' must be a RecordArray"):
        ak.record.Record("not an array", 0)
    
    # Wrong type for at parameter  
    with pytest.raises(TypeError, match="Record 'at' must be an integer"):
        ak.record.Record(record.array, "not an int")


@given(record_strategy())
def test_materialize_property(record):
    """Test materialize() returns a Record."""
    materialized = record.materialize()
    assert isinstance(materialized, ak.record.Record)
    assert materialized.at == record.at


@given(record_strategy())
def test_backend_property(record):
    """Test backend property and to_backend method."""
    backend = record.backend
    assert backend is not None
    
    # to_backend with same backend should return same object
    same_backend = record.to_backend(backend)
    assert same_backend is record
    
    # to_backend with None should use current backend
    none_backend = record.to_backend(None)
    assert none_backend is record


@given(record_strategy())
def test_parameters_property(record):
    """Test parameters property access."""
    params = record.parameters
    # Should be dict-like
    assert isinstance(params, dict) or params == {}


@given(record_strategy())
def test_depth_properties(record):
    """Test various depth properties."""
    # purelist_depth should be 0 for scalar
    assert record.purelist_depth == 0
    
    # minmax_depth should return tuple
    mindepth, maxdepth = record.minmax_depth
    assert isinstance(mindepth, int)
    assert isinstance(maxdepth, int)
    
    # branch_depth should return tuple
    branch, depth = record.branch_depth
    assert isinstance(depth, int)


# Test for potential bugs with special values

@given(record_strategy())
def test_copy_parameter_override(record):
    """Test copy() with parameter overrides."""
    # Create a different array
    new_array = ak.contents.RecordArray(
        [ak.contents.NumpyArray(np.array([99, 98, 97]))],
        fields=["x"]
    )
    
    # Copy with new array
    new_record = record.copy(array=new_array)
    assert new_record.array is new_array
    assert new_record.at == record.at  # at should be unchanged
    
    # Copy with new at
    if record.array.length > 1:
        new_at = (record.at + 1) % record.array.length
        new_record2 = record.copy(at=new_at)
        assert new_record2.array is record.array
        assert new_record2.at == new_at


@settings(max_examples=500)
@given(record_strategy())
def test_intensive_field_access(record):
    """Intensive test of field access with many examples."""
    if record.fields:
        # Access all fields multiple ways
        for field in record.fields:
            val1 = record[field]
            val2 = record.content(field)
            val3 = record._getitem_field(field)
            
            # All should give same result
            assert np.array_equal(val1, val2)
            assert np.array_equal(val1, val3)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])