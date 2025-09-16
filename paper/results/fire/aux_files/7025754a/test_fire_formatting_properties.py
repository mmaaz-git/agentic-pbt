"""Property-based tests for fire.formatting module using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import fire.formatting as formatting


# Test Indent function properties
@given(st.text(), st.integers(min_value=0, max_value=20))
def test_indent_preserves_line_count(text, spaces):
    """Indenting should preserve the number of lines."""
    original_lines = text.split('\n')
    indented = formatting.Indent(text, spaces)
    indented_lines = indented.split('\n')
    assert len(original_lines) == len(indented_lines)


@given(st.text(min_size=1), st.integers(min_value=1, max_value=20))
def test_indent_adds_spaces_to_non_empty_lines(text, spaces):
    """Non-empty lines should start with the specified number of spaces."""
    indented = formatting.Indent(text, spaces)
    for line in indented.split('\n'):
        if line:  # Non-empty line
            assert line.startswith(' ' * spaces)
            assert line[spaces:].lstrip() == line[spaces:]  # No leading spaces after indent


@given(st.text(), st.integers(min_value=0, max_value=20))
def test_indent_preserves_empty_lines(text, spaces):
    """Empty lines should remain empty after indenting."""
    indented = formatting.Indent(text, spaces)
    original_lines = text.split('\n')
    indented_lines = indented.split('\n')
    for orig, ind in zip(original_lines, indented_lines):
        if not orig:  # Empty line
            assert not ind  # Should remain empty


# Test WrappedJoin function properties
@given(st.lists(st.text(min_size=1, max_size=20), min_size=1), 
       st.text(min_size=1, max_size=5),
       st.integers(min_value=10, max_value=100))
def test_wrapped_join_preserves_all_items(items, separator, width):
    """All items should appear in the output."""
    lines = formatting.WrappedJoin(items, separator, width)
    joined_output = ''.join(lines)
    for item in items:
        assert item in joined_output


@given(st.lists(st.text(min_size=1, max_size=20), min_size=1),
       st.text(min_size=1, max_size=5),
       st.integers(min_value=10, max_value=100))
def test_wrapped_join_respects_width(items, separator, width):
    """No line should exceed the specified width."""
    lines = formatting.WrappedJoin(items, separator, width)
    for line in lines[:-1]:  # All lines except the last should be at or near width
        assert len(line) <= width + len(separator)  # Allow small overflow for separator


@given(st.lists(st.text(min_size=1, max_size=10), min_size=2, max_size=10),
       st.text(min_size=1, max_size=3),
       st.integers(min_value=20, max_value=100))
def test_wrapped_join_preserves_order(items, separator, width):
    """Items should appear in the same order in the output."""
    lines = formatting.WrappedJoin(items, separator, width)
    joined_output = ''.join(lines)
    
    # Find positions of each item in the output
    positions = []
    for item in items:
        pos = joined_output.find(item)
        if pos != -1:
            positions.append(pos)
    
    # Check that positions are in increasing order
    assert positions == sorted(positions)


# Test EllipsisTruncate function properties
@given(st.text(), st.integers(min_value=4, max_value=200), st.integers(min_value=10, max_value=200))
def test_ellipsis_truncate_short_text_unchanged(text, available_space, line_length):
    """Text shorter than available space should remain unchanged."""
    assume(len(text) <= available_space)
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    assert result == text


@given(st.text(min_size=10, max_size=100), st.integers(min_value=4, max_value=20), st.integers(min_value=30, max_value=200))
def test_ellipsis_truncate_result_length(text, available_space, line_length):
    """Truncated text should be exactly available_space characters."""
    assume(len(text) > available_space)
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    assert len(result) == available_space


@given(st.text(min_size=10, max_size=100), st.integers(min_value=4, max_value=50), st.integers(min_value=30, max_value=200))
def test_ellipsis_truncate_preserves_prefix(text, available_space, line_length):
    """Truncated text should preserve the beginning of the original."""
    assume(len(text) > available_space)
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    # Result should start with the same prefix (minus the ellipsis)
    prefix_len = available_space - len(formatting.ELLIPSIS)
    if prefix_len > 0:
        assert result.startswith(text[:prefix_len])


# Test EllipsisMiddleTruncate function properties
@given(st.text(), st.integers(min_value=4, max_value=200), st.integers(min_value=10, max_value=200))
def test_ellipsis_middle_truncate_short_text_unchanged(text, available_space, line_length):
    """Text shorter than available space should remain unchanged."""
    assume(len(text) < available_space)
    result = formatting.EllipsisMiddleTruncate(text, available_space, line_length)
    assert result == text


@given(st.text(min_size=10, max_size=100), st.integers(min_value=4, max_value=20), st.integers(min_value=30, max_value=200))
def test_ellipsis_middle_truncate_result_length(text, available_space, line_length):
    """Truncated text should be exactly available_space characters."""
    assume(len(text) >= available_space)
    result = formatting.EllipsisMiddleTruncate(text, available_space, line_length)
    assert len(result) == available_space


@given(st.text(min_size=10, max_size=100), st.integers(min_value=6, max_value=50), st.integers(min_value=30, max_value=200))
def test_ellipsis_middle_truncate_preserves_ends(text, available_space, line_length):
    """Middle truncation should preserve start and end of the text."""
    assume(len(text) >= available_space)
    result = formatting.EllipsisMiddleTruncate(text, available_space, line_length)
    
    # Calculate expected lengths
    available_string_len = available_space - len(formatting.ELLIPSIS)
    first_half_len = int(available_string_len / 2)
    second_half_len = available_string_len - first_half_len
    
    # Check that result preserves the beginning and end
    if first_half_len > 0:
        assert result.startswith(text[:first_half_len])
    if second_half_len > 0:
        assert result.endswith(text[-second_half_len:])


# Test DoubleQuote function properties
@given(st.text())
def test_double_quote_adds_quotes(text):
    """DoubleQuote should wrap text in double quotes."""
    result = formatting.DoubleQuote(text)
    assert result.startswith('"')
    assert result.endswith('"')
    assert result[1:-1] == text


@given(st.text())
def test_double_quote_round_trip(text):
    """Removing quotes should return the original text."""
    quoted = formatting.DoubleQuote(text)
    unquoted = quoted[1:-1]  # Remove first and last character
    assert unquoted == text


# Edge case tests
@given(st.integers(min_value=0, max_value=2), st.integers(min_value=10, max_value=100))
def test_ellipsis_truncate_small_available_space(available_space, line_length):
    """When available_space < len(ELLIPSIS), should use line_length instead."""
    text = "This is a very long string that needs truncation"
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    if available_space < len(formatting.ELLIPSIS):
        # Should not truncate when available_space is too small
        assert result == text


@given(st.integers(min_value=0, max_value=2), st.integers(min_value=10, max_value=100))
def test_ellipsis_middle_truncate_small_available_space(available_space, line_length):
    """When available_space < len(ELLIPSIS), should use line_length instead."""
    text = "This is a very long string that needs truncation"
    result = formatting.EllipsisMiddleTruncate(text, available_space, line_length)
    if available_space < len(formatting.ELLIPSIS):
        # Should not truncate when available_space is too small
        assert result == text


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])