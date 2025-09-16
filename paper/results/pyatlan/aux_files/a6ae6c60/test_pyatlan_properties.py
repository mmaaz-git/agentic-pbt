#!/usr/bin/env python3
"""
Property-based tests for pyatlan.client module using Hypothesis.
Testing utility functions and client behavior for bugs.
"""

import string
import sys
from hypothesis import given, assume, strategies as st, settings
import pytest

sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages/')

from pyatlan.utils import (
    to_camel_case, 
    get_parent_qualified_name,
    validate_required_fields,
    deep_get,
    API,
    HTTPMethod,
    EndPoint
)


# Test 1: to_camel_case idempotence property
@given(st.text(min_size=1, max_size=100))
def test_to_camel_case_idempotence(s):
    """Applying to_camel_case twice should be the same as applying once."""
    once = to_camel_case(s)
    twice = to_camel_case(once)
    assert once == twice, f"Not idempotent: {s} -> {once} -> {twice}"


# Test 2: to_camel_case no spaces in output
@given(st.text(alphabet=string.ascii_letters + string.digits + "_- ", min_size=1))
def test_to_camel_case_no_spaces(s):
    """Result should never contain spaces."""
    result = to_camel_case(s)
    assert " " not in result, f"Result contains spaces: '{result}' from '{s}'"


# Test 3: to_camel_case first character lowercase
@given(st.text(alphabet=string.ascii_letters + "_-", min_size=1))
def test_to_camel_case_first_char_lowercase(s):
    """First character should be lowercase if result is non-empty."""
    result = to_camel_case(s)
    if result:  # Only check if result is non-empty
        assert result[0].islower() or not result[0].isalpha(), \
            f"First char not lowercase: '{result[0]}' in '{result}'"


# Test 4: get_parent_qualified_name length property
@given(st.text(min_size=1).filter(lambda x: "/" in x))
def test_get_parent_qualified_name_length(qualified_name):
    """Parent qualified name should be shorter than original."""
    parent = get_parent_qualified_name(qualified_name)
    assert len(parent) <= len(qualified_name), \
        f"Parent longer than original: '{parent}' vs '{qualified_name}'"


# Test 5: get_parent_qualified_name preserves path structure
@given(
    st.lists(
        st.text(alphabet=string.ascii_letters + string.digits, min_size=1),
        min_size=2,
        max_size=10
    )
)
def test_get_parent_qualified_name_structure(segments):
    """Building a path and getting parent should give expected result."""
    qualified_name = "/".join(segments)
    parent = get_parent_qualified_name(qualified_name)
    expected_parent = "/".join(segments[:-1])
    assert parent == expected_parent, \
        f"Unexpected parent: got '{parent}', expected '{expected_parent}'"


# Test 6: validate_required_fields with None values
@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=5),
    st.integers(min_value=0)
)
def test_validate_required_fields_none_raises(field_names, none_index):
    """None values should always raise ValueError."""
    assume(none_index < len(field_names))
    values = ["valid"] * len(field_names)
    values[none_index] = None
    
    with pytest.raises(ValueError, match=f"{field_names[none_index]} is required"):
        validate_required_fields(field_names, values)


# Test 7: validate_required_fields with empty strings
@given(
    st.lists(st.text(alphabet=string.ascii_letters, min_size=1), min_size=1, max_size=5),
    st.integers(min_value=0)
)
def test_validate_required_fields_empty_string_raises(field_names, empty_index):
    """Empty strings should raise ValueError."""
    assume(empty_index < len(field_names))
    values = ["valid"] * len(field_names)
    values[empty_index] = "   "  # Blank string
    
    with pytest.raises(ValueError, match=f"{field_names[empty_index]} cannot be blank"):
        validate_required_fields(field_names, values)


# Test 8: validate_required_fields with empty lists
@given(
    st.lists(st.text(alphabet=string.ascii_letters, min_size=1), min_size=1, max_size=5),
    st.integers(min_value=0)
)
def test_validate_required_fields_empty_list_raises(field_names, empty_index):
    """Empty lists should raise ValueError."""
    assume(empty_index < len(field_names))
    values = [["valid"]] * len(field_names)
    values[empty_index] = []
    
    with pytest.raises(ValueError, match=f"{field_names[empty_index]} cannot be an empty list"):
        validate_required_fields(field_names, values)


