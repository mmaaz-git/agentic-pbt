#!/usr/bin/env python3
"""
Property-based test for IS_INTRESOURCE mathematical property.
This function is the core of win32ctypes resource handling logic.
"""

from hypothesis import given, strategies as st, settings
import pytest


def IS_INTRESOURCE(x):
    """
    Direct implementation of IS_INTRESOURCE from win32ctypes.
    According to win32ctypes/core/ctypes/_common.py line 34-35.
    """
    return x >> 16 == 0


# Property 1: IS_INTRESOURCE mathematical property
@given(st.integers())
def test_is_intresource_mathematical_property(x):
    """
    Test that IS_INTRESOURCE correctly identifies values < 2^16.
    This is a mathematical invariant claimed by the implementation.
    """
    result = IS_INTRESOURCE(x)
    
    # For positive values, the property should hold precisely:
    # Values 0-65535 (0x0000-0xFFFF) should return True
    # Values >= 65536 (0x10000+) should return False
    if x >= 0:
        expected = (x < 65536)
        assert result == expected, \
            f"IS_INTRESOURCE({x:#x}) returned {result}, expected {expected}"
    else:
        # For negative values, arithmetic right shift behaves differently
        # The implementation uses >> which does arithmetic shift in Python
        assert result == (x >> 16 == 0)


# Property 2: IS_INTRESOURCE boundary conditions  
@given(st.integers(min_value=0, max_value=100000))
def test_is_intresource_boundaries(x):
    """
    Test IS_INTRESOURCE at critical boundaries.
    According to Windows resource handling, integer resource IDs
    are in the range 0-65535 (16-bit values).
    """
    result = IS_INTRESOURCE(x)
    
    if x < 65536:
        assert result is True, \
            f"IS_INTRESOURCE({x:#x}) should be True for values < 65536"
    else:
        assert result is False, \
            f"IS_INTRESOURCE({x:#x}) should be False for values >= 65536"


# Property 3: Critical boundary values
@given(st.sampled_from([0, 1, 65534, 65535, 65536, 65537, 2**32-1, 2**32]))
def test_is_intresource_critical_values(x):
    """Test IS_INTRESOURCE at specific critical values."""
    result = IS_INTRESOURCE(x)
    expected = (x < 65536)
    assert result == expected, \
        f"IS_INTRESOURCE({x:#x}) = {result}, expected {expected}"


# Property 4: Negative value handling
@given(st.integers(min_value=-100000, max_value=-1))
def test_is_intresource_negative_values(x):
    """
    Test IS_INTRESOURCE with negative values.
    Due to sign extension in arithmetic right shift,
    negative values should always return False.
    """
    result = IS_INTRESOURCE(x)
    # Negative numbers when shifted right 16 bits will have
    # sign extension, so they won't equal 0
    assert result is False, \
        f"IS_INTRESOURCE({x}) should be False for negative values"


# Property 5: Complement property
@given(st.integers(min_value=0, max_value=2**20))
def test_is_intresource_complement(x):
    """
    Test that IS_INTRESOURCE(x) != IS_INTRESOURCE(x | 0x10000)
    for positive x < 65536.
    """
    if x < 65536:
        # x is an INTRESOURCE
        assert IS_INTRESOURCE(x) is True
        # x with bit 16 set is NOT an INTRESOURCE
        assert IS_INTRESOURCE(x | 0x10000) is False, \
            f"Setting bit 16 should make {x:#x} not an INTRESOURCE"


# Property 6: Idempotence with masking
@given(st.integers(min_value=0))
def test_is_intresource_masking(x):
    """
    Test that IS_INTRESOURCE(x & 0xFFFF) is always True
    for non-negative x, since masking keeps only lower 16 bits.
    """
    masked = x & 0xFFFF
    result = IS_INTRESOURCE(masked)
    assert result is True, \
        f"IS_INTRESOURCE({masked:#x}) should be True after masking to 16 bits"


if __name__ == "__main__":
    print("Running property-based tests for IS_INTRESOURCE...")
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-seed=0"])