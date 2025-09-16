#!/usr/bin/env python3
"""More intensive property-based tests for win32ctypes.core module"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pywin32-ctypes_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
from win32ctypes.core import compat


# Test with many examples and diverse inputs
@settings(max_examples=10000)
@given(st.one_of(
    st.binary(),
    st.text(),
    st.integers(),
    st.floats(),
    st.booleans(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.tuples(st.integers(), st.text()),
    st.sets(st.integers()),
    st.frozensets(st.integers()),
    st.complex_numbers(),
    st.fractions(),
    st.decimals(),
    st.datetimes(),
    st.dates(),
    st.times(),
    st.timedeltas(),
    st.uuids(),
))
def test_type_checking_consistency(obj):
    """Type checking functions should be mutually exclusive for non-bool types"""
    is_bytes_result = compat.is_bytes(obj)
    is_text_result = compat.is_text(obj)
    is_integer_result = compat.is_integer(obj)
    
    # Count how many return True
    true_count = sum([is_bytes_result, is_text_result, is_integer_result])
    
    # Special case: bool is a subclass of int in Python
    if isinstance(obj, bool):
        # bool should be recognized as integer
        assert is_integer_result is True
        assert is_bytes_result is False
        assert is_text_result is False
    elif isinstance(obj, bytes):
        assert is_bytes_result is True
        assert is_text_result is False
        assert is_integer_result is False
    elif isinstance(obj, str):
        assert is_text_result is True
        assert is_bytes_result is False
        assert is_integer_result is False
    elif isinstance(obj, int) and not isinstance(obj, bool):
        assert is_integer_result is True
        assert is_bytes_result is False
        assert is_text_result is False
    else:
        # For all other types, all should return False
        assert is_bytes_result is False
        assert is_text_result is False
        assert is_integer_result is False


@settings(max_examples=10000)
@given(st.one_of(st.binary(), st.binary(min_size=0, max_size=10000)))
def test_is_bytes_comprehensive(b):
    """Comprehensive test for is_bytes with various byte sizes"""
    result = compat.is_bytes(b)
    assert result is True
    # Verify it's actually bytes
    assert isinstance(b, bytes)


@settings(max_examples=10000)
@given(st.text(alphabet=st.characters(codec='utf-8', categories=['Ll', 'Lu', 'Lt', 'Lo', 'Nd', 'Pc', 'Sm', 'Sc', 'Sk', 'So'])))
def test_is_text_unicode(s):
    """Test is_text with various Unicode categories"""
    assert compat.is_text(s) is True


@settings(max_examples=10000)
@given(st.integers(min_value=-2**1000, max_value=2**1000))
def test_is_integer_large_numbers(i):
    """Test is_integer with very large numbers"""
    assert compat.is_integer(i) is True


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])