# Test 9: validate_required_fields with valid values
@given(
    st.lists(st.text(alphabet=string.ascii_letters, min_size=1), min_size=1, max_size=5),
    st.lists(st.text(min_size=1), min_size=1, max_size=5)
)
def test_validate_required_fields_valid_passes(field_names, values):
    """Valid non-empty values should not raise errors."""
    assume(len(field_names) == len(values))
    # This should not raise any exception
    validate_required_fields(field_names, values)


# Test 10: deep_get with simple keys
@given(
    st.text(alphabet=string.ascii_letters, min_size=1),
    st.one_of(st.text(), st.integers(), st.floats(allow_nan=False))
)
def test_deep_get_simple_key(key, value):
    """deep_get with single key should return the value."""
    dictionary = {key: value}
    result = deep_get(dictionary, key)
    assert result == value, f"Expected {value}, got {result}"


# Test 11: deep_get with nested keys
@given(
    st.text(alphabet=string.ascii_letters, min_size=1),
    st.text(alphabet=string.ascii_letters, min_size=1),
    st.one_of(st.text(), st.integers(), st.floats(allow_nan=False))
)
def test_deep_get_nested_keys(key1, key2, value):
    """deep_get with nested keys should work with dot notation."""
    assume(key1 != key2)  # Ensure different keys
    dictionary = {key1: {key2: value}}
    result = deep_get(dictionary, f"{key1}.{key2}")
    assert result == value, f"Expected {value}, got {result}"


# Test 12: deep_get with missing keys returns default
@given(
    st.dictionaries(st.text(min_size=1), st.text()),
    st.text(min_size=1),
    st.text()
)
def test_deep_get_missing_key_returns_default(dictionary, missing_key, default):
    """deep_get with non-existent key should return default."""
    assume(missing_key not in dictionary)
    result = deep_get(dictionary, missing_key, default)
    assert result == default, f"Expected default {default}, got {result}"


# Test 13: API.multipart_urljoin preserves base structure
@given(
    st.text(alphabet=string.ascii_letters + ":/", min_size=5).filter(lambda x: "://" in x),
    st.lists(st.text(alphabet=string.ascii_letters + string.digits, min_size=1), min_size=1, max_size=3)
)
def test_api_multipart_urljoin_preserves_scheme(base_url, paths):
    """multipart_urljoin should preserve URL scheme."""
    result = API.multipart_urljoin(base_url, *paths)
    if "://" in base_url:
        scheme = base_url.split("://")[0]
        assert result.startswith(scheme + "://"), \
            f"Scheme not preserved: {base_url} -> {result}"


# Test 14: API.multipart_urljoin handles slashes correctly
@given(
    st.text(alphabet=string.ascii_letters, min_size=1),
    st.text(alphabet=string.ascii_letters, min_size=1)
)
def test_api_multipart_urljoin_single_slash(left, right):
    """Should join with exactly one slash between segments."""
    # Test various combinations of trailing/leading slashes
    for left_suffix in ["", "/"]:
        for right_prefix in ["", "/"]:
            test_left = left + left_suffix
            test_right = right_prefix + right
            result = API.multipart_urljoin(test_left, test_right)
            # Count slashes between the two parts
            expected = f"{left}/{right}"
            assert expected in result or result == expected, \
                f"Unexpected join: '{test_left}' + '{test_right}' = '{result}'"


# Test 15: Testing round-trip property for get_parent_qualified_name
@given(
    st.lists(
        st.text(alphabet=string.ascii_letters + string.digits, min_size=1),
        min_size=1,
        max_size=10
    ),
    st.text(alphabet=string.ascii_letters + string.digits, min_size=1)
)
def test_get_parent_qualified_name_round_trip(parent_segments, child):
    """Getting parent and adding child back should preserve structure."""
    parent_path = "/".join(parent_segments)
    full_path = f"{parent_path}/{child}"
    
    extracted_parent = get_parent_qualified_name(full_path)
    reconstructed = f"{extracted_parent}/{child}" if extracted_parent else child
    
    assert reconstructed == full_path, \
        f"Round-trip failed: '{full_path}' -> parent: '{extracted_parent}' -> '{reconstructed}'"


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))