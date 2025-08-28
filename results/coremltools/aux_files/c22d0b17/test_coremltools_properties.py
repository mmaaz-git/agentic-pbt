#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import math
from hypothesis import given, strategies as st, assume, settings
import pytest

# Import the modules to test
from coremltools.models import datatypes
from coremltools.models import array_feature_extractor
from coremltools.models.datatypes import _normalize_datatype, _is_valid_datatype


# Test 1: Array datatype invariants
@given(st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=5))
def test_array_num_elements_invariant(dimensions):
    """Test that Array.num_elements equals the product of dimensions."""
    arr = datatypes.Array(*dimensions)
    
    # Calculate expected num_elements
    expected_num_elements = 1
    for d in dimensions:
        expected_num_elements *= d
    
    assert arr.num_elements == expected_num_elements


@given(st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=5))
def test_array_equality_reflexive(dimensions):
    """Test that Array equality is reflexive: a == a."""
    arr = datatypes.Array(*dimensions)
    assert arr == arr


@given(
    st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=5),
    st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=5)
)
def test_array_equality_symmetric(dims1, dims2):
    """Test that Array equality is symmetric: if a == b then b == a."""
    arr1 = datatypes.Array(*dims1)
    arr2 = datatypes.Array(*dims2)
    
    if arr1 == arr2:
        assert arr2 == arr1
    if arr1 != arr2:
        assert arr2 != arr1


@given(st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=5))
def test_array_hash_consistency(dimensions):
    """Test that equal Arrays have equal hashes."""
    arr1 = datatypes.Array(*dimensions)
    arr2 = datatypes.Array(*dimensions)
    
    assert arr1 == arr2
    assert hash(arr1) == hash(arr2)


# Test 2: Dictionary datatype properties
def test_dictionary_with_valid_key_types():
    """Test that Dictionary accepts valid key types."""
    # These should all work
    dict1 = datatypes.Dictionary(datatypes.Int64())
    dict2 = datatypes.Dictionary(datatypes.String())
    dict3 = datatypes.Dictionary(int)
    dict4 = datatypes.Dictionary(str)
    
    assert dict1.key_type == datatypes.Int64()
    assert dict2.key_type == datatypes.String()
    assert dict3.key_type == datatypes.Int64()
    assert dict4.key_type == datatypes.String()


@given(st.sampled_from([datatypes.Double(), datatypes.Array(5), float]))
def test_dictionary_rejects_invalid_key_types(invalid_key):
    """Test that Dictionary rejects invalid key types."""
    with pytest.raises(TypeError, match="Key type for dictionary must be either string or integer"):
        datatypes.Dictionary(invalid_key)


# Test 3: Simple datatype equality and hashing
def test_simple_datatype_singleton_properties():
    """Test that simple datatypes behave like singletons."""
    # Multiple instances should be equal
    int1 = datatypes.Int64()
    int2 = datatypes.Int64()
    assert int1 == int2
    assert hash(int1) == hash(int2)
    
    double1 = datatypes.Double()
    double2 = datatypes.Double()
    assert double1 == double2
    assert hash(double1) == hash(double2)
    
    string1 = datatypes.String()
    string2 = datatypes.String()
    assert string1 == string2
    assert hash(string1) == hash(string2)


# Test 4: Datatype normalization idempotence
@given(st.sampled_from([
    int, str, float,
    datatypes.Int64(), datatypes.String(), datatypes.Double(),
    "Int64", "String", "Double"
]))
def test_normalize_datatype_idempotence(datatype):
    """Test that normalizing a datatype twice gives the same result."""
    normalized_once = _normalize_datatype(datatype)
    normalized_twice = _normalize_datatype(normalized_once)
    
    assert normalized_once == normalized_twice
    assert type(normalized_once) == type(normalized_twice)


@given(st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=5))
def test_normalize_array_idempotence(dimensions):
    """Test that normalizing an Array datatype is idempotent."""
    arr = datatypes.Array(*dimensions)
    normalized_once = _normalize_datatype(arr)
    normalized_twice = _normalize_datatype(normalized_once)
    
    assert normalized_once == normalized_twice
    assert normalized_once is arr  # Should return the same object


# Test 5: Array feature extractor constraints
@given(
    array_size=st.integers(min_value=1, max_value=100),
    extract_indices=st.lists(st.integers(min_value=0), min_size=1, max_size=10)
)
def test_array_feature_extractor_index_bounds(array_size, extract_indices):
    """Test that array feature extractor respects index bounds."""
    # Filter indices to be within valid range
    valid_indices = [idx for idx in extract_indices if 0 <= idx < array_size]
    
    if not valid_indices:
        # Skip if no valid indices
        return
    
    input_array = datatypes.Array(array_size)
    input_features = [("input", input_array)]
    
    # This should work with valid indices
    spec = array_feature_extractor.create_array_feature_extractor(
        input_features, "output", valid_indices
    )
    
    # Verify the spec was created correctly
    assert len(spec.arrayFeatureExtractor.extractIndex) == len(valid_indices)
    for idx in spec.arrayFeatureExtractor.extractIndex:
        assert 0 <= idx < array_size


@given(
    array_size=st.integers(min_value=1, max_value=100),
    invalid_index=st.integers()
)
def test_array_feature_extractor_invalid_index_assertion(array_size, invalid_index):
    """Test that array feature extractor raises assertion for out-of-bounds indices."""
    assume(invalid_index < 0 or invalid_index >= array_size)
    
    input_array = datatypes.Array(array_size)
    input_features = [("input", input_array)]
    
    # This should raise an assertion error for invalid indices
    with pytest.raises(AssertionError):
        array_feature_extractor.create_array_feature_extractor(
            input_features, "output", [invalid_index]
        )


# Test 6: Array dimensions must be positive integers
@given(st.lists(st.integers(max_value=0), min_size=1, max_size=5))
def test_array_rejects_non_positive_dimensions(dimensions):
    """Test that Array rejects non-positive dimensions."""
    if any(d <= 0 for d in dimensions):
        with pytest.raises(AssertionError):
            datatypes.Array(*dimensions)


# Test 7: Test valid datatype detection
@given(st.sampled_from([
    int, str, float,
    datatypes.Int64(), datatypes.String(), datatypes.Double(),
    "Int64", "String", "Double",
]))
def test_is_valid_datatype_accepts_valid_types(datatype):
    """Test that _is_valid_datatype accepts all valid types."""
    assert _is_valid_datatype(datatype) == True


@given(st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=5))
def test_is_valid_datatype_accepts_arrays(dimensions):
    """Test that _is_valid_datatype accepts Array types."""
    arr = datatypes.Array(*dimensions)
    assert _is_valid_datatype(arr) == True


@given(st.sampled_from([datatypes.Int64(), datatypes.String()]))
def test_is_valid_datatype_accepts_dictionaries(key_type):
    """Test that _is_valid_datatype accepts Dictionary types with valid keys."""
    dict_type = datatypes.Dictionary(key_type)
    assert _is_valid_datatype(dict_type) == True


if __name__ == "__main__":
    print("Running property-based tests for coremltools.models...")
    pytest.main([__file__, "-v", "--tb=short"])