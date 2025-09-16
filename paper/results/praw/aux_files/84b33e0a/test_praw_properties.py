"""Property-based tests for praw.reddit and praw.util modules."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from praw.util import snake
import string
import re


# Strategy for generating camelCase-like strings
camel_case_strategy = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=0,
    max_size=100
)

# Strategy for dictionary keys (valid Python identifiers)
identifier_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "_",
    min_size=1,
    max_size=50
).filter(lambda s: s[0].isalpha() or s[0] == '_')


@given(camel_case_strategy)
def test_camel_to_snake_idempotence(text):
    """Test that applying camel_to_snake twice is the same as applying it once."""
    once = snake.camel_to_snake(text)
    twice = snake.camel_to_snake(once)
    assert once == twice, f"Not idempotent for input '{text}': {once} != {twice}"


@given(camel_case_strategy)
def test_camel_to_snake_always_lowercase(text):
    """Test that camel_to_snake always produces lowercase output."""
    result = snake.camel_to_snake(text)
    assert result == result.lower(), f"Output not lowercase for input '{text}': {result}"


@given(st.text())
def test_camel_to_snake_empty_string_preserved(text):
    """Test that empty strings are handled correctly."""
    if text == "":
        result = snake.camel_to_snake(text)
        assert result == "", "Empty string should remain empty"


@given(st.text(min_size=0, max_size=200))
def test_camel_to_snake_length_reasonable(text):
    """Test that the output length is reasonable compared to input."""
    result = snake.camel_to_snake(text)
    # The result should not be more than 2x the original length
    # (accounting for underscores being added)
    assert len(result) <= len(text) * 2 + 10, f"Output too long for '{text}': {len(result)} vs {len(text)}"


@given(st.dictionaries(
    keys=identifier_strategy,
    values=st.one_of(
        st.integers(),
        st.text(),
        st.booleans(),
        st.none(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    ),
    min_size=0,
    max_size=50
))
def test_snake_case_keys_value_preservation(dictionary):
    """Test that snake_case_keys preserves all values unchanged."""
    result = snake.snake_case_keys(dictionary)
    
    # All values should be preserved
    original_values = set(str(v) for v in dictionary.values())
    result_values = set(str(v) for v in result.values())
    
    assert original_values == result_values, f"Values changed: {original_values} != {result_values}"


@given(st.dictionaries(
    keys=identifier_strategy,
    values=st.integers(),
    min_size=0,
    max_size=50
))
def test_snake_case_keys_count_preservation(dictionary):
    """Test that snake_case_keys preserves the number of keys."""
    result = snake.snake_case_keys(dictionary)
    assert len(result) == len(dictionary), f"Key count changed: {len(dictionary)} -> {len(result)}"


@given(st.dictionaries(
    keys=st.text(alphabet=string.ascii_letters, min_size=1, max_size=20),
    values=st.integers()
))
def test_snake_case_keys_no_key_collision(dictionary):
    """Test that snake_case_keys doesn't cause key collisions for distinct keys."""
    # If all original keys are distinct, the transformed keys should also be distinct
    result = snake.snake_case_keys(dictionary)
    
    # The number of unique keys should remain the same
    # unless there were actual collisions in the camel_to_snake transformation
    if len(set(dictionary.keys())) == len(dictionary):
        assert len(set(result.keys())) == len(result), \
            f"Key collision detected: {dictionary.keys()} -> {result.keys()}"


@given(st.text(alphabet=string.ascii_lowercase + "_", min_size=0, max_size=50))
def test_camel_to_snake_already_snake_case(text):
    """Test that strings already in snake_case remain unchanged."""
    # If the input is already in snake_case (all lowercase with underscores),
    # it should remain unchanged
    result = snake.camel_to_snake(text)
    assert result == text, f"Snake case input changed: '{text}' -> '{result}'"


@given(st.text(alphabet=string.ascii_uppercase, min_size=1, max_size=20))
def test_camel_to_snake_all_caps(text):
    """Test handling of all-caps strings."""
    result = snake.camel_to_snake(text)
    # All caps should become all lowercase
    assert result == text.lower(), f"All caps not handled correctly: '{text}' -> '{result}'"


@given(st.text())
def test_camel_to_snake_no_crash(text):
    """Test that camel_to_snake doesn't crash on any string input."""
    try:
        result = snake.camel_to_snake(text)
        assert isinstance(result, str), f"Output is not a string: {type(result)}"
    except Exception as e:
        assert False, f"Function crashed on input '{text}': {e}"


# Test with specific patterns that might be problematic
@given(st.text(alphabet=string.digits, min_size=0, max_size=50))
def test_camel_to_snake_numeric_strings(text):
    """Test handling of purely numeric strings."""
    result = snake.camel_to_snake(text)
    # Numeric strings should remain unchanged (just lowercase, but digits don't have case)
    assert result == text, f"Numeric string changed: '{text}' -> '{result}'"


@given(st.text(alphabet=string.ascii_letters + string.digits).filter(
    lambda s: len(s) > 0 and any(c.isupper() for c in s)
))
def test_camel_to_snake_mixed_case_produces_underscores(text):
    """Test that mixed case strings produce underscores where expected."""
    result = snake.camel_to_snake(text)
    
    # If there's a lowercase letter followed by an uppercase letter,
    # there should be an underscore in the result
    has_camel_transition = any(
        i < len(text) - 1 and text[i].islower() and text[i+1].isupper()
        for i in range(len(text))
    )
    
    if has_camel_transition:
        assert '_' in result, f"No underscore added for camelCase input: '{text}' -> '{result}'"


@given(st.dictionaries(
    keys=st.text(min_size=1, max_size=10),
    values=st.integers()
).filter(lambda d: len(d) > 0))
def test_snake_case_keys_empty_key_handling(dictionary):
    """Test that snake_case_keys handles various key types correctly."""
    # Ensure we can process the dictionary without errors
    try:
        result = snake.snake_case_keys(dictionary)
        assert isinstance(result, dict), f"Output is not a dict: {type(result)}"
    except Exception as e:
        assert False, f"Function crashed on dictionary {dictionary}: {e}"


if __name__ == "__main__":
    # Run with verbose output
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])