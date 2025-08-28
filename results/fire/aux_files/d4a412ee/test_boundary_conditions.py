import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, example
import fire.custom_descriptions as custom_descriptions


@example(text='a', available_space=4, line_length=80)  # Exactly fits with quotes
@example(text='ab', available_space=4, line_length=80)  # One char too long
@example(text='abc', available_space=4, line_length=80)  # Should trigger line_length fallback
@given(st.text(min_size=1, max_size=3), st.integers(min_value=3, max_value=5), st.integers(min_value=80, max_value=100))
def test_summary_boundary_at_min_space(text, available_space, line_length):
    summary = custom_descriptions.GetStringTypeSummary(text, available_space, line_length)
    
    # When available_space < 5 (len('"..."')), uses line_length
    if available_space < 5:
        # Should use line_length instead
        if len(text) + 2 <= line_length:
            assert summary == f'"{text}"'
        else:
            assert '...' in summary
    else:
        # Normal truncation logic
        if len(text) + 2 <= available_space:
            assert summary == f'"{text}"'
        else:
            assert '...' in summary and len(summary) <= available_space


@example(text='test', available_space=18, line_length=80)  # Exactly fits
@example(text='testing', available_space=18, line_length=80)  # Should truncate  
@given(st.text(min_size=1, max_size=10), st.integers(min_value=17, max_value=25), st.integers(min_value=80, max_value=100))
def test_description_boundary_conditions(text, available_space, line_length):
    description = custom_descriptions.GetStringTypeDescription(text, available_space, line_length)
    
    # Minimum needed: len('The string ""...') = 17
    min_needed = len('The string ""') + len('...')  # 17
    
    if available_space < min_needed:
        # Should use line_length
        expected = f'The string "{text}"'
        if len(expected) <= line_length:
            assert description == expected
        else:
            assert '...' in description
    else:
        # Normal case
        assert description.startswith('The string "')
        assert description.endswith('"')


@given(st.text(min_size=100, max_size=200), st.integers(min_value=1, max_value=4), st.integers(min_value=80, max_value=100))
def test_very_long_text_small_space(text, available_space, line_length):
    # Test with very long text and tiny available_space
    summary = custom_descriptions.GetStringTypeSummary(text, available_space, line_length)
    
    # Should fall back to line_length and truncate
    assert summary.startswith('"')
    assert summary.endswith('"')
    assert '...' in summary
    assert len(summary) <= line_length


@given(st.text(min_size=0, max_size=100), st.integers(min_value=5, max_value=5), st.integers(min_value=80, max_value=80))
def test_exact_boundary_at_five(text, available_space, line_length):
    # Test the exact boundary at available_space=5
    summary = custom_descriptions.GetStringTypeSummary(text, available_space, line_length)
    
    # available_space=5 can fit:
    # - "" (2 chars)
    # - "x" (3 chars)  
    # - "xx" (4 chars)
    # - "xxx" (5 chars)
    # - longer strings get "..." (5 chars)
    
    if len(text) + 2 <= 5:  # Fits without truncation
        assert summary == f'"{text}"'
    else:  # Needs truncation
        assert summary == '"..."', f"Expected truncation for text={text!r}, got {summary!r}"


@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=10))
def test_negative_available_space(text):
    # What happens with negative available_space?
    for available_space in [-10, -1, 0]:
        try:
            summary = custom_descriptions.GetStringTypeSummary(text, available_space, 80)
            # Should not crash and should produce valid output
            assert summary.startswith('"') and summary.endswith('"')
        except Exception as e:
            # If it raises an exception, that's potentially a bug
            assert False, f"Failed with negative available_space: {e}"


@settings(max_examples=500)
@given(st.text(), st.integers(min_value=0, max_value=200), st.integers(min_value=10, max_value=200))
def test_length_consistency(text, available_space, line_length):
    # Test that the same text with the same parameters always gives the same result
    summary1 = custom_descriptions.GetStringTypeSummary(text, available_space, line_length)
    summary2 = custom_descriptions.GetStringTypeSummary(text, available_space, line_length)
    
    assert summary1 == summary2, "Same input should produce same output"
    
    description1 = custom_descriptions.GetStringTypeDescription(text, available_space, line_length)
    description2 = custom_descriptions.GetStringTypeDescription(text, available_space, line_length)
    
    assert description1 == description2, "Same input should produce same output"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])