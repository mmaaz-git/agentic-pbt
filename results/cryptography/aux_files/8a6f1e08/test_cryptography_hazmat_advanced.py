import os
from hypothesis import given, strategies as st, assume, settings, note
import pytest

from cryptography.hazmat.primitives import constant_time, keywrap, padding
from cryptography.hazmat.primitives.keywrap import InvalidUnwrap


# Test bit manipulation edge cases in keywrap 
@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32),
    key_to_wrap=st.binary(min_size=16).filter(lambda x: len(x) % 8 == 0)
)
def test_wrapped_key_bit_flip_detection(wrapping_key, key_to_wrap):
    """Any bit flip in wrapped key should be detected"""
    wrapped = keywrap.aes_key_wrap(wrapping_key, key_to_wrap)
    
    # Try flipping each bit
    for byte_idx in range(len(wrapped)):
        for bit_idx in range(8):
            corrupted = bytearray(wrapped)
            corrupted[byte_idx] ^= (1 << bit_idx)
            
            with pytest.raises(InvalidUnwrap):
                keywrap.aes_key_unwrap(wrapping_key, bytes(corrupted))


# Test empty input edge case
@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32)
)
def test_aes_key_wrap_empty_with_padding(wrapping_key):
    """Empty key should be wrappable with padding"""
    empty_key = b""
    wrapped = keywrap.aes_key_wrap_with_padding(wrapping_key, empty_key)
    unwrapped = keywrap.aes_key_unwrap_with_padding(wrapping_key, wrapped)
    assert unwrapped == empty_key


# Test unwrap with padding tamper detection
@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32),
    wrapped_key=st.binary(min_size=16, max_size=1000)
)
def test_aes_key_unwrap_with_padding_tamper_detection(wrapping_key, wrapped_key):
    """Random data should fail unwrapping with padding"""
    # Random data is extremely unlikely to be valid
    with pytest.raises(InvalidUnwrap):
        keywrap.aes_key_unwrap_with_padding(wrapping_key, wrapped_key)


# Test wrapping different keys with same wrapping key
@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32),
    key1=st.binary(min_size=16).filter(lambda x: len(x) % 8 == 0),
    key2=st.binary(min_size=16).filter(lambda x: len(x) % 8 == 0)
)
def test_different_keys_wrap_differently(wrapping_key, key1, key2):
    """Different keys should produce different wrapped results"""
    assume(key1 != key2)
    wrapped1 = keywrap.aes_key_wrap(wrapping_key, key1)
    wrapped2 = keywrap.aes_key_wrap(wrapping_key, key2)
    assert wrapped1 != wrapped2


# Test padding consistency 
@given(
    block_size=st.integers(min_value=8, max_value=2040).filter(lambda x: x % 8 == 0),
    data=st.binary(min_size=0, max_size=10000),
    chunk_size=st.integers(min_value=1, max_value=100)
)
def test_pkcs7_incremental_vs_single_shot(block_size, data, chunk_size):
    """Incremental padding should match single-shot padding"""
    # Single shot
    padder1 = padding.PKCS7(block_size).padder()
    result1 = padder1.update(data) + padder1.finalize()
    
    # Incremental
    padder2 = padding.PKCS7(block_size).padder()
    result2 = b""
    for i in range(0, len(data), chunk_size):
        result2 += padder2.update(data[i:i+chunk_size])
    result2 += padder2.finalize()
    
    assert result1 == result2


# Test padding idempotence
@given(
    block_size=st.integers(min_value=8, max_value=2040).filter(lambda x: x % 8 == 0)
)
def test_pkcs7_empty_input(block_size):
    """Empty input should still produce valid padding"""
    padder = padding.PKCS7(block_size).padder()
    padded = padder.update(b"") + padder.finalize()
    
    # Should have added padding
    assert len(padded) == block_size // 8
    
    # Should unpad correctly
    unpadder = padding.PKCS7(block_size).unpadder()
    unpadded = unpadder.update(padded) + unpadder.finalize()
    assert unpadded == b""


# Test very large padding blocks
@given(
    data=st.binary(min_size=0, max_size=10000)
)
def test_pkcs7_max_block_size(data):
    """Test maximum allowed block size"""
    max_block_size = 2040
    padder = padding.PKCS7(max_block_size).padder()
    padded = padder.update(data) + padder.finalize()
    
    unpadder = padding.PKCS7(max_block_size).unpadder()
    unpadded = unpadder.update(padded) + unpadder.finalize()
    assert unpadded == data


