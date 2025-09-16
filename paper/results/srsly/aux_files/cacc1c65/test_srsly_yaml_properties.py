#!/usr/bin/env python3
"""Property-based tests for srsly.ruamel_yaml module."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
import math
from srsly._yaml_api import yaml_dumps, yaml_loads, is_yaml_serializable


# Strategy for generating valid YAML data
yaml_scalars = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-2**63, max_value=2**63-1),  # YAML int range
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=0, max_size=1000),
)

# Recursive strategy for nested structures
yaml_collections = st.recursive(
    yaml_scalars,
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(
            st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),  # Non-empty keys
            children,
            max_size=10
        ),
    ),
    max_leaves=50
)


@given(yaml_collections)
@settings(max_examples=500)
def test_round_trip_property(data):
    """Test that yaml_loads(yaml_dumps(x)) = x for valid YAML data."""
    serialized = yaml_dumps(data)
    deserialized = yaml_loads(serialized)
    
    # Handle float comparison specially
    def compare_with_float_tolerance(obj1, obj2):
        if isinstance(obj1, float) and isinstance(obj2, float):
            if math.isnan(obj1):
                return math.isnan(obj2)
            return math.isclose(obj1, obj2, rel_tol=1e-9, abs_tol=1e-9)
        elif isinstance(obj1, dict) and isinstance(obj2, dict):
            if set(obj1.keys()) != set(obj2.keys()):
                return False
            return all(compare_with_float_tolerance(obj1[k], obj2[k]) for k in obj1.keys())
        elif isinstance(obj1, list) and isinstance(obj2, list):
            if len(obj1) != len(obj2):
                return False
            return all(compare_with_float_tolerance(a, b) for a, b in zip(obj1, obj2))
        else:
            return obj1 == obj2
    
    assert compare_with_float_tolerance(data, deserialized)


# Test unicode handling
unicode_strings = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Lt", "Lm", "Lo", "Nd", "Nl", "No"),
        blacklist_characters="\x00"  # YAML doesn't allow null bytes
    ),
    min_size=0,
    max_size=100
)

@given(unicode_strings)
@settings(max_examples=200)
def test_unicode_round_trip(text):
    """Test that unicode strings survive round-trip."""
    data = {"unicode_text": text, "list": [text]}
    serialized = yaml_dumps(data)
    deserialized = yaml_loads(serialized)
    assert deserialized["unicode_text"] == text
    assert deserialized["list"][0] == text


# Test complex nested structures
nested_structure = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(max_size=50),
    ),
    lambda children: st.one_of(
        st.lists(children, min_size=0, max_size=5),
        st.dictionaries(
            st.text(min_size=1, max_size=20).filter(lambda x: x.strip()),
            children,
            min_size=0,
            max_size=5
        ),
    ),
    max_leaves=30
)

@given(nested_structure)
@settings(max_examples=200)
def test_deeply_nested_round_trip(data):
    """Test round-trip with deeply nested structures."""
    serialized = yaml_dumps(data)
    deserialized = yaml_loads(serialized)
    
    # Convert both to strings for comparison to handle float precision
    assert str(data) == str(deserialized) or data == deserialized


# Test is_yaml_serializable consistency
@given(yaml_collections)
def test_is_yaml_serializable_consistency(data):
    """Test that is_yaml_serializable is consistent with actual serialization."""
    can_serialize = is_yaml_serializable(data)
    
    try:
        yaml_dumps(data)
        actual_serializable = True
    except Exception:
        actual_serializable = False
    
    assert can_serialize == actual_serializable


# Test special numeric values
special_numbers = st.one_of(
    st.just(0),
    st.just(-0.0),
    st.just(1.0),
    st.just(-1.0),
    st.floats(min_value=-1e308, max_value=1e308, allow_nan=False, allow_infinity=False),
    st.integers(min_value=-2**63, max_value=2**63-1),
)

@given(special_numbers)
def test_numeric_round_trip(num):
    """Test that numbers survive round-trip correctly."""
    data = {"number": num, "list": [num, -num if num != 0 else 0]}
    serialized = yaml_dumps(data)
    deserialized = yaml_loads(serialized)
    
    if isinstance(num, float):
        assert math.isclose(deserialized["number"], num, rel_tol=1e-9, abs_tol=1e-9)
        expected_neg = -num if num != 0 else 0
        assert math.isclose(deserialized["list"][1], expected_neg, rel_tol=1e-9, abs_tol=1e-9)
    else:
        assert deserialized["number"] == num
        assert deserialized["list"][1] == (-num if num != 0 else 0)


# Test empty collections
@given(st.one_of(
    st.just([]),
    st.just({}),
    st.lists(st.just([]), min_size=1, max_size=5),
    st.lists(st.just({}), min_size=1, max_size=5),
))
def test_empty_collections_round_trip(data):
    """Test that empty collections survive round-trip."""
    serialized = yaml_dumps(data)
    deserialized = yaml_loads(serialized)
    assert data == deserialized


# Test string edge cases
string_edge_cases = st.one_of(
    st.just(""),
    st.just(" "),
    st.just("\n"),
    st.just("\t"),
    st.just("  leading spaces"),
    st.just("trailing spaces  "),
    st.text(alphabet=" \n\t", min_size=1, max_size=10),  # Whitespace only
    st.text().filter(lambda x: "\n" in x or "\t" in x),  # Contains newlines/tabs
)

@given(string_edge_cases)
def test_string_edge_cases_round_trip(text):
    """Test that string edge cases survive round-trip."""
    data = {"text": text}
    serialized = yaml_dumps(data)
    deserialized = yaml_loads(serialized)
    assert deserialized["text"] == text


# Test dictionary with various key types
dict_keys = st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and x != "")

@given(st.dictionaries(dict_keys, st.integers(), min_size=0, max_size=20))
def test_dictionary_keys_round_trip(data):
    """Test that dictionaries with string keys survive round-trip."""
    serialized = yaml_dumps(data)
    deserialized = yaml_loads(serialized)
    assert data == deserialized


# Test sorting behavior
@given(st.dictionaries(
    st.text(min_size=1, max_size=10).filter(lambda x: x.strip()),
    st.integers(),
    min_size=2,
    max_size=10
))
def test_sort_keys_property(data):
    """Test that sort_keys parameter works correctly."""
    # With sorting
    sorted_yaml = yaml_dumps(data, sort_keys=True)
    # Without sorting  
    unsorted_yaml = yaml_dumps(data, sort_keys=False)
    
    # Both should deserialize to the same data
    assert yaml_loads(sorted_yaml) == data
    assert yaml_loads(unsorted_yaml) == data
    
    # Sorted version should have keys in order
    if len(data) > 1:
        sorted_keys = sorted(data.keys())
        lines = sorted_yaml.strip().split('\n')
        yaml_keys = [line.split(':')[0] for line in lines if ':' in line]
        assert yaml_keys == sorted_keys


if __name__ == "__main__":
    pytest.main([__file__, "-v"])