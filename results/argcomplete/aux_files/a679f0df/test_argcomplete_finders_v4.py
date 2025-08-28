import os
import sys
import argparse
from hypothesis import given, strategies as st, assume, settings, example
import argcomplete.finders as finders
from argcomplete.finders import CompletionFinder, default_validator
from argcomplete.lexers import split_line


# Test for inconsistency in filter_completions with duplicate handling
@given(
    base_list=st.lists(st.text(alphabet="abc", min_size=1, max_size=3), min_size=2, max_size=5, unique=True),
    duplicate_count=st.integers(min_value=1, max_value=3)
)
def test_filter_completions_duplicate_order(base_list, duplicate_count):
    """Property: filter_completions should maintain first occurrence when deduplicating"""
    # Create list with duplicates at specific positions
    completions = []
    for item in base_list:
        completions.append(item)
        for _ in range(duplicate_count):
            completions.append(item)
    
    finder = CompletionFinder()
    filtered = finder.filter_completions(completions)
    
    # Check that we keep first occurrence
    for item in base_list:
        first_index = completions.index(item)
        if item in filtered:
            filtered_index = filtered.index(item)
            # The filtered index should correspond to first occurrence pattern
            assert filtered.count(item) == 1, f"Item '{item}' appears multiple times after deduplication"


# Test quote_completions with last_wordbreak_pos edge cases
@given(
    completion=st.text(alphabet="abc:def=ghi@jkl", min_size=5, max_size=20),
    wordbreak_pos=st.integers(min_value=-10, max_value=30)
)
def test_quote_completions_wordbreak_edge_cases(completion, wordbreak_pos):
    """Property: quote_completions should handle any wordbreak_pos value"""
    finder = CompletionFinder()
    
    try:
        # This might trim the completion based on wordbreak_pos
        result = finder.quote_completions([completion], "", wordbreak_pos)
        assert len(result) == 1
        # If wordbreak_pos is valid and in range, check trimming
        if 0 <= wordbreak_pos < len(completion):
            # Result should be trimmed
            assert len(result[0]) <= len(completion)
    except Exception as e:
        # Should not crash on edge values
        assert False, f"quote_completions crashed with wordbreak_pos={wordbreak_pos}: {e}"


# Test the rl_complete method
@given(
    text=st.text(alphabet=st.characters(blacklist_categories=["Cc"], min_codepoint=32, max_codepoint=126), min_size=1, max_size=20),
    state=st.integers(min_value=0, max_value=10)
)
def test_rl_complete_states(text, state):
    """Property: rl_complete should handle multiple state calls correctly"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--option")
    finder = CompletionFinder(argument_parser=parser)
    
    # Mock sys.argv for the test
    original_argv = sys.argv
    sys.argv = ["test_program"]
    
    try:
        # First call with state=0 initializes
        if state == 0:
            result = finder.rl_complete(text, 0)
            # Should return a string or None
            assert result is None or isinstance(result, str)
        else:
            # Initialize first
            finder.rl_complete(text, 0)
            # Then get state
            result = finder.rl_complete(text, state)
            assert result is None or isinstance(result, str)
    finally:
        sys.argv = original_argv


# Test split_line with very long input
@given(
    char=st.characters(blacklist_categories=["Cc"], min_codepoint=32, max_codepoint=126),
    length=st.integers(min_value=100, max_value=1000)
)
@settings(max_examples=50)
def test_split_line_long_input(char, length):
    """Property: split_line should handle very long inputs"""
    # Create a very long line
    line = char * length
    
    try:
        result = split_line(line)
        prequote, prefix, suffix, words, wordbreak_pos = result
        # Should not crash and return valid structure
        assert isinstance(prefix, str)
        assert len(prefix) <= len(line)
    except Exception as e:
        # Long input shouldn't cause crashes
        assert False, f"split_line crashed on long input: {e}"


# Test validator case sensitivity
@given(
    base=st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=90), min_size=1, max_size=10),
    suffix=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=0, max_size=10)
)
def test_validator_case_sensitivity(base, suffix):
    """Property: default_validator is case-sensitive"""
    completion_upper = base.upper() + suffix
    completion_lower = base.lower() + suffix
    prefix_upper = base.upper()
    prefix_lower = base.lower()
    
    # Same case should match
    assert default_validator(completion_upper, prefix_upper) is True
    assert default_validator(completion_lower, prefix_lower) is True
    
    # Different case should not match
    assert default_validator(completion_upper, prefix_lower) is False
    assert default_validator(completion_lower, prefix_upper) is False


# Test filter_completions exclude parameter interaction
@given(
    all_items=st.lists(st.text(alphabet="abc", min_size=1, max_size=5), min_size=5, max_size=10, unique=True)
)
def test_filter_completions_exclude_all(all_items):
    """Property: Excluding all items should return empty list"""
    finder = CompletionFinder(exclude=all_items)
    filtered = finder.filter_completions(all_items)
    assert filtered == [], f"Expected empty list when excluding all items, got {filtered}"


# Test quote_completions with continuation characters
@given(
    base=st.text(alphabet=st.characters(blacklist_categories=["Cc"], min_codepoint=65, max_codepoint=90), min_size=1, max_size=10),
    continuation=st.sampled_from(["=", "/", ":"])
)
def test_quote_completions_continuation_chars(base, continuation):
    """Property: Completions ending with continuation chars should not get space appended"""
    completion = base + continuation
    finder = CompletionFinder(append_space=True)
    
    result = finder.quote_completions([completion], "", None)
    assert len(result) == 1
    
    # Should not have space appended due to continuation character
    assert not result[0].endswith(" "), \
        f"Completion '{completion}' ending with '{continuation}' got space appended: '{result[0]}'"


# Test split_line with mixed quotes
@given(
    text1=st.text(alphabet=st.characters(blacklist_categories=["Cc"], blacklist_characters='"\''), min_size=1, max_size=10),
    text2=st.text(alphabet=st.characters(blacklist_categories=["Cc"], blacklist_characters='"\''), min_size=1, max_size=10)
)
def test_split_line_mixed_quotes(text1, text2):
    """Property: split_line should handle mixed quote types"""
    line = f'"{text1}" \'{text2}\''
    
    try:
        prequote, prefix, suffix, words, wordbreak_pos = split_line(line)
        # Should parse both quoted strings
        assert len(words) >= 1, f"Expected at least 1 word, got {words}"
        assert text1 in words[0] or text1 == prefix, f"First text '{text1}' not found in result"
    except ValueError:
        # Might fail with unclosed quotes, but shouldn't crash unexpectedly
        pass


# Test CompletionFinder initialization with None parser
def test_completion_finder_none_parser():
    """Property: CompletionFinder should accept None as parser"""
    finder = CompletionFinder(argument_parser=None)
    assert finder._parser is None
    
    # Should still be able to filter completions
    completions = ["test1", "test2", "test1"]
    filtered = finder.filter_completions(completions)
    assert len(filtered) == 2  # Deduplication should work
    assert "test1" in filtered
    assert "test2" in filtered


# Test get_display_completions method
@given(
    items=st.dictionaries(
        keys=st.text(alphabet="abc", min_size=1, max_size=5),
        values=st.text(max_size=10),
        min_size=0,
        max_size=5
    )
)
def test_get_display_completions(items):
    """Property: get_display_completions should return the internal dictionary"""
    finder = CompletionFinder()
    finder._display_completions = items.copy()
    
    result = finder.get_display_completions()
    assert result == items, "get_display_completions should return the exact dictionary"
    
    # Check it's the same object (not a copy)
    assert result is finder._display_completions, "Should return reference, not copy"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))