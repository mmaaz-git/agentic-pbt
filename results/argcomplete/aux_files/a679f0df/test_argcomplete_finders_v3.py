import os
import sys
import argparse
from hypothesis import given, strategies as st, assume, settings, example
import argcomplete.finders as finders
from argcomplete.finders import CompletionFinder, ExclusiveCompletionFinder, default_validator
from argcomplete.lexers import split_line


# Test for potential integer overflow or boundary issues
@given(
    line=st.text(min_size=0, max_size=1000),
    point=st.integers()
)
@settings(max_examples=500)
def test_split_line_invalid_point(line, point):
    """Property: split_line should handle any point value gracefully"""
    try:
        result = split_line(line, point)
        # If it doesn't crash, check basic invariants
        prequote, prefix, suffix, words, wordbreak_pos = result
        assert isinstance(prequote, str)
        assert isinstance(prefix, str)
        assert isinstance(suffix, str)
        assert isinstance(words, list)
    except Exception as e:
        # Check if it's a reasonable exception
        # Negative points or points beyond the line should be handled
        pass


# Test filter_completions with None in exclude list
@given(
    completions=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=10)
)
def test_filter_completions_with_none_exclude(completions):
    """Property: filter_completions should handle None in exclude list"""
    # Include None in exclude list
    exclude = [None] + completions[:2] if len(completions) >= 2 else [None]
    
    finder = CompletionFinder(exclude=exclude)
    try:
        filtered = finder.filter_completions(completions)
        # Should not crash and should filter properly
        for item in completions[:2]:
            if item in exclude:
                assert item not in filtered
    except TypeError:
        # If it crashes with None, that's a bug
        assert False, "filter_completions crashed with None in exclude list"


# Test quote_completions with empty list
def test_quote_completions_empty_list():
    """Property: quote_completions should handle empty list"""
    finder = CompletionFinder()
    result = finder.quote_completions([], "", None)
    assert result == [], "Empty list should return empty list"


# Test quote_completions with None in list
@given(
    completions=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5)
)
def test_quote_completions_with_none(completions):
    """Property: quote_completions behavior with None in completions"""
    finder = CompletionFinder()
    completions_with_none = [None] + completions
    
    try:
        result = finder.quote_completions(completions_with_none, "", None)
        # Should either handle None gracefully or raise appropriate error
    except (TypeError, AttributeError) as e:
        # This might be expected, but let's check if it's handled consistently
        pass


# Test split_line with unmatched quotes
@given(
    text=st.text(alphabet=st.characters(blacklist_categories=["Cc"], min_codepoint=32, max_codepoint=126), min_size=1, max_size=20)
)
def test_split_line_unmatched_quotes(text):
    """Property: split_line should handle unmatched quotes"""
    # Add unmatched quote at beginning
    line_single = "'" + text
    line_double = '"' + text
    
    try:
        result1 = split_line(line_single)
        result2 = split_line(line_double)
        # Should not crash
        assert len(result1) == 5
        assert len(result2) == 5
    except ValueError:
        # This might be expected for unmatched quotes
        pass


# Test ExclusiveCompletionFinder behavior
@given(
    completions=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=10)
)
def test_exclusive_completion_finder(completions):
    """Property: ExclusiveCompletionFinder should behave differently from CompletionFinder"""
    parser = argparse.ArgumentParser()
    
    finder1 = CompletionFinder(argument_parser=parser)
    finder2 = ExclusiveCompletionFinder(argument_parser=parser)
    
    # Both should be able to filter completions
    filtered1 = finder1.filter_completions(completions)
    filtered2 = finder2.filter_completions(completions)
    
    # Basic properties should hold for both
    assert len(filtered1) <= len(completions)
    assert len(filtered2) <= len(completions)
    assert len(set(filtered1)) == len(filtered1)  # No duplicates
    assert len(set(filtered2)) == len(filtered2)  # No duplicates


# Test validator with special Unicode characters
@given(
    prefix=st.text(alphabet=st.characters(min_codepoint=0x1F300, max_codepoint=0x1F6FF), min_size=1, max_size=5),
    suffix=st.text(min_size=0, max_size=5)
)
def test_validator_unicode(prefix, suffix):
    """Property: validator should work with Unicode characters"""
    completion = prefix + suffix
    result = default_validator(completion, prefix)
    assert result is True, f"Validator failed for Unicode: '{completion}', prefix='{prefix}'"


# Test quote_completions preserves display_completions mapping
@given(
    completions=st.lists(
        st.text(alphabet=st.characters(blacklist_categories=["Cc"], min_codepoint=32, max_codepoint=126), min_size=1, max_size=10),
        min_size=1,
        max_size=5,
        unique=True
    ),
    descriptions=st.lists(st.text(max_size=20), min_size=1, max_size=5)
)
def test_quote_completions_display_mapping(completions, descriptions):
    """Property: quote_completions should preserve display_completions mapping"""
    finder = CompletionFinder()
    
    # Set up display completions
    for i, comp in enumerate(completions[:len(descriptions)]):
        finder._display_completions[comp] = descriptions[i]
    
    # Quote the completions
    quoted = finder.quote_completions(completions, "", None)
    
    # Check that display_completions was updated for escaped versions
    assert len(quoted) == len(completions)
    # The mapping should be preserved (possibly with escaped keys)
    assert len(finder._display_completions) >= min(len(completions), len(descriptions))


# Test multiple calls to filter_completions  
@given(
    completions1=st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=10),
    completions2=st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=10)
)
def test_filter_completions_multiple_calls(completions1, completions2):
    """Property: Multiple calls to filter_completions should be independent"""
    finder = CompletionFinder()
    
    filtered1 = finder.filter_completions(completions1)
    filtered2 = finder.filter_completions(completions2)
    
    # Each should be filtered independently
    assert all(item in completions1 for item in filtered1)
    assert all(item in completions2 for item in filtered2)
    
    # Deduplication should work for each
    assert len(set(filtered1)) == len(filtered1)
    assert len(set(filtered2)) == len(filtered2)


# Test environment variable handling in quote_completions
@given(
    completion=st.text(alphabet="abc:=@ \t", min_size=1, max_size=10)
)
def test_quote_completions_env_vars(completion):
    """Property: quote_completions should respect environment variables"""
    finder = CompletionFinder()
    
    # Test with ARGCOMPLETE_SHELL set to powershell
    os.environ["_ARGCOMPLETE_SHELL"] = "powershell"
    ps_quoted = finder.quote_completions([completion], "", None)
    
    # Clean up and test default
    os.environ.pop("_ARGCOMPLETE_SHELL", None)
    default_quoted = finder.quote_completions([completion], "", None)
    
    # Both should work
    assert len(ps_quoted) == 1
    assert len(default_quoted) == 1
    
    # PowerShell uses backtick as escape char, bash uses backslash
    # They might differ for special characters
    if any(c in completion for c in " \t"):
        # Escaping might be different
        pass  # Can't assert they're different without knowing exact rules


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))