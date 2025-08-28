import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

import math
from hypothesis import given, strategies as st, settings, assume
import fire.custom_descriptions as custom_descriptions
import fire.formatting as formatting


@given(st.text(), st.integers(min_value=5, max_value=200), st.integers(min_value=10, max_value=200))
def test_string_summary_always_has_double_quotes(text, available_space, line_length):
    assume(line_length >= available_space)
    summary = custom_descriptions.GetStringTypeSummary(text, available_space, line_length)
    assert summary.startswith('"'), f"Summary should start with double quote, got: {summary}"
    assert summary.endswith('"'), f"Summary should end with double quote, got: {summary}"


@given(st.text(), st.integers(min_value=20, max_value=200), st.integers(min_value=20, max_value=200))
def test_string_description_always_starts_with_prefix(text, available_space, line_length):
    assume(line_length >= available_space)
    description = custom_descriptions.GetStringTypeDescription(text, available_space, line_length)
    assert description.startswith('The string "'), f"Description should start with 'The string \"', got: {description}"
    assert description.endswith('"'), f"Description should end with double quote, got: {description}"


@given(st.text(min_size=0, max_size=1000), st.integers(min_value=10, max_value=200), st.integers(min_value=80, max_value=200))
def test_summary_respects_available_space(text, available_space, line_length):
    assume(line_length >= available_space)
    summary = custom_descriptions.GetStringTypeSummary(text, available_space, line_length)
    
    # When available_space is very small (< 5), it uses line_length instead
    if available_space >= 5:
        assert len(summary) <= max(available_space, len('""')), f"Summary length {len(summary)} exceeds available_space {available_space}"


@given(st.text(min_size=0, max_size=1000), st.integers(min_value=10, max_value=200), st.integers(min_value=80, max_value=200))
def test_description_respects_available_space(text, available_space, line_length):
    assume(line_length >= available_space)
    description = custom_descriptions.GetStringTypeDescription(text, available_space, line_length)
    
    # When available_space is very small, it uses line_length instead
    min_needed = len('The string ""') + len('...')
    if available_space >= min_needed:
        # Allow some flexibility for edge cases
        assert len(description) <= max(available_space + 3, line_length), f"Description length {len(description)} exceeds constraints"


