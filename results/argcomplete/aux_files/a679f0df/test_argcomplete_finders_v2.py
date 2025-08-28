import os
import sys
import argparse
from hypothesis import given, strategies as st, assume, settings, example
import argcomplete.finders as finders
from argcomplete.finders import CompletionFinder, default_validator
from argcomplete.lexers import split_line


# Test split_line with position parameter
@given(
    text=st.text(alphabet=st.characters(blacklist_categories=["Cc"], min_codepoint=32, max_codepoint=126), min_size=1, max_size=50),
    position=st.integers(min_value=0)
)
def test_split_line_position_bounds(text, position):
    """Property: split_line with position <= len(text) should not crash"""
    # Ensure position is within bounds
    position = min(position, len(text))
    
    try:
        prequote, prefix, suffix, words, wordbreak_pos = split_line(text, position)
        # The prefix + suffix should be part of the original text at the position
        assert prefix + suffix in text or prefix == "" or suffix == "", \
            f"prefix '{prefix}' + suffix '{suffix}' not found in '{text}'"
    except Exception as e:
        # split_line should handle any valid position without crashing
        assert False, f"split_line crashed with text='{text}', position={position}: {e}"


# Test CompletionFinder.quote_completions round-trip property
@given(
    text=st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=90), min_size=1, max_size=20)
)
def test_quote_completions_simple_roundtrip(text):
    """Property: For simple alphanumeric text, quoting should be reversible"""
    finder = CompletionFinder()
    
    # Quote the completion
    quoted = finder.quote_completions([text], "", None)
    assert len(quoted) == 1
    
    # If we added a space, remove it
    result = quoted[0]
    if result.endswith(" "):
        result = result[:-1]
    
    # For simple text with no special chars, it should be unchanged
    assert result == text, f"Simple text '{text}' changed to '{result}'"


# Test edge case: empty string handling
@given(
    completions=st.lists(st.text(min_size=0, max_size=10), min_size=0, max_size=5)
)
def test_filter_completions_empty_strings(completions):
    """Property: filter_completions should handle empty strings correctly"""
    finder = CompletionFinder()
    filtered = finder.filter_completions(completions)
    
    # Count empty strings
    empty_in = completions.count("")
    empty_out = filtered.count("")
    
    # Should have at most one empty string (deduplication)
    assert empty_out <= 1, f"Multiple empty strings in output: {filtered}"
    
    # If input had empty string, output should have at most one
    if empty_in > 0:
        assert empty_out <= 1, f"Empty string not properly deduplicated"


# Test validator with empty prefix
@given(
    completion=st.text(min_size=0, max_size=30)
)
def test_default_validator_empty_prefix(completion):
    """Property: default_validator with empty prefix should always return True"""
    result = default_validator(completion, "")
    assert result is True, f"Validator failed with empty prefix for '{completion}'"


# Test CompletionFinder initialization and state
@given(
    always_complete=st.sampled_from([True, False, "long", "short"]),
    print_suppressed=st.booleans(),
    append_space=st.booleans()
)
def test_completion_finder_initialization(always_complete, print_suppressed, append_space):
    """Property: CompletionFinder should initialize correctly with various options"""
    parser = argparse.ArgumentParser()
    finder = CompletionFinder(
        argument_parser=parser,
        always_complete_options=always_complete,
        print_suppressed=print_suppressed,
        append_space=append_space
    )
    
    assert finder._parser == parser
    assert finder.always_complete_options == always_complete
    assert finder.print_suppressed == print_suppressed
    assert finder.append_space == append_space
    assert finder.completing is False
    assert isinstance(finder._display_completions, dict)


# Test quote_completions with different quote types
@given(
    text=st.text(alphabet=st.characters(blacklist_categories=["Cc"], min_codepoint=32, max_codepoint=126), min_size=1, max_size=20)
)
@settings(max_examples=200)
def test_quote_completions_with_prequote(text):
    """Property: quote_completions should handle different prequote characters"""
    finder = CompletionFinder()
    
    # Test with double quote
    quoted_double = finder.quote_completions([text], '"', None)
    assert len(quoted_double) == 1
    
    # Test with single quote
    quoted_single = finder.quote_completions([text], "'", None)
    assert len(quoted_single) == 1
    
    # Both should produce valid results
    assert quoted_double[0] is not None
    assert quoted_single[0] is not None


# Test the escaping of special characters in different shells
@given(
    completion=st.text(alphabet="abc$!`'\"\\", min_size=1, max_size=10)
)
def test_quote_completions_shell_specific(completion):
    """Property: Different shells should have different escaping rules"""
    finder = CompletionFinder()
    
    # Test default (bash) behavior
    os.environ.pop("_ARGCOMPLETE_SHELL", None)
    bash_quoted = finder.quote_completions([completion], "", None)
    
    # Test zsh behavior
    os.environ["_ARGCOMPLETE_SHELL"] = "zsh"
    zsh_quoted = finder.quote_completions([completion], "", None)
    
    # Test fish behavior
    os.environ["_ARGCOMPLETE_SHELL"] = "fish"
    fish_quoted = finder.quote_completions([completion], "", None)
    
    # Clean up
    os.environ.pop("_ARGCOMPLETE_SHELL", None)
    
    # All should produce results
    assert len(bash_quoted) == 1
    assert len(zsh_quoted) == 1
    assert len(fish_quoted) == 1


# Test split_line with special COMP_WORDBREAKS characters
@given(
    text=st.text(alphabet="abc:=@", min_size=2, max_size=20)
)
def test_split_line_with_wordbreaks(text):
    """Property: split_line should handle COMP_WORDBREAKS characters"""
    # Set custom wordbreaks
    os.environ["_ARGCOMPLETE_COMP_WORDBREAKS"] = ":="
    
    try:
        prequote, prefix, suffix, words, wordbreak_pos = split_line(text)
        # Should not crash and should return valid results
        assert isinstance(prequote, str)
        assert isinstance(prefix, str)
        assert isinstance(suffix, str)
        assert isinstance(words, list)
        # wordbreak_pos can be None or an integer
        assert wordbreak_pos is None or isinstance(wordbreak_pos, int)
    finally:
        # Clean up
        os.environ.pop("_ARGCOMPLETE_COMP_WORDBREAKS", None)


# Test quote_completions length invariant
@given(
    completions=st.lists(
        st.text(alphabet=st.characters(blacklist_categories=["Cc"], min_codepoint=32, max_codepoint=126), min_size=1, max_size=10),
        min_size=1,
        max_size=20
    )
)
def test_quote_completions_length_invariant(completions):
    """Property: quote_completions should return same number of completions"""
    finder = CompletionFinder()
    quoted = finder.quote_completions(completions, "", None)
    
    assert len(quoted) == len(completions), \
        f"Length changed from {len(completions)} to {len(quoted)}"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))