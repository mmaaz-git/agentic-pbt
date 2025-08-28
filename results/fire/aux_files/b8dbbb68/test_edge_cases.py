"""Specific edge case tests for potential bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
from fire import custom_descriptions, formatting


def test_ellipsis_truncate_with_available_space_exactly_3():
    """Test EllipsisTruncate when available_space is exactly 3 (length of ellipsis)."""
    text = "Hello World"
    result = formatting.EllipsisTruncate(text, 3, 80)
    assert result == "...", f"Expected '...' but got '{result}'"


def test_ellipsis_truncate_with_available_space_2():
    """Test EllipsisTruncate when available_space is 2 (less than ellipsis length)."""
    text = "Hello World"
    result = formatting.EllipsisTruncate(text, 2, 80)
    # Should fallback to line_length
    assert result == text or len(result) == 80, f"Should use full text or line_length"


def test_get_summary_with_quotes_in_string():
    """Test GetSummary with strings containing quotes."""
    text = 'He said "Hello"'
    result = custom_descriptions.GetSummary(text, 50, 80)
    assert result == f'"{text}"', f"Should handle internal quotes: {result}"


def test_get_summary_available_space_exactly_fits():
    """Test when available_space is exactly the size needed."""
    text = "Hi"
    # Need 4 chars total: "Hi"
    result = custom_descriptions.GetSummary(text, 4, 80)
    assert result == '"Hi"', f"Should show full text when it exactly fits: {result}"


def test_get_summary_one_char_too_small():
    """Test when available_space is one character too small."""
    text = "Hello"
    # Need 7 chars for "Hello", give 6
    result = custom_descriptions.GetSummary(text, 6, 80)
    # Should truncate with ellipsis
    assert result == '"..."', f"Should show ellipsis when one char short: {result}"


def test_get_description_minimum_space():
    """Test GetDescription with minimum usable space."""
    text = "Test"
    # Minimum for 'The string "..."' is 16 characters
    result = custom_descriptions.GetDescription(text, 16, 80)
    assert result == 'The string "..."', f"Should show minimum description: {result}"


def test_ellipsis_middle_truncate():
    """Test the EllipsisMiddleTruncate function."""
    text = "abcdefghijklmnopqrstuvwxyz"
    result = formatting.EllipsisMiddleTruncate(text, 10, 80)
    assert len(result) == 10, f"Result should be exactly 10 chars: {result}"
    assert "..." in result, f"Should contain ellipsis: {result}"
    assert result[0] == 'a', f"Should start with first char: {result}"
    assert result[-1] == 'z', f"Should end with last char: {result}"


@given(st.text(min_size=10, max_size=100))
def test_ellipsis_middle_truncate_preserves_ends(text):
    """EllipsisMiddleTruncate should preserve start and end of string."""
    if len(text) < 10:
        return
    
    result = formatting.EllipsisMiddleTruncate(text, 10, 80)
    
    # Should preserve some characters from start and end
    assert result[0] == text[0], "Should preserve first character"
    assert result[-1] == text[-1], "Should preserve last character"
    assert "..." in result, "Should contain ellipsis in middle"


def test_needs_custom_description_edge_cases():
    """Test NeedsCustomDescription with edge case types."""
    # These should return True
    assert custom_descriptions.NeedsCustomDescription("string") == True
    assert custom_descriptions.NeedsCustomDescription(42) == True
    assert custom_descriptions.NeedsCustomDescription(3.14) == True
    assert custom_descriptions.NeedsCustomDescription(True) == True
    assert custom_descriptions.NeedsCustomDescription({}) == True
    assert custom_descriptions.NeedsCustomDescription([]) == True
    assert custom_descriptions.NeedsCustomDescription(()) == True
    assert custom_descriptions.NeedsCustomDescription(set()) == True
    assert custom_descriptions.NeedsCustomDescription(frozenset()) == True
    assert custom_descriptions.NeedsCustomDescription(b"bytes") == True
    assert custom_descriptions.NeedsCustomDescription(complex(1, 2)) == True
    
    # These should return False
    assert custom_descriptions.NeedsCustomDescription(None) == False
    assert custom_descriptions.NeedsCustomDescription(object()) == False
    assert custom_descriptions.NeedsCustomDescription(lambda x: x) == False
    
    class CustomClass:
        pass
    assert custom_descriptions.NeedsCustomDescription(CustomClass()) == False


def test_get_summary_with_line_length_smaller_than_available_space():
    """Test when line_length is smaller than available_space (edge case)."""
    text = "Hello World"
    # This is an unusual case where available_space > line_length
    result = custom_descriptions.GetSummary(text, 100, 20)
    # Should still work, probably limited by line_length
    assert result.startswith('"') and result.endswith('"')


def test_empty_string_edge_cases():
    """Test empty string with various space configurations."""
    # Empty string with no space
    result = custom_descriptions.GetSummary("", 0, 80)
    assert result == '""', f"Empty string with 0 space: {result}"
    
    # Empty string with minimal space
    result = custom_descriptions.GetSummary("", 2, 80)
    assert result == '""', f"Empty string with 2 space: {result}"
    
    # Empty string description
    result = custom_descriptions.GetDescription("", 20, 80)
    assert result == 'The string ""', f"Empty string description: {result}"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])