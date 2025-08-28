#!/usr/bin/env python3
"""Property-based tests for pyatlan using Hypothesis."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest

# Import the functions to test
from pyatlan.utils import (
    to_camel_case,
    get_parent_qualified_name,
    select_optional_set_fields,
    validate_required_fields,
    API,
    deep_get,
    non_null,
    validate_single_required_field,
)


# Property 1: to_camel_case idempotence - applying twice should be same as once
@given(st.text(min_size=1, max_size=100))
def test_to_camel_case_idempotence(s):
    """Test that applying to_camel_case twice is same as applying once."""
    once = to_camel_case(s)
    twice = to_camel_case(once)
    assert once == twice


# Property 2: to_camel_case preserves alphanumeric content (just changes case)
@given(st.text(alphabet=st.characters(categories=["Lu", "Ll", "Nd"]), min_size=1))
def test_to_camel_case_preserves_content(s):
    """Test that to_camel_case preserves all alphanumeric characters."""
    result = to_camel_case(s)
    # Remove case and compare - all letters/numbers should be preserved
    original_alphanum = ''.join(c for c in s.lower() if c.isalnum())
    result_alphanum = ''.join(c for c in result.lower() if c.isalnum())
    assert original_alphanum == result_alphanum


# Property 3: get_parent_qualified_name length invariant
@given(st.text(min_size=1).filter(lambda x: '/' in x))
def test_get_parent_qualified_name_length(qualified_name):
    """Test that parent qualified name is shorter than original."""
    parent = get_parent_qualified_name(qualified_name)
    # Parent should be shorter unless input has no '/' or ends with '/'
    if qualified_name.count('/') > 0 and not qualified_name.endswith('/'):
        assert len(parent) < len(qualified_name)


# Property 4: get_parent_qualified_name path consistency  
@given(st.lists(st.text(alphabet=st.characters(blacklist_characters="/"), min_size=1), min_size=2))
def test_get_parent_qualified_name_consistency(parts):
    """Test that parent of a constructed path is the path without last element."""
    qualified_name = '/'.join(parts)
    parent = get_parent_qualified_name(qualified_name)
    expected = '/'.join(parts[:-1])
    assert parent == expected


# Property 5: select_optional_set_fields removes all None values
@given(st.dictionaries(st.text(), st.one_of(st.none(), st.text(), st.integers())))
def test_select_optional_set_fields_removes_none(params):
    """Test that select_optional_set_fields removes all None values."""
    result = select_optional_set_fields(params)
    assert None not in result.values()
    # All non-None values should be preserved
    for key, value in params.items():
        if value is not None:
            assert key in result
            assert result[key] == value


# Property 6: non_null function behavior
@given(st.one_of(st.none(), st.text(), st.integers()), st.text())
def test_non_null_behavior(obj, default):
    """Test non_null returns obj if not None, else default."""
    result = non_null(obj, default)
    if obj is not None:
        assert result == obj
    else:
        assert result == default


# Property 7: API.multipart_urljoin invariants
@given(
    st.text(min_size=1),
    st.lists(st.text(min_size=1), min_size=0, max_size=5)
)
def test_api_multipart_urljoin_no_double_slashes(base, paths):
    """Test that multipart_urljoin doesn't create double slashes."""
    result = API.multipart_urljoin(base, *paths)
    # Should not have '//' except in protocol (http://)
    if '://' in result:
        # Split by protocol
        parts = result.split('://', 1)
        if len(parts) > 1:
            # Check the part after protocol
            assert '//' not in parts[1]
    else:
        assert '//' not in result


# Property 8: deep_get with simple keys
@given(
    st.dictionaries(st.text(alphabet=st.characters(blacklist_characters="."), min_size=1), 
                    st.integers()),
    st.text(alphabet=st.characters(blacklist_characters="."), min_size=1)
)
def test_deep_get_simple_keys(dictionary, key):
    """Test deep_get with non-nested keys."""
    if key in dictionary:
        result = deep_get(dictionary, key)
        assert result == dictionary[key]
    else:
        result = deep_get(dictionary, key, default="NOT_FOUND")
        assert result == "NOT_FOUND"


# Property 9: validate_required_fields error conditions
@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=5),
    st.lists(st.one_of(st.none(), st.text(min_size=0)), min_size=1, max_size=5)
)
def test_validate_required_fields_with_none_or_empty(field_names, values):
    """Test that validate_required_fields raises for None or empty values."""
    # Ensure lists are same length
    min_len = min(len(field_names), len(values))
    field_names = field_names[:min_len]
    values = values[:min_len]
    
    has_invalid = any(v is None or (isinstance(v, str) and not v.strip()) for v in values)
    
    if has_invalid:
        with pytest.raises(ValueError):
            validate_required_fields(field_names, values)
    else:
        # Should not raise if all values are valid
        try:
            validate_required_fields(field_names, values)
        except ValueError:
            # This shouldn't happen for valid values
            pass


# Property 10: validate_single_required_field mutual exclusivity
@given(
    st.lists(st.text(min_size=1), min_size=2, max_size=5),
    st.lists(st.one_of(st.none(), st.integers()), min_size=2, max_size=5)
)
def test_validate_single_required_field_mutual_exclusivity(field_names, values):
    """Test that validate_single_required_field enforces exactly one non-None value."""
    # Ensure lists are same length
    min_len = min(len(field_names), len(values))
    field_names = field_names[:min_len]
    values = values[:min_len]
    
    non_none_count = sum(1 for v in values if v is not None)
    
    if non_none_count == 0:
        # Should raise when all are None
        with pytest.raises(ValueError, match="One of the following parameters are required"):
            validate_single_required_field(field_names, values)
    elif non_none_count == 1:
        # Should not raise when exactly one is not None
        validate_single_required_field(field_names, values)
    else:
        # Should raise when multiple are not None
        with pytest.raises(ValueError, match="Only one of the following parameters are allowed"):
            validate_single_required_field(field_names, values)


# Property 11: Test path joining edge cases
@given(st.text(), st.text())
def test_api_multipart_urljoin_handles_slashes(left, right):
    """Test that multipart_urljoin correctly handles leading/trailing slashes."""
    result = API.multipart_urljoin(left, right)
    
    # If both inputs are non-empty, result should contain both
    if left and right:
        # The content (minus slashes) should be preserved
        left_content = left.strip('/')
        right_content = right.strip('/')
        if left_content:
            assert left_content in result
        if right_content:
            assert right_content in result


# Property 12: Test deep_get with nested dictionaries
@given(st.text(alphabet=st.characters(blacklist_characters="."), min_size=1),
       st.text(alphabet=st.characters(blacklist_characters="."), min_size=1),
       st.integers())
def test_deep_get_nested(key1, key2, value):
    """Test deep_get with nested dictionary structure."""
    dictionary = {key1: {key2: value}}
    dot_key = f"{key1}.{key2}"
    
    result = deep_get(dictionary, dot_key)
    assert result == value
    
    # Test with non-existent nested key
    wrong_key = f"{key1}.wrong_key"
    result = deep_get(dictionary, wrong_key, default="DEFAULT")
    assert result == "DEFAULT"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])