@given(st.one_of(
    st.text(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.dictionaries(st.text(), st.integers()),
    st.lists(st.integers()),
    st.tuples(st.integers()),
    st.sets(st.integers()),
    st.frozensets(st.integers()),
    st.binary(),
    st.complex_numbers(allow_nan=False, allow_infinity=False)
))
def test_needs_custom_description_for_primitives(obj):
    result = custom_descriptions.NeedsCustomDescription(obj)
    type_ = type(obj)
    
    # These types should return True according to the function
    primitive_types = (str, int, bytes, float, complex, bool, dict, tuple, list, set, frozenset)
    
    if type_ in primitive_types:
        assert result is True, f"NeedsCustomDescription should return True for {type_.__name__}, got {result}"
    else:
        assert result is False, f"NeedsCustomDescription should return False for {type_.__name__}, got {result}"


@given(st.text(min_size=20, max_size=500), st.integers(min_value=5, max_value=15), st.integers(min_value=80, max_value=200))
def test_truncation_with_ellipsis(text, available_space, line_length):
    assume(line_length >= available_space)
    
    summary = custom_descriptions.GetStringTypeSummary(text, available_space, line_length)
    
    # If text is longer than available_space - 2 (for quotes), it should be truncated
    if len(text) + 2 > available_space:  # 2 for quotes
        assert '...' in summary, f"Truncated summary should contain ellipsis, got: {summary}"


@given(st.one_of(st.integers(), st.floats(), st.lists(st.integers())))
def test_get_summary_returns_none_for_non_strings(obj):
    summary = custom_descriptions.GetSummary(obj, 80, 80)
    assert summary is None, f"GetSummary should return None for {type(obj).__name__}, got {summary}"


@given(st.one_of(st.integers(), st.floats(), st.lists(st.integers())))
def test_get_description_returns_none_for_non_strings(obj):
    description = custom_descriptions.GetDescription(obj, 80, 80)
    assert description is None, f"GetDescription should return None for {type(obj).__name__}, got {description}"


@given(st.text(), st.integers(min_value=0, max_value=3), st.integers(min_value=80, max_value=200))
def test_very_small_available_space_falls_back_to_line_length(text, available_space, line_length):
    summary = custom_descriptions.GetStringTypeSummary(text, available_space, line_length)
    # When available_space < len('""...') = 5, it should use line_length
    if available_space < 5:
        # Should not crash and should produce valid output
        assert summary.startswith('"') and summary.endswith('"')


@given(st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cs"]), min_size=1), 
       st.integers(min_value=10, max_value=200), 
       st.integers(min_value=80, max_value=200))
def test_ellipsis_truncate_preserves_string_content(text, available_space, line_length):
    assume(line_length >= available_space)
    summary = custom_descriptions.GetStringTypeSummary(text, available_space, line_length)
    
    # Remove quotes
    content = summary[1:-1]
    
    if '...' in content:
        # If truncated, the non-ellipsis part should be from the original text
        prefix = content[:-3]  # Remove the ellipsis
        assert text.startswith(prefix), f"Truncated content should be prefix of original"
    else:
        # If not truncated, content should equal original text
        assert content == text, f"Non-truncated content should equal original"


@given(st.text(min_size=0, max_size=0))  # Empty string
def test_empty_string_handling(text):
    # Test with various available spaces
    for available_space in [0, 1, 2, 3, 4, 5, 10, 50]:
        summary = custom_descriptions.GetStringTypeSummary(text, available_space, 80)
        assert summary == '""', f"Empty string should give empty quotes, got: {summary}"
        
        description = custom_descriptions.GetStringTypeDescription(text, available_space, 80)
        assert description == 'The string ""', f"Empty string description should be 'The string \"\"', got: {description}"


@given(st.text(alphabet='\\', min_size=1, max_size=10))  # Backslash characters
def test_special_characters_backslash(text):
    summary = custom_descriptions.GetStringTypeSummary(text, 50, 80)
    assert summary.startswith('"') and summary.endswith('"')
    # Check the content matches (accounting for potential truncation)
    content = summary[1:-1]
    if '...' not in content:
        assert content == text


@given(st.text(alphabet='"', min_size=1, max_size=10))  # Quote characters
def test_special_characters_quotes(text):
    summary = custom_descriptions.GetStringTypeSummary(text, 50, 80)
    assert summary.startswith('"') and summary.endswith('"')
    # The quotes inside should not break the outer quotes
    assert summary.count('"') >= 2  # At least the outer quotes


@given(st.integers(min_value=0, max_value=4), st.integers(min_value=80, max_value=200))
def test_boundary_available_space_less_than_ellipsis(available_space, line_length):
    # When available_space < len("...") = 3, special handling occurs
    text = "This is a long string that should be truncated"
    summary = custom_descriptions.GetStringTypeSummary(text, available_space, line_length)
    
    # Should not crash and should produce valid output
    assert summary.startswith('"') and summary.endswith('"')
    
    # When available_space < 5, it should use line_length
    if available_space < 5:
        assert len(summary) <= line_length


@settings(max_examples=1000)  # Increase test runs for edge case detection
@given(st.text(), st.integers(min_value=5, max_value=10), st.integers(min_value=80, max_value=100))
def test_edge_case_intensive(text, available_space, line_length):
    # Focus on edge cases with small available_space
    summary = custom_descriptions.GetStringTypeSummary(text, available_space, line_length)
    description = custom_descriptions.GetStringTypeDescription(text, available_space, line_length)
    
    # Basic invariants that should always hold
    assert summary.startswith('"') and summary.endswith('"')
    assert description.startswith('The string "') and description.endswith('"')
    
    # Length constraints
    if available_space >= 5:
        # For summary
        if len(text) + 2 <= available_space:
            assert len(summary) == len(text) + 2
        else:
            assert '...' in summary
    
    # Consistency check - same input should give same output
    summary2 = custom_descriptions.GetStringTypeSummary(text, available_space, line_length)
    assert summary == summary2


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])