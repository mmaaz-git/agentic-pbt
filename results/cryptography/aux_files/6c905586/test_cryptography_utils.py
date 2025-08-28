import pytest
from hypothesis import given, strategies as st, assume, settings
import cryptography.utils as utils


@given(st.integers(min_value=0))
def test_int_to_bytes_round_trip_no_length(x):
    """Test that int_to_bytes without length can be reversed"""
    result = utils.int_to_bytes(x)
    recovered = int.from_bytes(result, 'big')
    assert recovered == x


@given(st.integers(min_value=0), st.integers(min_value=1, max_value=1000))
def test_int_to_bytes_with_length(x, length):
    """Test int_to_bytes with explicit length parameter"""
    # Calculate minimum required bytes
    if x == 0:
        min_bytes = 1
    else:
        min_bytes = (x.bit_length() + 7) // 8
    
    # Only test if length is sufficient
    assume(length >= min_bytes)
    
    result = utils.int_to_bytes(x, length)
    assert len(result) == length
    recovered = int.from_bytes(result, 'big')
    assert recovered == x


@given(st.integers(min_value=0), st.integers(min_value=1, max_value=1000))
def test_int_to_bytes_insufficient_length(x, length):
    """Test that int_to_bytes raises error when length too small"""
    if x == 0:
        min_bytes = 1
    else:
        min_bytes = (x.bit_length() + 7) // 8
    
    # Only test insufficient lengths
    assume(length < min_bytes)
    
    with pytest.raises(OverflowError):
        utils.int_to_bytes(x, length)


@given(st.integers(min_value=0))
def test_int_to_bytes_zero_length(x):
    """Test that length=0 always raises ValueError"""
    with pytest.raises(ValueError, match="length argument can't be 0"):
        utils.int_to_bytes(x, 0)


@given(st.integers(max_value=-1))
def test_int_to_bytes_negative_integers(x):
    """Test behavior with negative integers"""
    # Should raise OverflowError for negative values
    with pytest.raises(OverflowError):
        utils.int_to_bytes(x)


@given(st.integers(min_value=-1000, max_value=-1), st.integers(min_value=1, max_value=100))
def test_int_to_bytes_negative_with_length(x, length):
    """Test negative integers with explicit length"""
    with pytest.raises(OverflowError):
        utils.int_to_bytes(x, length)


@given(st.integers(min_value=0, max_value=2**256))
def test_int_to_bytes_length_calculation(x):
    """Test that default length calculation is correct"""
    result = utils.int_to_bytes(x)
    
    # Verify minimum encoding
    if x == 0:
        assert len(result) == 1
    else:
        expected_len = (x.bit_length() + 7) // 8
        assert len(result) == expected_len
    
    # Verify no leading zeros except for x=0
    if x > 0:
        assert result[0] != 0


@given(st.integers(min_value=0))
def test_int_to_bytes_endianness(x):
    """Test that int_to_bytes uses big-endian encoding"""
    result = utils.int_to_bytes(x)
    
    # Manual big-endian check
    if x == 0:
        assert result == b'\x00'
    else:
        # Convert back and verify
        recovered = int.from_bytes(result, 'big')
        assert recovered == x
        
        # Should fail with little-endian if x > 255
        if x > 255:
            little_endian = int.from_bytes(result, 'little')
            assert little_endian != x


@given(st.integers(min_value=1, max_value=2**64), st.integers(min_value=1, max_value=100))
def test_int_to_bytes_padding(x, extra_bytes):
    """Test that padding with extra bytes works correctly"""
    min_bytes = (x.bit_length() + 7) // 8
    length = min_bytes + extra_bytes
    
    result = utils.int_to_bytes(x, length)
    assert len(result) == length
    
    # Check padding is zeros at the beginning (big-endian)
    for i in range(extra_bytes):
        assert result[i] == 0
    
    # Verify value is preserved
    recovered = int.from_bytes(result, 'big')
    assert recovered == x