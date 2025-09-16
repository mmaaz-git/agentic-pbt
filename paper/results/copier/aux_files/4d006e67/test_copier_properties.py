"""Property-based tests for copier library using Hypothesis."""

import sys
import os
from decimal import Decimal
from enum import Enum

# Add the copier path to sys.path  
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

import hypothesis.strategies as st
from hypothesis import given, assume, settings

# Import copier functions
from copier._tools import (
    cast_to_bool,
    cast_to_str,
    force_str_end,
    normalize_git_path,
    escape_git_path,
)


# Property 1: force_str_end should always ensure the string ends with the specified ending
@given(
    original_str=st.text(),
    end=st.text(min_size=1)  # Ensure end is not empty
)
def test_force_str_end_property(original_str, end):
    """Test that force_str_end always makes the string end with the specified ending."""
    result = force_str_end(original_str, end)
    assert result.endswith(end), f"Result '{result}' doesn't end with '{end}'"
    
    # Also test that if the string already ends with 'end', it shouldn't be duplicated
    if original_str.endswith(end):
        assert result == original_str


# Property 2: force_str_end idempotence - applying it twice should be the same as once
@given(
    original_str=st.text(),
    end=st.text(min_size=1)
)
def test_force_str_end_idempotent(original_str, end):
    """Test that applying force_str_end twice gives the same result as applying once."""
    once = force_str_end(original_str, end)
    twice = force_str_end(once, end)
    assert once == twice


# Property 3: cast_to_bool with numeric strings
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_cast_to_bool_numeric(value):
    """Test cast_to_bool with numeric values."""
    result = cast_to_bool(value)
    # According to the function, 0 should be False, everything else True
    if value == 0:
        assert result is False
    else:
        assert result is True


# Property 4: cast_to_bool with string representations of booleans
@given(st.sampled_from(["y", "yes", "t", "true", "on", "Y", "YES", "T", "TRUE", "ON"]))
def test_cast_to_bool_true_strings(value):
    """Test that known true strings are converted to True."""
    assert cast_to_bool(value) is True


@given(st.sampled_from(["n", "no", "f", "false", "off", "~", "null", "none", 
                        "N", "NO", "F", "FALSE", "OFF", "NULL", "NONE"]))
def test_cast_to_bool_false_strings(value):
    """Test that known false strings are converted to False."""
    assert cast_to_bool(value) is False


# Property 5: cast_to_str with various types
@given(st.one_of(
    st.text(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.decimals(allow_nan=False, allow_infinity=False),
))
def test_cast_to_str_basic_types(value):
    """Test cast_to_str with basic types."""
    result = cast_to_str(value)
    assert isinstance(result, str)
    
    # For numeric types, the string representation should be parseable back
    if isinstance(value, (int, float, Decimal)):
        assert str(value) == result


# Property 6: cast_to_str with bytes
@given(st.binary())
def test_cast_to_str_bytes(value):
    """Test cast_to_str with bytes."""
    # The function decodes bytes as utf-8
    # We need to ensure the bytes are valid utf-8
    try:
        expected = value.decode('utf-8')
        result = cast_to_str(value)
        assert result == expected
    except UnicodeDecodeError:
        # Skip invalid utf-8 sequences
        pass


# Property 7: normalize_git_path handles quoted paths correctly
@given(st.text(min_size=2))
def test_normalize_git_path_quoted(path):
    """Test normalize_git_path with quoted paths."""
    # When a path is surrounded by quotes, they should be removed
    quoted_path = f'"{path}"'
    result = normalize_git_path(quoted_path)
    # The quotes should be gone (unless they were escaped)
    assert not (result.startswith('"') and result.endswith('"'))


# Property 8: escape_git_path escapes backslashes
@given(st.text())
def test_escape_git_path_backslashes(path):
    """Test that escape_git_path properly escapes backslashes."""
    result = escape_git_path(path)
    # Count backslashes - every original backslash should be doubled
    original_backslashes = path.count('\\')
    # The result should have at least as many backslashes (they get doubled)
    # Note: This is a simplified test as escape_git_path does more complex escaping
    if '\\' in path:
        assert '\\\\' in result or result.count('\\') >= original_backslashes


# Property 9: Round-trip property for simple paths (without special characters)
@given(st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126, 
                                      blacklist_characters='"\\[]?*')))
def test_git_path_simple_roundtrip(path):
    """Test that simple paths remain unchanged through escape."""
    # For simple paths without special characters, escaping should not change them much
    escaped = escape_git_path(path)
    # The escaped path should at least contain all the original characters
    # (though they might be escaped)
    for char in path:
        if char not in ' \t\n\r':  # Whitespace gets special treatment
            assert char in escaped or f'\\{char}' in escaped


# Property 10: force_str_end with default newline
@given(st.text())
def test_force_str_end_default_newline(text):
    """Test force_str_end with default newline ending."""
    result = force_str_end(text)
    assert result.endswith('\n')
    # If text already ended with newline, it shouldn't be duplicated
    if text.endswith('\n'):
        assert result == text
    else:
        assert result == text + '\n'


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])