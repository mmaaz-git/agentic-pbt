"""Property-based tests for fire.formatting module using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import fire.formatting as formatting


# Test Indent function
@given(st.text(), st.integers(min_value=0, max_value=20))
def test_indent_preserves_line_count(text, spaces):
    """Indenting should preserve the number of lines."""
    result = formatting.Indent(text, spaces)
    assert text.count('\n') == result.count('\n')


@given(st.text(), st.integers(min_value=0, max_value=20))
def test_indent_adds_spaces_to_nonempty_lines(text, spaces):
    """Each non-empty line should start with exactly 'spaces' spaces."""
    result = formatting.Indent(text, spaces)
    for line in result.split('\n'):
        if line:  # non-empty line
            assert line.startswith(' ' * spaces)
            assert line[spaces:].lstrip() == line[spaces:]  # no extra leading spaces


@given(st.text())
def test_indent_empty_lines_remain_empty(text):
    """Empty lines should remain empty after indentation."""
    spaces = 4
    result = formatting.Indent(text, spaces)
    original_lines = text.split('\n')
    result_lines = result.split('\n')
    
    for orig, res in zip(original_lines, result_lines):
        if not orig:  # empty line
            assert not res  # should remain empty


# Test WrappedJoin function
@given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10),
       st.text(min_size=1, max_size=5),
       st.integers(min_value=10, max_value=100))
def test_wrapped_join_preserves_all_items(items, separator, width):
    """All items should appear in the output."""
    lines = formatting.WrappedJoin(items, separator, width)
    joined_output = ''.join(lines)
    
    for item in items:
        assert item in joined_output


@given(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=10),
       st.text(min_size=1, max_size=5),
       st.integers(min_value=20, max_value=100))
def test_wrapped_join_respects_width(items, separator, width):
    """Lines should not exceed width unless a single item is longer than width."""
    lines = formatting.WrappedJoin(items, separator, width)
    
    for line in lines:
        # Line should not exceed width unless it contains a single item longer than width
        if len(line) > width:
            # Check if this is due to a single long item
            line_without_separator = line.rstrip(separator)
            parts = line_without_separator.split(separator)
            # If there's only one part, it's a single long item
            assert len(parts) == 1 or any(len(item) > width for item in items)


@given(st.lists(st.text(min_size=1, max_size=10), min_size=2, max_size=10),
       st.text(min_size=1, max_size=5),
       st.integers(min_value=20, max_value=100))
def test_wrapped_join_separator_placement(items, separator, width):
    """Separator should only appear between items, not at the very end."""
    lines = formatting.WrappedJoin(items, separator, width)
    
    if lines:
        last_line = lines[-1]
        # Last line should not end with separator
        assert not last_line.endswith(separator)


# Test EllipsisTruncate function
@given(st.text(), st.integers(min_value=0, max_value=200), st.integers(min_value=10, max_value=200))
def test_ellipsis_truncate_no_truncation_when_fits(text, available_space, line_length):
    """If text fits in available_space, it should be returned unchanged."""
    assume(line_length >= 3)  # Must fit ellipsis
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    
    if len(text) <= available_space and available_space >= 3:
        assert result == text


@given(st.text(min_size=10, max_size=100), st.integers(min_value=4, max_value=50), st.integers(min_value=10, max_value=200))
def test_ellipsis_truncate_adds_ellipsis(text, available_space, line_length):
    """When truncation happens, result should end with '...'."""
    assume(available_space < len(text))
    assume(line_length >= available_space)
    
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    
    if len(text) > available_space and available_space >= 3:
        assert result.endswith('...')
        assert len(result) == available_space


@given(st.text(min_size=5, max_size=100), st.integers(min_value=4, max_value=50), st.integers(min_value=10, max_value=200))
def test_ellipsis_truncate_preserves_prefix(text, available_space, line_length):
    """Truncation should preserve the beginning of the text."""
    assume(available_space < len(text))
    assume(available_space >= 3)
    
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    
    if len(text) > available_space:
        prefix_len = available_space - 3
        assert result[:prefix_len] == text[:prefix_len]


# Test EllipsisMiddleTruncate function
@given(st.text(), st.integers(min_value=0, max_value=200), st.integers(min_value=10, max_value=200))
def test_ellipsis_middle_truncate_no_truncation_when_fits(text, available_space, line_length):
    """If text fits in available_space, it should be returned unchanged."""
    result = formatting.EllipsisMiddleTruncate(text, available_space, line_length)
    
    if len(text) < available_space and available_space >= 3:
        assert result == text


@given(st.text(min_size=10, max_size=100), st.integers(min_value=4, max_value=50), st.integers(min_value=10, max_value=200))
def test_ellipsis_middle_truncate_contains_ellipsis(text, available_space, line_length):
    """When truncation happens, result should contain '...' in the middle."""
    assume(len(text) >= available_space)
    assume(available_space >= 3)
    
    result = formatting.EllipsisMiddleTruncate(text, available_space, line_length)
    
    if len(text) >= available_space:
        assert '...' in result
        assert len(result) == available_space


@given(st.text(min_size=10, max_size=100), st.integers(min_value=7, max_value=50), st.integers(min_value=10, max_value=200))
def test_ellipsis_middle_truncate_preserves_ends(text, available_space, line_length):
    """Middle truncation should preserve start and end of original text."""
    assume(len(text) >= available_space)
    assume(available_space >= 7)  # Need space for at least 2 chars + ... + 2 chars
    
    result = formatting.EllipsisMiddleTruncate(text, available_space, line_length)
    
    if len(text) >= available_space:
        available_string_len = available_space - 3
        first_half_len = available_string_len // 2
        second_half_len = available_string_len - first_half_len
        
        # Check that start is preserved
        assert result[:first_half_len] == text[:first_half_len]
        # Check that end is preserved
        assert result[-second_half_len:] == text[-second_half_len:]


# Test DoubleQuote function
@given(st.text())
def test_double_quote_adds_quotes(text):
    """DoubleQuote should wrap text in double quotes."""
    result = formatting.DoubleQuote(text)
    assert result.startswith('"')
    assert result.endswith('"')
    assert result[1:-1] == text


# Test for edge case in EllipsisTruncate
@given(st.integers(min_value=0, max_value=2), st.integers(min_value=10, max_value=200))
def test_ellipsis_truncate_small_available_space(available_space, line_length):
    """When available_space < 3, should fallback to line_length."""
    text = "This is a long text that needs truncation"
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    
    if available_space < 3:
        # Should use line_length instead
        if len(text) <= line_length:
            assert result == text
        else:
            assert len(result) == line_length
            assert result.endswith('...')


# Test for edge case in EllipsisMiddleTruncate
@given(st.integers(min_value=0, max_value=2), st.integers(min_value=10, max_value=200))
def test_ellipsis_middle_truncate_small_available_space(available_space, line_length):
    """When available_space < 3, should fallback to line_length."""
    text = "This is a long text that needs truncation"
    result = formatting.EllipsisMiddleTruncate(text, available_space, line_length)
    
    if available_space < 3:
        # Should use line_length instead
        if len(text) < line_length:
            assert result == text
        else:
            assert len(result) == line_length
            assert '...' in result


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])