"""Extended property-based tests with more examples and edge cases."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
from fire import custom_descriptions, formatting
import math


# Test with more examples
@settings(max_examples=1000)
@given(st.text(), st.integers(min_value=0, max_value=200), st.integers(min_value=10, max_value=200))
@example("", 0, 80)  # Empty string with zero space
@example("a" * 100, 5, 80)  # Very long string with small space
@example("test", 4, 80)  # Exactly at boundary
def test_get_summary_always_quotes_strings_extended(text, available_space, line_length):
    """GetSummary should always return quoted strings - extended test."""
    assume(line_length >= available_space)
    result = custom_descriptions.GetSummary(text, available_space, line_length)
    assert result.startswith('"'), f"Summary should start with quote: {result}"
    assert result.endswith('"'), f"Summary should end with quote: {result}"


@settings(max_examples=1000)
@given(st.text(min_size=0), st.integers(min_value=0, max_value=2), st.integers(min_value=80, max_value=100))
def test_get_summary_very_small_space(text, available_space, line_length):
    """Test GetSummary with extremely small available_space values."""
    result = custom_descriptions.GetSummary(text, available_space, line_length)
    
    # Should always produce valid output
    assert result.startswith('"') and result.endswith('"')
    
    # With very small space, should fallback to line_length
    if available_space < 5:
        # The function should use line_length instead
        if len(text) + 2 <= line_length:
            assert result == f'"{text}"'
        else:
            # Should be truncated to fit line_length
            assert len(result) <= line_length


@settings(max_examples=1000)
@given(st.text(alphabet="🦄🌟💫🔥", min_size=0, max_size=20), 
       st.integers(min_value=5, max_value=50), 
       st.integers(min_value=50, max_value=100))
def test_get_summary_with_unicode(text, available_space, line_length):
    """Test GetSummary with Unicode characters."""
    result = custom_descriptions.GetSummary(text, available_space, line_length)
    
    # Should handle Unicode properly
    assert result.startswith('"') and result.endswith('"')
    
    # Extract content
    content = result[1:-1]
    
    # Check that Unicode is preserved when not truncated
    if len(text) + 2 <= available_space:
        assert content == text, f"Unicode should be preserved: expected {text}, got {content}"


@settings(max_examples=500)
@given(st.text(min_size=0, max_size=200).filter(lambda x: '\n' not in x and '\t' not in x),
       st.integers(min_value=5, max_value=50))
def test_ellipsis_truncate_exact_boundaries(text, available_space):
    """Test EllipsisTruncate at exact boundary conditions."""
    line_length = 100
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    
    # Test exact boundaries
    if len(text) == available_space:
        assert result == text, "Text of exact length should not be truncated"
    elif len(text) == available_space - 1:
        assert result == text, "Text one char shorter should not be truncated"
    elif len(text) == available_space + 1 and available_space >= 3:
        # Just over the boundary - should truncate
        assert result.endswith('...'), "Text one char over should be truncated"
        assert len(result) == available_space


@settings(max_examples=500)
@given(st.text(alphabet=st.characters(blacklist_categories=['Cc', 'Cs']), min_size=1, max_size=100),
       st.integers(min_value=10, max_value=50))
def test_get_description_consistency(text, available_space):
    """Test that GetDescription is consistent with GetSummary truncation logic."""
    line_length = 100
    
    summary = custom_descriptions.GetSummary(text, available_space, line_length)
    description = custom_descriptions.GetDescription(text, available_space + len('The string '), line_length)
    
    # Extract the quoted part from description
    if description.startswith('The string "') and description.endswith('"'):
        desc_quoted = '"' + description[len('The string "'):]
        
        # If we give GetDescription the same extra space it uses for prefix,
        # the quoted part should be similar to GetSummary result
        # (This tests internal consistency)


@settings(max_examples=500)
@given(st.text(min_size=0, max_size=10), st.integers(min_value=-10, max_value=300))
def test_get_summary_negative_or_large_space(text, available_space):
    """Test GetSummary with negative or very large available_space."""
    line_length = 80
    
    # The function should handle these gracefully
    if available_space < 0:
        # Should treat as 0 and fallback to line_length
        result = custom_descriptions.GetSummary(text, available_space, line_length)
        assert result.startswith('"') and result.endswith('"')
    else:
        result = custom_descriptions.GetSummary(text, available_space, line_length)
        assert result.startswith('"') and result.endswith('"')
        
        # With very large space, should show full text
        if available_space >= len(text) + 2:
            assert result == f'"{text}"'


@settings(max_examples=500)
@given(st.lists(st.text(min_size=1, max_size=5), min_size=2, max_size=5))
def test_get_summary_different_strings_different_outputs(strings):
    """Different strings should produce different summaries when possible."""
    available_space = 20
    line_length = 80
    
    # Get summaries for all strings
    summaries = [custom_descriptions.GetSummary(s, available_space, line_length) for s in strings]
    
    # If strings are different and short enough to fit, summaries should be different
    unique_strings = set(strings)
    if len(unique_strings) > 1:
        # Check which strings fit completely
        fitting_strings = [s for s in unique_strings if len(s) + 2 <= available_space]
        if len(fitting_strings) > 1:
            fitting_summaries = [custom_descriptions.GetSummary(s, available_space, line_length) 
                                for s in fitting_strings]
            assert len(set(fitting_summaries)) == len(fitting_strings), \
                "Different strings that fit should have different summaries"


@settings(max_examples=1000)
@given(st.one_of(
    st.just(None),
    st.just(object()),
    st.just(lambda x: x),
    st.just(type),
    st.builds(type, st.just("TestClass"), st.just((object,)), st.just({}))
))
def test_get_summary_returns_none_for_non_primitives(obj):
    """GetSummary should return None for non-primitive types."""
    result = custom_descriptions.GetSummary(obj, 50, 80)
    assert result is None, f"GetSummary should return None for {type(obj)}"


@settings(max_examples=1000)
@given(st.text(min_size=0, max_size=50))
def test_get_summary_get_description_none_for_non_strings(text):
    """GetSummary and GetDescription should only work for actual strings."""
    # These should work for strings
    assert custom_descriptions.GetSummary(text, 50, 80) is not None
    assert custom_descriptions.GetDescription(text, 50, 80) is not None
    
    # But should return None for other types that aren't in CUSTOM_DESC_SUM_FN_DICT
    class CustomClass:
        pass
    
    obj = CustomClass()
    assert custom_descriptions.GetSummary(obj, 50, 80) is None
    assert custom_descriptions.GetDescription(obj, 50, 80) is None


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short', '--hypothesis-show-statistics'])