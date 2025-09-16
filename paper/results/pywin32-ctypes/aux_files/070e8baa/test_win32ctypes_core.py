#!/usr/bin/env python3
"""Property-based tests for win32ctypes.core module"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pywin32-ctypes_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import hypothesis
import math
import struct

# Import the module components we can test
from win32ctypes.core import compat

# Import ctypes for testing IS_INTRESOURCE
import ctypes
from ctypes import c_void_p


# Test the type checking functions from compat.py
@given(st.binary())
def test_is_bytes_with_bytes(b):
    """is_bytes should return True for bytes objects"""
    assert compat.is_bytes(b) is True


@given(st.text())
def test_is_bytes_with_text(s):
    """is_bytes should return False for str objects"""
    assert compat.is_bytes(s) is False


@given(st.integers())
def test_is_bytes_with_integers(i):
    """is_bytes should return False for integers"""
    assert compat.is_bytes(i) is False


@given(st.lists(st.integers()))
def test_is_bytes_with_lists(lst):
    """is_bytes should return False for lists"""
    assert compat.is_bytes(lst) is False


@given(st.one_of(st.none(), st.floats(), st.booleans(), st.dictionaries(st.text(), st.integers())))
def test_is_bytes_with_other_types(obj):
    """is_bytes should return False for other types"""
    assert compat.is_bytes(obj) is False


@given(st.text())
def test_is_text_with_text(s):
    """is_text should return True for str objects"""
    assert compat.is_text(s) is True


@given(st.binary())
def test_is_text_with_bytes(b):
    """is_text should return False for bytes objects"""
    assert compat.is_text(b) is False


@given(st.integers())
def test_is_text_with_integers(i):
    """is_text should return False for integers"""
    assert compat.is_text(i) is False


@given(st.one_of(st.none(), st.floats(), st.booleans(), st.lists(st.integers())))
def test_is_text_with_other_types(obj):
    """is_text should return False for other types"""
    assert compat.is_text(obj) is False


@given(st.integers())
def test_is_integer_with_integers(i):
    """is_integer should return True for int objects"""
    assert compat.is_integer(i) is True


@given(st.booleans())
def test_is_integer_with_booleans(b):
    """is_integer should return True for bool (subclass of int)"""
    # In Python, bool is a subclass of int
    assert compat.is_integer(b) is True


@given(st.floats())
def test_is_integer_with_floats(f):
    """is_integer should return False for float objects"""
    assert compat.is_integer(f) is False


@given(st.text())
def test_is_integer_with_text(s):
    """is_integer should return False for str objects"""
    assert compat.is_integer(s) is False


@given(st.one_of(st.none(), st.binary(), st.lists(st.integers())))
def test_is_integer_with_other_types(obj):
    """is_integer should return False for other types"""
    assert compat.is_integer(obj) is False


# Test IS_INTRESOURCE from _common.py (if we can import it)
try:
    # Try to import with the cffi backend (default)
    from win32ctypes.core._common import IS_INTRESOURCE
    HAS_IS_INTRESOURCE = True
except ImportError:
    try:
        # Try the ctypes backend directly
        from win32ctypes.core.ctypes._common import IS_INTRESOURCE
        HAS_IS_INTRESOURCE = True
    except ImportError:
        HAS_IS_INTRESOURCE = False
        
if HAS_IS_INTRESOURCE:
    @given(st.integers(min_value=0, max_value=65535))
    def test_is_intresource_true_for_small_values(x):
        """IS_INTRESOURCE should return True for values where x >> 16 == 0"""
        assert IS_INTRESOURCE(x) is True
        assert x >> 16 == 0  # Verify the property
    
    @given(st.integers(min_value=65536))
    def test_is_intresource_false_for_large_values(x):
        """IS_INTRESOURCE should return False for values where x >> 16 != 0"""
        assert IS_INTRESOURCE(x) is False
        assert x >> 16 != 0  # Verify the property
    
    @given(st.integers())
    def test_is_intresource_correctness(x):
        """IS_INTRESOURCE(x) should be equivalent to (x >> 16 == 0)"""
        # This tests the exact implementation
        expected = (x >> 16 == 0)
        # Handle negative numbers - they would have high bits set
        if x < 0:
            expected = False
        assert IS_INTRESOURCE(x) == expected
    
    @given(st.integers(min_value=-65536, max_value=-1))
    def test_is_intresource_negative_values(x):
        """IS_INTRESOURCE should handle negative values correctly"""
        # Negative values have high bits set, so x >> 16 != 0
        result = IS_INTRESOURCE(x)
        # The actual behavior depends on how Python handles right shift of negative numbers
        # and how the function interprets them
        assert result == (x >> 16 == 0)


# Test edge cases and special values
def test_is_bytes_edge_cases():
    """Test edge cases for is_bytes"""
    assert compat.is_bytes(b'') is True  # Empty bytes
    assert compat.is_bytes(b'\x00') is True  # Null byte
    assert compat.is_bytes(b'\xff' * 1000) is True  # Large bytes
    assert compat.is_bytes(bytearray(b'test')) is False  # bytearray is not bytes
    assert compat.is_bytes(memoryview(b'test')) is False  # memoryview is not bytes


def test_is_text_edge_cases():
    """Test edge cases for is_text"""
    assert compat.is_text('') is True  # Empty string
    assert compat.is_text('\x00') is True  # Null character
    assert compat.is_text('🦄' * 1000) is True  # Unicode string
    assert compat.is_text(r'\n\t') is True  # Raw string


def test_is_integer_edge_cases():
    """Test edge cases for is_integer"""
    assert compat.is_integer(0) is True
    assert compat.is_integer(-1) is True
    assert compat.is_integer(2**63 - 1) is True  # Large int
    assert compat.is_integer(-2**63) is True  # Large negative int
    assert compat.is_integer(True) is True  # bool is subclass of int
    assert compat.is_integer(False) is True  # bool is subclass of int
    
    # Interesting case: numpy integers if numpy is available
    try:
        import numpy as np
        # numpy integers might not be recognized as Python integers by isinstance
        np_int = np.int32(42)
        result = compat.is_integer(np_int)
        # This could be False because np.int32 is not a Python int
        print(f"numpy.int32 result: {result}")
    except ImportError:
        pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])