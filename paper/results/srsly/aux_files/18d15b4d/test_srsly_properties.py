#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

import tempfile
import os
import math
from pathlib import Path
from hypothesis import given, assume, strategies as st, settings
import srsly
import pytest

# Strategy for JSON-serializable data
json_primitives = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-1e15, max_value=1e15),
    st.floats(allow_nan=False, allow_infinity=False, width=64),
    st.text(min_size=0, max_size=100)
)

def json_composite(base):
    return st.recursive(
        base,
        lambda children: st.one_of(
            st.lists(children, max_size=10),
            st.dictionaries(st.text(min_size=1, max_size=20), children, max_size=10)
        ),
        max_leaves=50
    )

json_data = json_composite(json_primitives)

# Test 1: JSON round-trip property
@given(json_data)
@settings(max_examples=200)
def test_json_round_trip(data):
    """Test that json_loads(json_dumps(x)) == x"""
    serialized = srsly.json_dumps(data)
    deserialized = srsly.json_loads(serialized)
    assert deserialized == data

# Test 2: JSON round-trip with sorting
@given(json_data)
@settings(max_examples=100)
def test_json_round_trip_with_sort(data):
    """Test that json_loads(json_dumps(x, sort_keys=True)) == x"""
    serialized = srsly.json_dumps(data, sort_keys=True)
    deserialized = srsly.json_loads(serialized)
    assert deserialized == data

# Test 3: msgpack round-trip property
@given(json_data)
@settings(max_examples=200)
def test_msgpack_round_trip(data):
    """Test that msgpack_loads(msgpack_dumps(x)) == x"""
    serialized = srsly.msgpack_dumps(data)
    deserialized = srsly.msgpack_loads(serialized)
    assert deserialized == data

# Test 4: msgpack with use_list=False should preserve tuples vs lists
@given(st.lists(st.integers(), min_size=0, max_size=10))
@settings(max_examples=100)
def test_msgpack_use_list_false(data):
    """Test that msgpack with use_list=False returns tuples instead of lists"""
    # Convert list to tuple for testing
    tuple_data = tuple(data)
    serialized = srsly.msgpack_dumps(tuple_data)
    
    # With use_list=True (default), should get list back
    with_list = srsly.msgpack_loads(serialized, use_list=True)
    assert isinstance(with_list, list)
    assert list(with_list) == list(tuple_data)
    
    # With use_list=False, should get tuple back
    without_list = srsly.msgpack_loads(serialized, use_list=False)
    assert isinstance(without_list, tuple)
    assert without_list == tuple_data

# Test 5: YAML round-trip property
@given(json_data)
@settings(max_examples=200)
def test_yaml_round_trip(data):
    """Test that yaml_loads(yaml_dumps(x)) == x"""
    serialized = srsly.yaml_dumps(data)
    deserialized = srsly.yaml_loads(serialized)
    assert deserialized == data

# Test 6: Pickle round-trip property
@given(json_data)
@settings(max_examples=200)
def test_pickle_round_trip(data):
    """Test that pickle_loads(pickle_dumps(x)) == x"""
    serialized = srsly.pickle_dumps(data)
    deserialized = srsly.pickle_loads(serialized)
    assert deserialized == data

# Test 7: is_json_serializable correctness
@given(json_data)
@settings(max_examples=100)
def test_is_json_serializable_true(data):
    """Test that is_json_serializable returns True for valid JSON data"""
    assert srsly.is_json_serializable(data) is True

@given(st.one_of(
    st.functions(),
    st.builds(lambda: lambda x: x),
    st.builds(set, st.lists(st.integers(), min_size=1)),
    st.builds(bytes, st.binary(min_size=1, max_size=100))
))
@settings(max_examples=50)
def test_is_json_serializable_false(data):
    """Test that is_json_serializable returns False for non-JSON data"""
    assert srsly.is_json_serializable(data) is False

# Test 8: File I/O round-trips for JSON
@given(json_data)
@settings(max_examples=100)
def test_json_file_round_trip(data):
    """Test writing and reading JSON files preserves data"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        srsly.write_json(temp_path, data)
        loaded = srsly.read_json(temp_path)
        assert loaded == data
    finally:
        os.unlink(temp_path)

# Test 9: JSONL file round-trip
@given(st.lists(json_data, min_size=0, max_size=20))
@settings(max_examples=50)
def test_jsonl_file_round_trip(lines):
    """Test writing and reading JSONL files preserves data"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        temp_path = f.name
    
    try:
        srsly.write_jsonl(temp_path, lines)
        loaded = list(srsly.read_jsonl(temp_path))
        assert loaded == lines
    finally:
        os.unlink(temp_path)

# Test 10: json_loads("-") should raise ValueError
def test_json_loads_dash_raises():
    """Test that json_loads("-") raises ValueError as documented"""
    with pytest.raises(ValueError, match="Expected object or value"):
        srsly.json_loads("-")

# Test 11: Test bytes input for json_loads
@given(json_data)
@settings(max_examples=100)
def test_json_loads_bytes_input(data):
    """Test that json_loads works with bytes input"""
    json_str = srsly.json_dumps(data)
    json_bytes = json_str.encode('utf-8')
    deserialized = srsly.json_loads(json_bytes)
    assert deserialized == data

# Test 12: Cross-format serialization compatibility
@given(json_data)
@settings(max_examples=50)
def test_cross_format_compatibility(data):
    """Test that data serialized in one format can be represented in another"""
    # Serialize with JSON
    json_str = srsly.json_dumps(data)
    json_loaded = srsly.json_loads(json_str)
    
    # Serialize the JSON-loaded data with msgpack
    msgpack_bytes = srsly.msgpack_dumps(json_loaded)
    msgpack_loaded = srsly.msgpack_loads(msgpack_bytes)
    
    # Serialize the msgpack-loaded data with YAML
    yaml_str = srsly.yaml_dumps(msgpack_loaded)
    yaml_loaded = srsly.yaml_loads(yaml_str)
    
    # All should be equal
    assert json_loaded == msgpack_loaded == yaml_loaded == data

# Test 13: Unicode handling in JSON
@given(st.text(alphabet="🦄🎉📚💻🌟✨", min_size=1, max_size=50))
@settings(max_examples=100)
def test_json_unicode_handling(text):
    """Test that JSON properly handles Unicode characters"""
    data = {"unicode_key": text, text: "value"}
    serialized = srsly.json_dumps(data)
    deserialized = srsly.json_loads(serialized)
    assert deserialized == data

# Test 14: Large integer handling
@given(st.integers())
@settings(max_examples=100)
def test_json_integer_handling(num):
    """Test JSON handling of various integers"""
    if abs(num) > 10**15:
        # JSON might have precision issues with very large integers
        assume(False)
    
    serialized = srsly.json_dumps(num)
    deserialized = srsly.json_loads(serialized)
    assert deserialized == num

# Test 15: Edge case - empty containers
@given(st.one_of(
    st.just([]),
    st.just({}),
    st.just(""),
))
@settings(max_examples=50)
def test_empty_containers(data):
    """Test serialization of empty containers"""
    # JSON
    json_serialized = srsly.json_dumps(data)
    json_deserialized = srsly.json_loads(json_serialized)
    assert json_deserialized == data
    
    # msgpack
    msgpack_serialized = srsly.msgpack_dumps(data)
    msgpack_deserialized = srsly.msgpack_loads(msgpack_serialized)
    assert msgpack_deserialized == data
    
    # YAML
    yaml_serialized = srsly.yaml_dumps(data)
    yaml_deserialized = srsly.yaml_loads(yaml_serialized)
    assert yaml_deserialized == data