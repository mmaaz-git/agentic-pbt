"""Test extreme edge cases that might expose bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from fire import custom_descriptions, formatting


@settings(max_examples=1000)
@given(st.text(min_size=0, max_size=10), 
       st.integers(min_value=-1000000, max_value=-1))
def test_negative_available_space(text, available_space):
    """Test with negative available_space values."""
    line_length = 80
    
    # Should handle negative space gracefully
    result = custom_descriptions.GetSummary(text, available_space, line_length)
    assert result.startswith('"') and result.endswith('"')
    
    # With negative space, should fall back to line_length
    if len(text) + 2 <= line_length:
        assert result == f'"{text}"'


@settings(max_examples=1000)
@given(st.text(min_size=0, max_size=10),
       st.integers(min_value=-1000000, max_value=-1))
def test_negative_line_length(text, line_length):
    """Test with negative line_length values."""
    available_space = 20
    
    # Should handle negative line_length
    result = custom_descriptions.GetSummary(text, available_space, line_length)
    assert result.startswith('"') and result.endswith('"')


@settings(max_examples=500)
@given(st.text(min_size=0, max_size=5))
def test_both_negative(text):
    """Test with both parameters negative."""
    result = custom_descriptions.GetSummary(text, -10, -10)
    assert result.startswith('"') and result.endswith('"')


def test_extreme_large_values():
    """Test with extremely large values."""
    text = "Hello"
    
    # Very large available_space
    result = custom_descriptions.GetSummary(text, 999999999, 80)
    assert result == '"Hello"'
    
    # Very large line_length
    result = custom_descriptions.GetSummary(text, 10, 999999999)
    assert result == '"Hello"'
    
    # Both very large
    result = custom_descriptions.GetSummary(text, 999999999, 999999999)
    assert result == '"Hello"'


def test_zero_values():
    """Test with zero values."""
    text = "Test"
    
    # Zero available_space
    result = custom_descriptions.GetSummary(text, 0, 80)
    assert result.startswith('"') and result.endswith('"')
    
    # Zero line_length
    result = custom_descriptions.GetSummary(text, 20, 0)
    assert result.startswith('"') and result.endswith('"')
    
    # Both zero
    result = custom_descriptions.GetSummary(text, 0, 0)
    assert result.startswith('"') and result.endswith('"')


@settings(max_examples=500)
@given(st.text(alphabet="a", min_size=100000, max_size=100001))
def test_very_long_strings(text):
    """Test with very long strings."""
    # Should handle very long strings without errors
    result = custom_descriptions.GetSummary(text, 50, 80)
    assert result.startswith('"') and result.endswith('"')
    assert len(result) <= 50
    assert '"aaa' in result  # Should start with the repeated 'a's
    assert '..."' in result  # Should be truncated


def test_ellipsis_truncate_edge_cases():
    """Test EllipsisTruncate with edge cases."""
    # Empty string
    assert formatting.EllipsisTruncate("", 10, 80) == ""
    assert formatting.EllipsisTruncate("", 0, 80) == ""
    assert formatting.EllipsisTruncate("", -1, 80) == ""
    
    # Text length exactly equals available_space
    assert formatting.EllipsisTruncate("abc", 3, 80) == "abc"
    
    # Text length one more than available_space
    assert formatting.EllipsisTruncate("abcd", 3, 80) == "..."
    
    # Available space is 1 or 2 (less than ellipsis)
    result = formatting.EllipsisTruncate("Hello", 1, 80)
    assert result == "Hello"  # Falls back to line_length
    
    result = formatting.EllipsisTruncate("Hello", 2, 80)
    assert result == "Hello"  # Falls back to line_length


def test_ellipsis_middle_truncate_edge_cases():
    """Test EllipsisMiddleTruncate with edge cases."""
    # Empty string
    assert formatting.EllipsisMiddleTruncate("", 10, 80) == ""
    
    # Very small available_space
    result = formatting.EllipsisMiddleTruncate("abcdefgh", 3, 80)
    # With only 3 chars available, should just be ellipsis
    assert result == "..."
    
    # Available space of 4
    result = formatting.EllipsisMiddleTruncate("abcdefgh", 4, 80)
    assert len(result) == 4
    assert "..." in result
    
    # Text shorter than available space
    assert formatting.EllipsisMiddleTruncate("ab", 10, 80) == "ab"


@settings(max_examples=500)
@given(st.text(min_size=10, max_size=100))
def test_ellipsis_middle_truncate_symmetry(text):
    """Test that EllipsisMiddleTruncate maintains reasonable symmetry."""
    available_space = 10
    line_length = 80
    
    result = formatting.EllipsisMiddleTruncate(text, available_space, line_length)
    
    if len(text) > available_space:
        assert len(result) == available_space
        assert "..." in result
        
        # Find position of ellipsis
        ellipsis_pos = result.index("...")
        
        # Check that we have some content before and after ellipsis
        before_ellipsis = ellipsis_pos
        after_ellipsis = len(result) - ellipsis_pos - 3
        
        # The difference shouldn't be more than 1 (for odd lengths)
        assert abs(before_ellipsis - after_ellipsis) <= 1, \
            f"Asymmetric truncation: {before_ellipsis} before, {after_ellipsis} after"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])