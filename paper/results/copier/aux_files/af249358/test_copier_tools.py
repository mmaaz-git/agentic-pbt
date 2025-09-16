"""Property-based tests for copier.tools module."""

import sys
import os
from enum import Enum
from decimal import Decimal

import pytest
from hypothesis import given, strategies as st, assume, settings

# Add the venv site-packages to path to import copier
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier._tools import (
    cast_to_str,
    cast_to_bool,
    force_str_end,
    normalize_git_path,
    escape_git_path,
    try_enum,
)


# Test 1: cast_to_str properties
@given(st.text())
def test_cast_to_str_preserves_strings(s):
    """String values should be preserved as-is."""
    result = cast_to_str(s)
    assert result == s
    assert isinstance(result, str)


@given(st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False)))
def test_cast_to_str_converts_numbers(num):
    """Numbers should be converted to their string representation."""
    result = cast_to_str(num)
    assert result == str(num)
    assert isinstance(result, str)


@given(st.binary())
def test_cast_to_str_decodes_bytes(data):
    """Bytes should be decoded to strings."""
    try:
        result = cast_to_str(data)
        assert isinstance(result, str)
        assert result == data.decode()
    except UnicodeDecodeError:
        # Skip invalid UTF-8 sequences
        pass


@given(st.decimals(allow_nan=False, allow_infinity=False))
def test_cast_to_str_handles_decimal(d):
    """Decimal values should be converted to string."""
    result = cast_to_str(d)
    assert result == str(d)
    assert isinstance(result, str)


# Test 2: cast_to_bool properties
@given(st.sampled_from(["y", "yes", "t", "true", "on", "Y", "YES", "T", "TRUE", "ON"]))
def test_cast_to_bool_true_strings(s):
    """YAML true strings should convert to True."""
    assert cast_to_bool(s) is True


@given(st.sampled_from(["n", "no", "f", "false", "off", "~", "null", "none", 
                         "N", "NO", "F", "FALSE", "OFF", "NULL", "NONE"]))
def test_cast_to_bool_false_strings(s):
    """YAML false strings should convert to False."""
    assert cast_to_bool(s) is False


@given(st.integers())
def test_cast_to_bool_numeric_strings(n):
    """Numeric strings: 0 should be False, non-zero should be True."""
    str_n = str(n)
    result = cast_to_bool(str_n)
    if n == 0:
        assert result is False
    else:
        assert result is True


@given(st.floats(allow_nan=False))
def test_cast_to_bool_float_strings(f):
    """Float strings: 0.0 should be False, non-zero should be True."""
    str_f = str(f)
    result = cast_to_bool(str_f)
    if f == 0.0:
        assert result is False
    else:
        assert result is True


# Test 3: force_str_end properties
@given(st.text(), st.text(min_size=1))
def test_force_str_end_idempotence(s, end):
    """Applying force_str_end twice should give the same result."""
    result1 = force_str_end(s, end)
    result2 = force_str_end(result1, end)
    assert result1 == result2


@given(st.text(), st.text(min_size=1))
def test_force_str_end_always_ends_with(s, end):
    """Result should always end with the specified ending."""
    result = force_str_end(s, end)
    assert result.endswith(end)


@given(st.text(min_size=1))
def test_force_str_end_no_duplication(s):
    """If string already ends with suffix, it shouldn't be duplicated."""
    # Test with newline (default)
    s_with_nl = s + "\n"
    result = force_str_end(s_with_nl)
    assert result.count("\n") == s.count("\n") + 1


# Test 4: Git path normalization and escaping
@given(st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs"))))
def test_git_path_escape_preserves_normal_paths(path):
    """Escaping a normal path should preserve most characters."""
    assume(not any(c in path for c in ['*', '?', '[', ']', '\\']))
    escaped = escape_git_path(path)
    # Should not change much for normal paths
    # Backslashes and special git wildcards should be escaped
    assert all(c in escaped for c in path if c not in ' \t\n')


@given(st.text(min_size=1))
def test_normalize_git_path_handles_quotes(path):
    """normalize_git_path should handle quoted paths."""
    # Add quotes around the path
    quoted = f'"{path}"'
    result = normalize_git_path(quoted)
    # Result should not have surrounding quotes
    if len(path) >= 2 and path[0] != '"' and path[-1] != '"':
        assert not (result.startswith('"') and result.endswith('"'))


@given(st.text())
def test_escape_git_path_escapes_backslashes(path):
    """escape_git_path should escape backslashes."""
    if '\\' in path:
        escaped = escape_git_path(path)
        # Each backslash should be doubled
        assert escaped.count('\\\\') >= path.count('\\')


# Test 5: try_enum properties
class TestEnum(Enum):
    VALUE1 = 1
    VALUE2 = 2
    VALUE3 = "three"


@given(st.sampled_from([1, 2, "three"]))
def test_try_enum_valid_values(value):
    """Valid enum values should return the enum member."""
    result = try_enum(TestEnum, value)
    assert isinstance(result, TestEnum)
    assert result.value == value


@given(st.one_of(st.integers(), st.text()).filter(lambda x: x not in [1, 2, "three"]))
def test_try_enum_invalid_values(value):
    """Invalid enum values should return the original value."""
    result = try_enum(TestEnum, value)
    assert result == value
    assert not isinstance(result, TestEnum)


@given(st.integers())
def test_try_enum_preserves_type_for_invalid(value):
    """try_enum should preserve the type of invalid values."""
    assume(value not in [1, 2])  # Exclude valid enum values
    result = try_enum(TestEnum, value)
    assert type(result) == type(value)
    assert result == value


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])