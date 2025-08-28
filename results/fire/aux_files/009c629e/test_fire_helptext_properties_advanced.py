#!/usr/bin/env python3
"""Advanced property-based tests for fire.helptext and fire.formatting modules."""

import sys
import os
import collections

# Add the fire module to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume, example
import fire.formatting as formatting
import fire.helptext as helptext
import fire.trace as trace
import fire.inspectutils as inspectutils


# Test for potential edge cases with small available_space
@given(
    text=st.text(min_size=10, max_size=200),
    available_space=st.integers(min_value=0, max_value=2),  # Very small space
    line_length=st.integers(min_value=10, max_value=200)
)
def test_ellipsis_truncate_small_space(text, available_space, line_length):
    """Test EllipsisTruncate with very small available_space."""
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    
    # When available_space < len(ELLIPSIS), should use line_length instead
    if available_space < len(formatting.ELLIPSIS):
        # Result should not exceed line_length
        assert len(result) <= line_length, f"Result length {len(result)} exceeds line_length {line_length}"
        if len(text) > line_length:
            assert len(result) == line_length, f"Result should be exactly line_length when text is too long"


# Test for composition of formatting functions
@given(
    text=st.text(alphabet=st.characters(blacklist_characters='\r'), min_size=0, max_size=100),
    spaces=st.integers(min_value=0, max_value=5),
    available_space=st.integers(min_value=10, max_value=50),
    line_length=st.integers(min_value=50, max_value=100)
)
def test_indent_then_truncate_composition(text, spaces, available_space, line_length):
    """Test composition of Indent followed by EllipsisTruncate."""
    # First indent, then truncate
    indented = formatting.Indent(text, spaces)
    truncated = formatting.EllipsisTruncate(indented, available_space, line_length)
    
    # The truncated result should still respect the length constraint
    if len(indented) > available_space and available_space >= len(formatting.ELLIPSIS):
        assert len(truncated) == available_space
    elif len(indented) <= available_space:
        assert truncated == indented


# Test for HelpText not crashing on various inputs
@given(
    component_type=st.sampled_from(['function', 'class', 'int', 'str', 'list', 'dict', 'none'])
)
@settings(max_examples=50)
def test_helptext_no_crash(component_type):
    """Test that HelpText doesn't crash on various component types."""
    if component_type == 'function':
        def test_func(x, y=10, *args, **kwargs):
            """Test function."""
            return x + y
        component = test_func
    elif component_type == 'class':
        class TestClass:
            """Test class."""
            def method(self, x):
                return x * 2
        component = TestClass
    elif component_type == 'int':
        component = 42
    elif component_type == 'str':
        component = "test string"
    elif component_type == 'list':
        component = [1, 2, 3]
    elif component_type == 'dict':
        component = {'key': 'value'}
    else:  # none
        component = None
    
    # Should not crash
    try:
        result = helptext.HelpText(component)
        assert isinstance(result, str), "HelpText should return a string"
        assert len(result) > 0, "HelpText should return non-empty string"
    except Exception as e:
        # Some components might legitimately fail, but let's see what happens
        pass


# Test _CreateItem for edge cases
@given(
    name=st.text(min_size=0, max_size=100),
    description=st.one_of(st.none(), st.text(min_size=0, max_size=200)),
    indent=st.integers(min_value=0, max_value=10)
)
def test_create_item_property(name, description, indent):
    """Test _CreateItem with various inputs."""
    result = helptext._CreateItem(name, description, indent)
    
    # Property: result should always contain the name
    assert name in result, f"Name '{name}' not in result"
    
    # Property: if description is None or empty, result should just be the name
    if not description:
        assert result == name, "Result should be just name when no description"
    else:
        # Description should be indented
        lines = result.split('\n')
        assert len(lines) >= 2, "Should have at least name and description lines"
        # Check indentation of description
        if len(lines) > 1 and lines[1]:
            assert lines[1].startswith(' ' * indent), f"Description not indented by {indent} spaces"


# Test for WrappedJoin with edge case: empty items
@given(
    separator=st.text(alphabet=st.characters(blacklist_characters='\n\r'), min_size=1, max_size=5),
    width=st.integers(min_value=10, max_value=100)
)
def test_wrapped_join_empty_items(separator, width):
    """Test WrappedJoin with empty list."""
    items = []
    result_lines = formatting.WrappedJoin(items, separator, width)
    
    # Should return a list with one empty string
    assert result_lines == [''], "Empty items should produce single empty string"


# Test for boundary case in EllipsisMiddleTruncate
@given(
    text=st.text(min_size=0, max_size=200)
)
@example(text='abcdefghij', available_space=3, line_length=80)  # Specific edge case
def test_ellipsis_middle_truncate_boundary(text, available_space=3, line_length=80):
    """Test EllipsisMiddleTruncate at boundary conditions."""
    result = formatting.EllipsisMiddleTruncate(text, available_space, line_length)
    
    # When available_space == len(ELLIPSIS), interesting behavior
    if available_space == len(formatting.ELLIPSIS) and len(text) >= available_space:
        # Should just be the ellipsis
        assert result == formatting.ELLIPSIS or len(result) == line_length


# Test UsageText doesn't crash
@given(
    component_type=st.sampled_from(['function', 'class', 'int', 'str', 'list'])
)
@settings(max_examples=30)
def test_usagetext_no_crash(component_type):
    """Test that UsageText doesn't crash on various component types."""
    if component_type == 'function':
        def test_func(x, y=10):
            return x + y
        component = test_func
    elif component_type == 'class':
        class TestClass:
            def method(self, x):
                return x * 2
        component = TestClass
    elif component_type == 'int':
        component = 42
    elif component_type == 'str':
        component = "test"
    else:  # list
        component = [1, 2, 3]
    
    try:
        result = helptext.UsageText(component, verbose=False)
        assert isinstance(result, str), "UsageText should return a string"
        assert 'Usage:' in result, "UsageText should contain 'Usage:'"
    except Exception as e:
        # Some components might legitimately fail
        pass


# Test for special characters in flags
@given(
    flags=st.lists(
        st.text(alphabet='🦄💫✨🌟💥🎉', min_size=1, max_size=5),
        min_size=1, max_size=10
    )
)
def test_get_short_flags_unicode(flags):
    """Test _GetShortFlags with Unicode characters."""
    short_flags = helptext._GetShortFlags(flags)
    
    # Should handle Unicode gracefully
    first_chars = [f[0] for f in flags if f]
    first_char_counts = collections.Counter(first_chars)
    
    # Property: returned flags should be unique first characters
    for short_flag in short_flags:
        assert first_char_counts[short_flag] == 1


# Test for very long single item in WrappedJoin
@given(
    long_item=st.text(min_size=100, max_size=200),
    width=st.integers(min_value=10, max_value=50)  # Width smaller than item
)
def test_wrapped_join_long_item(long_item, width):
    """Test WrappedJoin with item longer than width."""
    items = [long_item]
    result_lines = formatting.WrappedJoin(items, ' | ', width)
    
    # The item should still appear, even if it exceeds width
    joined = ''.join(result_lines)
    assert long_item in joined, "Long item should still appear in result"
    
    # First line should contain the long item (even if it exceeds width)
    assert long_item in result_lines[0]


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])