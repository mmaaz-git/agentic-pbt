"""Property-based tests for fire.custom_descriptions module using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from fire import custom_descriptions, formatting
import math


@given(st.text(), st.integers(min_value=0, max_value=200), st.integers(min_value=10, max_value=200))
def test_get_summary_always_quotes_strings(text, available_space, line_length):
    """GetSummary should always return quoted strings."""
    assume(line_length >= available_space)
    result = custom_descriptions.GetSummary(text, available_space, line_length)
    assert result.startswith('"'), f"Summary should start with quote: {result}"
    assert result.endswith('"'), f"Summary should end with quote: {result}"


@given(st.text(min_size=1), st.integers(min_value=5, max_value=50), st.integers(min_value=50, max_value=200))
def test_get_summary_truncation(text, available_space, line_length):
    """GetSummary should truncate with ellipsis when text doesn't fit."""
    assume(line_length >= available_space)
    result = custom_descriptions.GetSummary(text, available_space, line_length)
    
    # Remove quotes to get actual content
    content = result[1:-1]
    
    # If the original text + 2 quotes fits, it should be shown in full
    if len(text) + 2 <= available_space:
        assert content == text, f"Text should not be truncated when it fits"
    # If it doesn't fit and we have enough space for ellipsis
    elif available_space >= 5:  # Minimum for "..."
        # Content should be truncated with ellipsis
        if len(text) > available_space - 2:
            assert content.endswith('...'), f"Truncated text should end with ellipsis: {content}"
            # Length should not exceed available space
            assert len(result) <= available_space, f"Result length {len(result)} exceeds available_space {available_space}"


@given(st.text(), st.integers(min_value=0, max_value=200), st.integers(min_value=10, max_value=200))
def test_get_description_format(text, available_space, line_length):
    """GetDescription should always start with 'The string ' and quote the value."""
    assume(line_length >= available_space)
    result = custom_descriptions.GetDescription(text, available_space, line_length)
    assert result.startswith('The string "'), f"Description should start with 'The string \"': {result}"
    assert result.endswith('"'), f"Description should end with quote: {result}"


@given(st.text(min_size=0, max_size=10), st.integers(min_value=0, max_value=4))
def test_get_summary_small_available_space_fallback(text, available_space):
    """When available_space < 5 (minimum for quotes + ellipsis), should use line_length."""
    line_length = 80
    result = custom_descriptions.GetSummary(text, available_space, line_length)
    
    # Should still produce valid quoted output
    assert result.startswith('"') and result.endswith('"')
    
    # For very small available_space, it should fallback to line_length
    # So the result can be longer than available_space
    if available_space < 5 and len(text) > 0:
        # Result might be longer than available_space due to fallback
        assert len(result) <= line_length


@given(st.text(min_size=0, max_size=100), st.integers(min_value=3, max_value=150), st.integers(min_value=80, max_value=200))
def test_ellipsis_truncate_length_invariant(text, available_space, line_length):
    """EllipsisTruncate should never return text longer than available_space (when >= 3)."""
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    
    if available_space >= 3:  # Minimum for ellipsis
        if len(text) <= available_space:
            assert result == text, "Text should not be truncated when it fits"
        else:
            assert len(result) <= available_space, f"Result length {len(result)} exceeds available_space {available_space}"
            assert result.endswith('...'), "Truncated text should end with ellipsis"


@given(st.text(min_size=0, max_size=50), st.integers(min_value=5, max_value=100))
def test_get_summary_monotonicity(text, base_space):
    """As available_space increases, output should not get shorter."""
    line_length = 200
    
    result1 = custom_descriptions.GetSummary(text, base_space, line_length)
    result2 = custom_descriptions.GetSummary(text, base_space + 10, line_length)
    
    # The content (without quotes) should not get shorter with more space
    content1 = result1[1:-1] if result1.startswith('"') else result1
    content2 = result2[1:-1] if result2.startswith('"') else result2
    
    # If content1 is truncated (ends with ...), content2 should be at least as long
    if content1.endswith('...'):
        # Remove ellipsis for comparison
        base_content1 = content1[:-3] if content1.endswith('...') else content1
        base_content2 = content2[:-3] if content2.endswith('...') else content2
        
        # With more space, we should show at least as much content
        assert len(base_content2) >= len(base_content1), \
            f"Content got shorter with more space: '{content1}' -> '{content2}'"


@given(st.text(min_size=1, max_size=100), st.integers(min_value=1, max_value=10))
def test_ellipsis_truncate_small_available_space(text, available_space):
    """Test EllipsisTruncate behavior with very small available_space."""
    line_length = 80
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    
    # When available_space < 3 (length of ellipsis), it should use line_length
    if available_space < 3:
        if len(text) <= line_length:
            assert result == text
        else:
            assert len(result) == line_length
            assert result.endswith('...')
    else:
        # Normal truncation
        if len(text) <= available_space:
            assert result == text
        else:
            assert len(result) == available_space
            assert result.endswith('...')


@given(st.text())
def test_needs_custom_description_for_strings(text):
    """NeedsCustomDescription should return True for all strings."""
    assert custom_descriptions.NeedsCustomDescription(text) == True


@given(st.text(min_size=0, max_size=200), st.integers(min_value=5, max_value=100), st.integers(min_value=100, max_value=200))
def test_get_description_truncation(text, available_space, line_length):
    """GetDescription should properly truncate long strings."""
    assume(line_length >= available_space)
    result = custom_descriptions.GetDescription(text, available_space, line_length)
    
    # Should always have the correct format
    assert result.startswith('The string "')
    assert result.endswith('"')
    
    # Extract the quoted part
    prefix_len = len('The string "')
    content = result[prefix_len:-1]
    
    # Check truncation behavior
    full_length_needed = len('The string "') + len(text) + 1  # 1 for closing quote
    
    if full_length_needed <= available_space:
        # Should show full text
        assert content == text
    elif available_space >= len('The string "...""'):  # Minimum meaningful size
        # Should be truncated with ellipsis
        if len(text) > 0 and full_length_needed > available_space:
            assert content.endswith('...')


@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.dictionaries(st.text(), st.integers()),
    st.lists(st.integers()),
    st.tuples(st.integers()),
    st.sets(st.integers()),
    st.frozensets(st.integers())
))
def test_needs_custom_description_for_primitives(obj):
    """NeedsCustomDescription should return True for primitive types."""
    assert custom_descriptions.NeedsCustomDescription(obj) == True


@given(st.integers(min_value=10, max_value=200))
def test_get_summary_empty_string(line_length):
    """GetSummary should handle empty strings correctly."""
    result = custom_descriptions.GetSummary("", 10, line_length)
    assert result == '""', f"Empty string should be represented as empty quotes: {result}"


@given(st.text(alphabet="a", min_size=1, max_size=100), st.integers(min_value=6, max_value=50))
def test_ellipsis_truncate_consistent_behavior(text, available_space):
    """EllipsisTruncate should consistently truncate at the same position."""
    line_length = 100
    result1 = formatting.EllipsisTruncate(text, available_space, line_length)
    result2 = formatting.EllipsisTruncate(text, available_space, line_length)
    
    assert result1 == result2, "Same input should produce same output"
    
    if len(text) > available_space and available_space >= 3:
        # Verify truncation point
        expected_text_len = available_space - 3  # 3 for "..."
        assert result1[:expected_text_len] == text[:expected_text_len]
        assert result1 == text[:expected_text_len] + "..."


if __name__ == '__main__':
    # Run the tests
    import pytest
    pytest.main([__file__, '-v'])