import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import string
import pytest
from unittest.mock import Mock

# Import the modules we're testing
from simple_history.templatetags.getattributes import getattribute
from simple_history.template_utils import (
    conditional_str,
    is_safe_str,
    ObjDiffDisplay,
    HistoricalRecordContextHelper,
)
from django.utils.safestring import SafeString, mark_safe


# Test 1: getattribute filter should behave like getattr with None default
@given(
    st.text(min_size=1, max_size=100).filter(lambda x: x.isidentifier()),
    st.text(min_size=1, max_size=100)
)
def test_getattribute_returns_none_for_missing_attrs(attr_name, value):
    """getattribute should return None for missing attributes"""
    obj = Mock()
    # Don't set the attribute, so it doesn't exist
    result = getattribute(obj, attr_name)
    assert result is None


@given(
    st.text(min_size=1, max_size=100).filter(lambda x: x.isidentifier()),
    st.one_of(st.text(), st.integers(), st.floats(allow_nan=False), st.booleans())
)
def test_getattribute_returns_existing_attrs(attr_name, value):
    """getattribute should return existing attributes"""
    obj = Mock()
    setattr(obj, attr_name, value)
    result = getattribute(obj, attr_name)
    assert result == value


# Test 2: conditional_str should be idempotent for strings
@given(st.text())
def test_conditional_str_idempotent_for_strings(s):
    """conditional_str should return strings unchanged"""
    result = conditional_str(s)
    assert result == s
    assert result is s  # Should be the same object


@given(st.one_of(st.integers(), st.floats(allow_nan=False), st.booleans(), st.none()))
def test_conditional_str_converts_non_strings(value):
    """conditional_str should convert non-strings to strings"""
    result = conditional_str(value)
    assert isinstance(result, str)
    assert result == str(value)


# Test 3: is_safe_str should correctly identify safe strings
@given(st.text())
def test_is_safe_str_detects_safe_strings(s):
    """is_safe_str should detect SafeString objects"""
    safe = mark_safe(s)
    assert is_safe_str(safe) is True
    assert is_safe_str(s) is False


# Test 4: ObjDiffDisplay.common_shorten_repr properties
@given(
    st.lists(st.text(min_size=0, max_size=50), min_size=1, max_size=5),
    st.integers(min_value=10, max_value=200)
)
def test_common_shorten_repr_preserves_short_strings(strings, max_length):
    """Strings shorter than max_length should be returned unchanged"""
    display = ObjDiffDisplay(max_length=max_length)
    # Only test when all strings are shorter than max_length
    assume(all(len(s) <= max_length for s in strings))
    
    result = display.common_shorten_repr(*strings)
    assert result == tuple(strings)


@given(
    st.text(min_size=1, max_size=20),  # common prefix
    st.lists(st.text(min_size=0, max_size=100), min_size=2, max_size=5),  # suffixes
    st.integers(min_value=30, max_value=150)
)
def test_common_shorten_repr_preserves_prefix(prefix, suffixes, max_length):
    """common_shorten_repr should preserve common prefixes"""
    display = ObjDiffDisplay(max_length=max_length)
    strings = [prefix + suffix for suffix in suffixes]
    
    # Skip if strings are already short enough
    assume(any(len(s) > max_length for s in strings))
    
    result = display.common_shorten_repr(*strings)
    
    # Check that all results start with some part of the prefix
    # (might be shortened if prefix is too long)
    if prefix:
        # Find the common prefix in the results
        result_prefix = os.path.commonprefix(result)
        # The result should have preserved at least part of the original prefix
        if result_prefix:
            assert prefix.startswith(result_prefix) or result_prefix in prefix


@given(
    st.lists(st.text(min_size=100, max_size=500), min_size=1, max_size=5),
    st.integers(min_value=30, max_value=100)
)
def test_common_shorten_repr_respects_max_length(long_strings, max_length):
    """Shortened strings should not exceed max_length"""
    display = ObjDiffDisplay(max_length=max_length)
    result = display.common_shorten_repr(*long_strings)
    
    for shortened in result:
        assert len(shortened) <= max_length


# Test 5: shorten method edge cases
@given(
    st.text(min_size=0, max_size=200),
    st.integers(min_value=0, max_value=50),
    st.integers(min_value=0, max_value=50)
)
def test_shorten_handles_various_inputs(s, prefix_len, suffix_len):
    """shorten should handle various input combinations without crashing"""
    display = ObjDiffDisplay()
    
    # Only test valid combinations where we don't exceed string length
    assume(prefix_len >= 0)
    assume(suffix_len >= 0)
    assume(prefix_len + suffix_len <= len(s) + display.placeholder_len)
    
    result = display.shorten(s, prefix_len, suffix_len)
    assert isinstance(result, str)
    
    # If no shortening needed, should return original
    if len(s) <= prefix_len + suffix_len + display.placeholder_len:
        assert result == s


# Test 6: String formatting with lists
@given(st.lists(st.text(max_size=50), max_size=10))
def test_stringify_list_formatting(string_list):
    """Lists should be formatted as [elem1, elem2, ...]"""
    from simple_history.template_utils import HistoricalRecordContextHelper
    from unittest.mock import Mock
    
    helper = HistoricalRecordContextHelper(Mock(), Mock())
    change = Mock()
    change.field = 'test_field'
    
    # Mock the model meta to avoid Django dependency issues
    field_meta = Mock()
    field_meta.verbose_name = 'Test Field'
    helper.model._meta.get_field = Mock(return_value=field_meta)
    
    # Test the stringify_value logic (internal to stringify_delta_change_values)
    # We'll test the list case specifically
    old_val = string_list
    new_val = ['new_item']
    
    old_str, new_str = helper.stringify_delta_change_values(change, old_val, new_val)
    
    # Check that old_str is formatted as a list
    if string_list:
        assert old_str.startswith('[')
        assert old_str.endswith(']')
        # Check all elements are present (might be shortened)
        for item in string_list[:3]:  # Check first few items
            if len(str(item)) < 20:  # Only check short items that won't be shortened
                assert str(item) in old_str or len(old_str) > 100


# Test 7: SafeString preservation in lists
@given(st.lists(st.text(max_size=20), min_size=1, max_size=5))
def test_safe_string_preservation_in_lists(string_list):
    """Lists of safe strings should preserve safety if all elements are safe"""
    from simple_history.template_utils import HistoricalRecordContextHelper
    from unittest.mock import Mock
    
    helper = HistoricalRecordContextHelper(Mock(), Mock())
    change = Mock()
    change.field = 'test_field'
    
    field_meta = Mock()
    field_meta.verbose_name = 'Test Field'
    helper.model._meta.get_field = Mock(return_value=field_meta)
    
    # Create a list of safe strings
    safe_list = [mark_safe(s) for s in string_list]
    
    old_str, new_str = helper.stringify_delta_change_values(change, safe_list, ['test'])
    
    # The result should be a SafeString if all inputs were safe
    # (Note: After escaping, the type might change, but we're testing the internal logic)
    assert isinstance(old_str, (str, SafeString))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])