#!/usr/bin/env python3
"""Property-based tests for fire.helptext and fire.formatting modules."""

import sys
import os
import collections

# Add the fire module to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import fire.formatting as formatting
import fire.helptext as helptext


# Test 1: EllipsisTruncate length invariant
@given(
    text=st.text(min_size=0, max_size=200),
    available_space=st.integers(min_value=0, max_value=100),
    line_length=st.integers(min_value=10, max_value=200)
)
def test_ellipsis_truncate_length_invariant(text, available_space, line_length):
    """Test that EllipsisTruncate never exceeds available_space."""
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    
    # Property: if text is longer than available_space and available_space >= len(ELLIPSIS),
    # then result length should be exactly available_space
    if len(text) > available_space and available_space >= len(formatting.ELLIPSIS):
        assert len(result) == available_space, f"Result length {len(result)} exceeds available_space {available_space}"
    
    # Property: if text fits, it should be returned unchanged
    if len(text) <= available_space:
        assert result == text, "Text that fits should be returned unchanged"
    
    # Property: when truncation occurs, ellipsis should be present
    if len(text) > available_space and available_space >= len(formatting.ELLIPSIS):
        assert result.endswith(formatting.ELLIPSIS), "Truncated text should end with ellipsis"


# Test 2: EllipsisMiddleTruncate length invariant
@given(
    text=st.text(min_size=0, max_size=200),
    available_space=st.integers(min_value=0, max_value=100),
    line_length=st.integers(min_value=10, max_value=200)
)
def test_ellipsis_middle_truncate_length_invariant(text, available_space, line_length):
    """Test that EllipsisMiddleTruncate never exceeds available_space."""
    result = formatting.EllipsisMiddleTruncate(text, available_space, line_length)
    
    # Property: if text is longer than available_space and available_space >= len(ELLIPSIS),
    # then result length should be exactly available_space
    if len(text) > available_space and available_space >= len(formatting.ELLIPSIS):
        assert len(result) == available_space, f"Result length {len(result)} != available_space {available_space}"
    
    # Property: if text fits, it should be returned unchanged
    if len(text) < available_space:
        assert result == text, "Text that fits should be returned unchanged"
    
    # Property: when truncation occurs, ellipsis should be in the middle
    if len(text) >= available_space and available_space >= len(formatting.ELLIPSIS):
        assert formatting.ELLIPSIS in result, "Truncated text should contain ellipsis"
        # Check that both beginning and end of original text are preserved
        if available_space > len(formatting.ELLIPSIS):
            available_string_len = available_space - len(formatting.ELLIPSIS)
            first_half_len = int(available_string_len / 2)
            second_half_len = available_string_len - first_half_len
            if first_half_len > 0:
                assert result.startswith(text[:first_half_len]), "Should preserve text beginning"
            if second_half_len > 0:
                assert result.endswith(text[-second_half_len:]), "Should preserve text ending"


# Test 3: Indent property
@given(
    text=st.text(alphabet=st.characters(blacklist_characters='\r'), min_size=0, max_size=100),
    spaces=st.integers(min_value=0, max_value=10)
)
def test_indent_property(text, spaces):
    """Test that Indent adds exact number of spaces to non-empty lines."""
    result = formatting.Indent(text, spaces)
    
    # Split both original and result into lines
    original_lines = text.split('\n')
    result_lines = result.split('\n')
    
    # Property: same number of lines
    assert len(result_lines) == len(original_lines), "Number of lines should not change"
    
    # Property: each non-empty line should be indented by exactly `spaces` spaces
    for orig_line, result_line in zip(original_lines, result_lines):
        if orig_line:  # Non-empty line
            expected = ' ' * spaces + orig_line
            assert result_line == expected, f"Non-empty line not indented correctly"
        else:  # Empty line
            assert result_line == '', "Empty lines should remain empty"


# Test 4: WrappedJoin width property
@given(
    items=st.lists(st.text(alphabet=st.characters(blacklist_characters='\n\r'), min_size=1, max_size=20), min_size=0, max_size=10),
    separator=st.text(alphabet=st.characters(blacklist_characters='\n\r'), min_size=1, max_size=5),
    width=st.integers(min_value=10, max_value=100)
)
def test_wrapped_join_width_property(items, separator, width):
    """Test that WrappedJoin never produces lines exceeding width."""
    # Skip if any single item is longer than width (can't be wrapped properly)
    assume(all(len(item) <= width for item in items))
    
    result_lines = formatting.WrappedJoin(items, separator, width)
    
    # Property: no line should exceed the specified width
    for line in result_lines:
        assert len(line) <= width, f"Line '{line}' exceeds width {width}: length {len(line)}"
    
    # Property: all items should appear in the output
    joined_result = ''.join(result_lines)
    for item in items:
        assert item in joined_result, f"Item '{item}' not found in result"


# Test 5: _GetShortFlags property
@given(
    flags=st.lists(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=10), min_size=0, max_size=20)
)
def test_get_short_flags_property(flags):
    """Test that _GetShortFlags returns only unique first characters."""
    short_flags = helptext._GetShortFlags(flags)
    
    # Property: short_flags should only contain first characters of flags
    first_chars = [f[0] for f in flags if f]
    for short_flag in short_flags:
        assert short_flag in first_chars, f"Short flag '{short_flag}' not a first character"
    
    # Property: each character in short_flags should appear exactly once as a first character in flags
    first_char_counts = collections.Counter(first_chars)
    for short_flag in short_flags:
        assert first_char_counts[short_flag] == 1, f"Short flag '{short_flag}' is not unique"
    
    # Property: all unique first characters should be in short_flags
    unique_first_chars = [char for char, count in first_char_counts.items() if count == 1]
    assert sorted(short_flags) == sorted(unique_first_chars), "Not all unique first characters are returned"


# Test 6: Round-trip property for Indent
@given(
    text=st.text(alphabet=st.characters(blacklist_characters='\r'), min_size=0, max_size=100)
)
def test_indent_zero_is_identity(text):
    """Test that Indent with 0 spaces is identity function."""
    result = formatting.Indent(text, spaces=0)
    assert result == text, "Indent with 0 spaces should return unchanged text"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])