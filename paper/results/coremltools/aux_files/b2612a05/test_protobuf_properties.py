#!/usr/bin/env python3
"""Property-based tests for coremltools.proto using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import coremltools.proto.DataStructures_pb2 as DS
import coremltools.proto.Model_pb2 as Model
import coremltools.proto.FeatureTypes_pb2 as FT


# Strategies for generating test data
safe_floats = st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)
safe_doubles = safe_floats
safe_strings = st.text(min_size=0, max_size=1000)
safe_int64s = st.integers(min_value=-2**63+1, max_value=2**63-1)

# Test 1: Round-trip serialization for vector types
@given(st.lists(safe_doubles, min_size=0, max_size=1000))
def test_double_vector_round_trip(values):
    """Test that DoubleVector serialization/deserialization preserves data."""
    vec = DS.DoubleVector()
    vec.vector.extend(values)
    
    # Serialize and deserialize
    serialized = vec.SerializeToString()
    vec2 = DS.DoubleVector()
    vec2.ParseFromString(serialized)
    
    # Check values are preserved
    assert list(vec2.vector) == values


@given(st.lists(safe_floats, min_size=0, max_size=1000))
def test_float_vector_round_trip(values):
    """Test that FloatVector serialization/deserialization preserves data."""
    vec = DS.FloatVector()
    vec.vector.extend(values)
    
    serialized = vec.SerializeToString()
    vec2 = DS.FloatVector()
    vec2.ParseFromString(serialized)
    
    # Note: float32 precision may differ slightly from Python floats
    assert len(vec2.vector) == len(values)
    for v1, v2 in zip(values, vec2.vector):
        # Account for float32 precision
        if v1 != 0:
            assert abs(v1 - v2) / abs(v1) < 1e-6
        else:
            assert abs(v2) < 1e-6


@given(st.lists(safe_int64s, min_size=0, max_size=1000))
def test_int64_vector_round_trip(values):
    """Test that Int64Vector serialization/deserialization preserves data."""
    vec = DS.Int64Vector()
    vec.vector.extend(values)
    
    serialized = vec.SerializeToString()
    vec2 = DS.Int64Vector()
    vec2.ParseFromString(serialized)
    
    assert list(vec2.vector) == values


@given(st.lists(safe_strings, min_size=0, max_size=100))
def test_string_vector_round_trip(values):
    """Test that StringVector serialization/deserialization preserves data."""
    vec = DS.StringVector()
    vec.vector.extend(values)
    
    serialized = vec.SerializeToString()
    vec2 = DS.StringVector()
    vec2.ParseFromString(serialized)
    
    assert list(vec2.vector) == values


# Test 2: Map round-trip serialization
@given(st.dictionaries(safe_strings, safe_doubles, min_size=0, max_size=100))
def test_string_to_double_map_round_trip(mapping):
    """Test StringToDoubleMap serialization round-trip."""
    msg = DS.StringToDoubleMap()
    for k, v in mapping.items():
        msg.map[k] = v
    
    serialized = msg.SerializeToString()
    msg2 = DS.StringToDoubleMap()
    msg2.ParseFromString(serialized)
    
    assert dict(msg2.map) == mapping


@given(st.dictionaries(safe_strings, safe_int64s, min_size=0, max_size=100))
def test_string_to_int64_map_round_trip(mapping):
    """Test StringToInt64Map serialization round-trip."""
    msg = DS.StringToInt64Map()
    for k, v in mapping.items():
        msg.map[k] = v
    
    serialized = msg.SerializeToString()
    msg2 = DS.StringToInt64Map()
    msg2.ParseFromString(serialized)
    
    assert dict(msg2.map) == mapping


@given(st.dictionaries(safe_int64s, safe_doubles, min_size=0, max_size=100))
def test_int64_to_double_map_round_trip(mapping):
    """Test Int64ToDoubleMap serialization round-trip."""
    msg = DS.Int64ToDoubleMap()
    for k, v in mapping.items():
        msg.map[k] = v
    
    serialized = msg.SerializeToString()
    msg2 = DS.Int64ToDoubleMap()
    msg2.ParseFromString(serialized)
    
    assert dict(msg2.map) == mapping


@given(st.dictionaries(safe_int64s, safe_strings, min_size=0, max_size=100))
def test_int64_to_string_map_round_trip(mapping):
    """Test Int64ToStringMap serialization round-trip."""
    msg = DS.Int64ToStringMap()
    for k, v in mapping.items():
        msg.map[k] = v
    
    serialized = msg.SerializeToString()
    msg2 = DS.Int64ToStringMap()
    msg2.ParseFromString(serialized)
    
    assert dict(msg2.map) == mapping


# Test 3: Clear() resets to default state
@given(st.lists(safe_doubles, min_size=1, max_size=100))
def test_clear_resets_double_vector(values):
    """Test that Clear() resets DoubleVector to empty state."""
    vec = DS.DoubleVector()
    vec.vector.extend(values)
    
    assert len(vec.vector) > 0
    vec.Clear()
    assert len(vec.vector) == 0
    assert list(vec.vector) == []


@given(st.dictionaries(safe_strings, safe_doubles, min_size=1, max_size=50))
def test_clear_resets_string_double_map(mapping):
    """Test that Clear() resets StringToDoubleMap to empty state."""
    msg = DS.StringToDoubleMap()
    for k, v in mapping.items():
        msg.map[k] = v
    
    assert len(msg.map) > 0
    msg.Clear()
    assert len(msg.map) == 0
    assert dict(msg.map) == {}


# Test 4: CopyFrom creates exact copy
@given(st.lists(safe_doubles, min_size=0, max_size=100))
def test_copy_from_double_vector(values):
    """Test that CopyFrom creates an exact copy of DoubleVector."""
    vec1 = DS.DoubleVector()
    vec1.vector.extend(values)
    
    vec2 = DS.DoubleVector()
    vec2.CopyFrom(vec1)
    
    assert list(vec2.vector) == values
    assert vec1.SerializeToString() == vec2.SerializeToString()


@given(st.dictionaries(safe_strings, safe_int64s, min_size=0, max_size=50))
def test_copy_from_string_int64_map(mapping):
    """Test that CopyFrom creates an exact copy of StringToInt64Map."""
    msg1 = DS.StringToInt64Map()
    for k, v in mapping.items():
        msg1.map[k] = v
    
    msg2 = DS.StringToInt64Map()
    msg2.CopyFrom(msg1)
    
    assert dict(msg2.map) == mapping
    assert msg1.SerializeToString() == msg2.SerializeToString()


# Test 5: ByteSize consistency
@given(st.lists(safe_doubles, min_size=0, max_size=100))
def test_byte_size_consistency_double_vector(values):
    """Test that ByteSize() is consistent with serialized size."""
    vec = DS.DoubleVector()
    vec.vector.extend(values)
    
    byte_size = vec.ByteSize()
    serialized = vec.SerializeToString()
    
    # ByteSize should match the length of serialized data
    assert byte_size == len(serialized)


@given(st.dictionaries(safe_strings, safe_doubles, min_size=0, max_size=50))
def test_byte_size_consistency_map(mapping):
    """Test that ByteSize() is consistent for maps."""
    msg = DS.StringToDoubleMap()
    for k, v in mapping.items():
        msg.map[k] = v
    
    byte_size = msg.ByteSize()
    serialized = msg.SerializeToString()
    
    assert byte_size == len(serialized)


# Test 6: Idempotent serialization
@given(st.lists(safe_int64s, min_size=0, max_size=100))
def test_idempotent_serialization(values):
    """Test that multiple serializations produce identical results."""
    vec = DS.Int64Vector()
    vec.vector.extend(values)
    
    serialized1 = vec.SerializeToString()
    serialized2 = vec.SerializeToString()
    
    assert serialized1 == serialized2


# Test 7: ArrayFeatureType shape handling
@given(st.lists(st.integers(min_value=1, max_value=10000), min_size=0, max_size=10))
def test_array_feature_type_shape(shape):
    """Test ArrayFeatureType shape preservation."""
    arr_type = FT.ArrayFeatureType()
    arr_type.shape.extend(shape)
    
    serialized = arr_type.SerializeToString()
    arr_type2 = FT.ArrayFeatureType()
    arr_type2.ParseFromString(serialized)
    
    assert list(arr_type2.shape) == shape


# Test 8: Overwriting values in vectors
@given(
    st.lists(safe_doubles, min_size=1, max_size=100),
    st.lists(safe_doubles, min_size=1, max_size=100)
)
def test_vector_overwrite(values1, values2):
    """Test that vector values can be properly overwritten."""
    vec = DS.DoubleVector()
    
    # Set initial values
    vec.vector.extend(values1)
    assert list(vec.vector) == values1
    
    # Clear and set new values
    del vec.vector[:]
    vec.vector.extend(values2)
    assert list(vec.vector) == values2


# Test 9: Map key collision and overwrite
@given(
    st.lists(st.tuples(safe_strings, safe_doubles), min_size=1, max_size=50)
)
def test_map_key_overwrite(pairs):
    """Test map behavior with duplicate keys."""
    msg = DS.StringToDoubleMap()
    
    expected = {}
    for k, v in pairs:
        msg.map[k] = v
        expected[k] = v  # Later values should overwrite
    
    assert dict(msg.map) == expected


# Test 10: Empty message serialization
def test_empty_messages():
    """Test that empty messages serialize and deserialize correctly."""
    # Test empty vector
    vec = DS.DoubleVector()
    serialized = vec.SerializeToString()
    vec2 = DS.DoubleVector()
    vec2.ParseFromString(serialized)
    assert list(vec2.vector) == []
    
    # Test empty map
    msg = DS.StringToDoubleMap()
    serialized = msg.SerializeToString()
    msg2 = DS.StringToDoubleMap()
    msg2.ParseFromString(serialized)
    assert dict(msg2.map) == {}


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])