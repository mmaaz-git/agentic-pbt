import os
import sys
import argparse
from hypothesis import given, strategies as st, assume, settings
import argcomplete.finders as finders
from argcomplete.finders import CompletionFinder, default_validator
from argcomplete.lexers import split_line


# Test 1: default_validator should return True when completion starts with prefix
@given(
    prefix=st.text(min_size=1, max_size=20),
    suffix=st.text(min_size=0, max_size=20)
)
def test_default_validator_prefix_property(prefix, suffix):
    """Property: default_validator(prefix + suffix, prefix) should always be True"""
    completion = prefix + suffix
    result = default_validator(completion, prefix)
    assert result is True, f"Validator failed for completion='{completion}', prefix='{prefix}'"


# Test 2: default_validator should return False when completion doesn't start with prefix
@given(
    completion=st.text(min_size=1, max_size=30),
    prefix=st.text(min_size=1, max_size=30)
)
def test_default_validator_negative_property(completion, prefix):
    """Property: If completion doesn't start with prefix, validator should return False"""
    # Skip cases where completion actually starts with prefix
    assume(not completion.startswith(prefix))
    result = default_validator(completion, prefix)
    assert result is False, f"Validator should fail for completion='{completion}', prefix='{prefix}'"


# Test 3: split_line parsing consistency
@given(
    words=st.lists(
        st.text(alphabet=st.characters(blacklist_categories=["Cc"], blacklist_characters=' \t\n"\'\\'), min_size=1),
        min_size=1,
        max_size=5
    )
)
def test_split_line_simple_words(words):
    """Property: split_line should correctly parse space-separated words"""
    line = " ".join(words)
    prequote, prefix, suffix, parsed_words, wordbreak_pos = split_line(line)
    
    # The parsed words should match the input words
    assert len(parsed_words) == len(words), f"Word count mismatch: expected {len(words)}, got {len(parsed_words)}"
    for original, parsed in zip(words, parsed_words):
        assert original == parsed, f"Word mismatch: '{original}' != '{parsed}'"


# Test 4: split_line with quotes
@given(
    text=st.text(alphabet=st.characters(blacklist_categories=["Cc"], blacklist_characters='"\''), min_size=1, max_size=20)
)
def test_split_line_quoted_text(text):
    """Property: split_line should handle quoted strings properly"""
    # Test with double quotes
    line = f'"{text}"'
    prequote, prefix, suffix, words, wordbreak_pos = split_line(line)
    
    # Should parse as a single word containing the text
    assert len(words) == 1, f"Expected 1 word for quoted text, got {len(words)}"
    assert text in words[0], f"Text '{text}' not found in parsed word '{words[0]}'"


# Test 5: CompletionFinder.filter_completions deduplication
@given(
    completions=st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=20)
)
def test_filter_completions_deduplication(completions):
    """Property: filter_completions should remove duplicates"""
    finder = CompletionFinder()
    filtered = finder.filter_completions(completions)
    
    # Check no duplicates in output
    assert len(filtered) == len(set(filtered)), "filter_completions produced duplicates"
    
    # Check length constraint
    assert len(filtered) <= len(completions), "Filtered list longer than input"
    
    # Check all elements in filtered were in original
    for item in filtered:
        assert item in completions, f"Item '{item}' not in original completions"


# Test 6: CompletionFinder.filter_completions exclusion
@given(
    completions=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=20),
    exclude_indices=st.lists(st.integers(min_value=0, max_value=19), min_size=0, max_size=5)
)
def test_filter_completions_exclusion(completions, exclude_indices):
    """Property: filter_completions should exclude specified items"""
    # Build exclude list from indices
    exclude = []
    for idx in exclude_indices:
        if idx < len(completions):
            exclude.append(completions[idx])
    
    finder = CompletionFinder(exclude=exclude)
    filtered = finder.filter_completions(completions)
    
    # Check that excluded items are not in output
    for excluded_item in exclude:
        assert excluded_item not in filtered, f"Excluded item '{excluded_item}' found in filtered output"


# Test 7: quote_completions with special characters
@given(
    completion=st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=20)
)
@settings(max_examples=500)
def test_quote_completions_escaping(completion):
    """Property: quote_completions should properly escape special characters"""
    finder = CompletionFinder()
    
    # Test without quotes (normal mode)
    quoted = finder.quote_completions([completion], "", None)
    assert len(quoted) == 1, "Should return one completion"
    
    # The result should escape special characters
    special_chars = "();<>|&!`$* \t\n\"'\\"
    result = quoted[0]
    
    # Check that special characters are escaped
    for char in special_chars:
        if char in completion:
            # The character should be escaped in the result (unless it's the last char and a continuation char)
            if char not in "=/:" or result[-1] != char:
                assert "\\" + char in result or result.endswith(" "), \
                    f"Special char '{char}' not properly escaped in '{result}'"


# Test 8: Multiple word completions preserve order
@given(
    completions=st.lists(
        st.text(alphabet=st.characters(blacklist_categories=["Cc"], blacklist_characters=' \t\n'), min_size=1, max_size=10),
        min_size=2,
        max_size=10,
        unique=True
    )
)
def test_filter_completions_preserves_order(completions):
    """Property: filter_completions should preserve the order of completions"""
    finder = CompletionFinder()
    filtered = finder.filter_completions(completions)
    
    # Check that order is preserved
    filtered_indices = [completions.index(item) for item in filtered]
    assert filtered_indices == sorted(filtered_indices), \
        f"Order not preserved: {filtered} from {completions}"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))