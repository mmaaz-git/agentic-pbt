#!/usr/bin/env python3
"""Property-based tests for copier.main and helper functions."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import copier._tools as tools
import copier._main

# Test 1: force_str_end idempotence
@given(
    original_str=st.text(),
    end=st.text(min_size=1, max_size=10)
)
def test_force_str_end_idempotence(original_str, end):
    """Applying force_str_end twice should have the same effect as once."""
    once = tools.force_str_end(original_str, end)
    twice = tools.force_str_end(once, end)
    assert once == twice
    assert twice.endswith(end)


# Test 2: cast_to_bool idempotence
@given(value=st.one_of(
    st.text(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_cast_to_bool_idempotence(value):
    """Casting to bool twice should equal casting once."""
    once = tools.cast_to_bool(value)
    twice = tools.cast_to_bool(once)
    assert once == twice
    assert isinstance(once, bool)


# Test 3: Testing the specific YAML boolean values
@given(value=st.sampled_from(["y", "yes", "t", "true", "on", "Y", "YES", "T", "TRUE", "ON"]))
def test_cast_to_bool_true_values(value):
    """YAML true values should always return True."""
    assert tools.cast_to_bool(value) is True


@given(value=st.sampled_from(["n", "no", "f", "false", "off", "~", "null", "none", "N", "NO", "F", "FALSE", "OFF", "NULL", "NONE"]))
def test_cast_to_bool_false_values(value):
    """YAML false values should always return False."""
    assert tools.cast_to_bool(value) is False


# Test 4: cast_to_bool numeric behavior
@given(value=st.floats(allow_nan=False, allow_infinity=False))
def test_cast_to_bool_numeric(value):
    """Numeric values should be False for 0, True otherwise."""
    result = tools.cast_to_bool(value)
    if value == 0:
        assert result is False
    else:
        assert result is True


# Test 5: normalize_git_path and escape_git_path relationship
@given(path=st.text(min_size=1))
def test_escape_normalize_git_path(path):
    """Test the relationship between escape and normalize git path functions."""
    # Skip paths with null bytes which are invalid in filenames
    assume('\x00' not in path)
    
    # Escape then normalize should preserve certain properties
    escaped = tools.escape_git_path(path)
    
    # The escaped path should not contain unescaped special git wildcard characters
    # unless they were already escaped
    assert escaped == tools.escape_git_path(tools.normalize_git_path(escaped))


# Test 6: cast_to_str on various types
@given(value=st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.binary()
))
def test_cast_to_str_types(value):
    """cast_to_str should successfully convert supported types."""
    try:
        result = tools.cast_to_str(value)
        assert isinstance(result, str)
        
        # For numeric types, converting back should preserve value
        if isinstance(value, int):
            assert int(result) == value
        elif isinstance(value, float):
            assert float(result) == value
        elif isinstance(value, bytes):
            assert result == value.decode()
    except ValueError:
        # The function raises ValueError for unsupported types
        # This is expected for some inputs
        pass


# Test 7: Path normalization preserves UTF-8 validity
@given(path=st.text(min_size=1))
def test_normalize_git_path_utf8(path):
    """normalize_git_path should always return valid UTF-8 strings."""
    # Skip if the path starts and ends with quotes but has odd escaping
    if path and path[0] == '"' and path[-1] == '"':
        # This mimics git-quoted paths
        try:
            normalized = tools.normalize_git_path(path)
            # Result should be valid UTF-8 (this will raise if not)
            normalized.encode('utf-8')
            assert isinstance(normalized, str)
        except (IndexError, UnicodeDecodeError, UnicodeEncodeError):
            # Some malformed inputs may cause issues, which is acceptable
            pass
    else:
        # Non-quoted paths should pass through with some transformations
        normalized = tools.normalize_git_path(path)
        assert isinstance(normalized, str)


# Test 8: Round-trip for git path with specific patterns
@given(path=st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1))
def test_git_path_ascii_roundtrip(path):
    """For ASCII paths without quotes, operations should be stable."""
    assume('"' not in path)
    assume('\\' not in path)
    
    # For simple ASCII paths, escape should be stable
    escaped1 = tools.escape_git_path(path)
    escaped2 = tools.escape_git_path(escaped1)
    assert escaped1 == escaped2


# Test 9: force_str_end with empty end
def test_force_str_end_empty_end():
    """force_str_end with empty end should return original string."""
    test_strings = ["hello", "world", "", "test\n", "foo\nbar"]
    for s in test_strings:
        assert tools.force_str_end(s, "") == s


# Test 10: cast_to_bool on string representations of numbers
@given(num=st.integers())
def test_cast_to_bool_string_numbers(num):
    """String representations of numbers should behave like the numbers."""
    str_num = str(num)
    assert tools.cast_to_bool(str_num) == tools.cast_to_bool(num)


if __name__ == "__main__":
    # Run a quick check on all tests
    import pytest
    pytest.main([__file__, "-v"])