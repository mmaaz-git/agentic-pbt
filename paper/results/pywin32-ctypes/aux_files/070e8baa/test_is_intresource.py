#!/usr/bin/env python3
"""Test IS_INTRESOURCE implementation directly"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pywin32-ctypes_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import struct


# Since we can't import the module due to Windows dependencies,
# let's implement the function based on what we saw in the code
def IS_INTRESOURCE(x):
    """Implementation from win32ctypes.core.ctypes._common"""
    return x >> 16 == 0


@given(st.integers())
def test_is_intresource_implementation(x):
    """Test the IS_INTRESOURCE implementation"""
    result = IS_INTRESOURCE(x)
    
    # For positive numbers, it should return True only if x < 65536
    if x >= 0:
        if x < 65536:
            assert result is True
            assert x >> 16 == 0
        else:
            assert result is False
            assert x >> 16 != 0
    else:
        # For negative numbers, the right shift will never equal 0
        # because negative numbers have sign bits extended
        assert result is False


@given(st.integers(min_value=0, max_value=65535))
def test_is_intresource_valid_resources(x):
    """Valid resource IDs should be recognized"""
    assert IS_INTRESOURCE(x) is True


@given(st.integers(min_value=65536, max_value=2**32))
def test_is_intresource_invalid_resources(x):
    """Values >= 65536 should not be recognized as INTRESOURCE"""
    assert IS_INTRESOURCE(x) is False


@given(st.integers())
def test_is_intresource_boundary_values(x):
    """Test boundary conditions"""
    result = IS_INTRESOURCE(x)
    
    # Test specific boundaries
    if x == 0:
        assert result is True
    elif x == 65535:
        assert result is True
    elif x == 65536:
        assert result is False
    elif x == -1:
        # -1 has all bits set, so right shift won't be 0
        assert result is False


@given(st.integers(min_value=-2**63, max_value=-1))
def test_is_intresource_negative(x):
    """Negative values should never be valid INTRESOURCE"""
    result = IS_INTRESOURCE(x)
    # In Python, right shift of negative numbers extends the sign bit
    # So x >> 16 will never be 0 for negative x
    assert result is False
    assert x >> 16 != 0


@settings(max_examples=10000)
@given(st.integers())
def test_is_intresource_intensive(x):
    """Intensive testing of IS_INTRESOURCE"""
    result = IS_INTRESOURCE(x)
    
    # The function checks if the upper 48 bits are all zero (for 64-bit)
    # or upper 16 bits are zero (for 32-bit resources)
    # In the Windows API, INTRESOURCE values are in range 0-65535
    
    # Calculate what we expect
    if x < 0:
        # Negative numbers will have sign bits, so never INTRESOURCE
        expected = False
    elif x <= 65535:
        expected = True
    else:
        expected = False
    
    assert result == expected
    
    # Also verify the bit operation
    assert result == (x >> 16 == 0)


# Test edge cases that might reveal bugs
def test_is_intresource_edge_cases():
    """Test specific edge cases"""
    # Powers of 2 near the boundary
    assert IS_INTRESOURCE(2**15) is True  # 32768
    assert IS_INTRESOURCE(2**16 - 1) is True  # 65535
    assert IS_INTRESOURCE(2**16) is False  # 65536
    assert IS_INTRESOURCE(2**16 + 1) is False  # 65537
    
    # Maximum values
    assert IS_INTRESOURCE(2**63 - 1) is False
    assert IS_INTRESOURCE(-2**63) is False
    
    # Special Windows constants (from Windows headers)
    # MAKEINTRESOURCE(-1) is often used for special values
    assert IS_INTRESOURCE(-1) is False
    
    # Some actual Windows resource IDs
    assert IS_INTRESOURCE(1) is True  # RT_CURSOR
    assert IS_INTRESOURCE(2) is True  # RT_BITMAP
    assert IS_INTRESOURCE(3) is True  # RT_ICON
    assert IS_INTRESOURCE(14) is True  # RT_GROUP_ICON


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])