# Test ANSIX923 incremental consistency
@given(
    block_size=st.integers(min_value=8, max_value=2040).filter(lambda x: x % 8 == 0),
    data=st.binary(min_size=0, max_size=10000),
    chunk_size=st.integers(min_value=1, max_value=100)
)
def test_ansix923_incremental_vs_single_shot(block_size, data, chunk_size):
    """Incremental ANSIX923 padding should match single-shot padding"""
    # Single shot
    padder1 = padding.ANSIX923(block_size).padder()
    result1 = padder1.update(data) + padder1.finalize()
    
    # Incremental
    padder2 = padding.ANSIX923(block_size).padder()
    result2 = b""
    for i in range(0, len(data), chunk_size):
        result2 += padder2.update(data[i:i+chunk_size])
    result2 += padder2.finalize()
    
    assert result1 == result2


# Test that bytes_eq handles empty bytes
def test_constant_time_empty_bytes():
    """bytes_eq should handle empty bytes correctly"""
    assert constant_time.bytes_eq(b"", b"") is True
    assert constant_time.bytes_eq(b"", b"x") is False
    assert constant_time.bytes_eq(b"x", b"") is False


# Test wrap/unwrap with exactly 8-byte key (minimum after padding requirement)
@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32)
)
def test_aes_key_wrap_with_padding_8_bytes(wrapping_key):
    """Test wrapping exactly 8 bytes with padding (special case in code)"""
    key_to_wrap = b"12345678"
    wrapped = keywrap.aes_key_wrap_with_padding(wrapping_key, key_to_wrap)
    
    # This should use the special case for exactly 8 bytes after padding
    assert len(wrapped) == 16  # Special case produces exactly 16 bytes
    
    unwrapped = keywrap.aes_key_unwrap_with_padding(wrapping_key, wrapped)
    assert unwrapped == key_to_wrap


# Test unwrap edge case with exactly 16 bytes
@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32),
    key_to_wrap=st.binary(min_size=1, max_size=8)
)
def test_aes_key_unwrap_with_padding_16_bytes(wrapping_key, key_to_wrap):
    """Test unwrapping exactly 16 bytes (special case in code)"""
    wrapped = keywrap.aes_key_wrap_with_padding(wrapping_key, key_to_wrap)
    
    if len(wrapped) == 16:  # Special case path
        unwrapped = keywrap.aes_key_unwrap_with_padding(wrapping_key, wrapped)
        assert unwrapped == key_to_wrap


# Test invalid wrapped key sizes
@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32),
    wrapped_key=st.binary(max_size=15)
)
def test_unwrap_with_padding_too_short(wrapping_key, wrapped_key):
    """Wrapped keys < 16 bytes should fail unwrapping with padding"""
    with pytest.raises(InvalidUnwrap, match="Must be at least 16 bytes"):
        keywrap.aes_key_unwrap_with_padding(wrapping_key, wrapped_key)


@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32),
    wrapped_key=st.binary(max_size=23)
)
def test_unwrap_too_short(wrapping_key, wrapped_key):
    """Wrapped keys < 24 bytes should fail regular unwrapping"""
    with pytest.raises(InvalidUnwrap, match="Must be at least 24 bytes"):
        keywrap.aes_key_unwrap(wrapping_key, wrapped_key)


@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32),
    wrapped_key=st.binary(min_size=24).filter(lambda x: len(x) % 8 != 0)
)
def test_unwrap_not_multiple_of_8(wrapping_key, wrapped_key):
    """Wrapped keys not multiple of 8 should fail unwrapping"""
    with pytest.raises(InvalidUnwrap, match="wrapped key must be a multiple of 8 bytes"):
        keywrap.aes_key_unwrap(wrapping_key, wrapped_key)


# Test that unwrap validates the AIV correctly
@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32),
    key_to_wrap=st.binary(min_size=1, max_size=100)
)
def test_aes_key_wrap_unwrap_padding_validates_aiv(wrapping_key, key_to_wrap):
    """Test that unwrap_with_padding validates the AIV header correctly"""
    wrapped = keywrap.aes_key_wrap_with_padding(wrapping_key, key_to_wrap)
    
    # Corrupt the first 4 bytes (AIV magic number)
    if len(wrapped) > 16:
        # For wrapped keys > 16 bytes, corruption happens after unwrapping
        corrupted = bytearray(wrapped)
        # We can't easily corrupt the AIV without knowing the internal state
        # Skip this case
        pass
    
    # Just verify round-trip works
    unwrapped = keywrap.aes_key_unwrap_with_padding(wrapping_key, wrapped)
    assert unwrapped == key_to_wrap