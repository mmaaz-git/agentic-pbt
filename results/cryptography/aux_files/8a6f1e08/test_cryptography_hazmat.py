import os
import secrets
from hypothesis import given, strategies as st, assume, settings
import pytest

from cryptography.hazmat.primitives import constant_time, keywrap, padding
from cryptography.hazmat.primitives.keywrap import InvalidUnwrap


# Test 1: Constant time comparison properties
@given(st.binary())
def test_constant_time_reflexivity(data):
    """bytes_eq should be reflexive: a == a"""
    assert constant_time.bytes_eq(data, data) is True


@given(st.binary(), st.binary())
def test_constant_time_symmetry(a, b):
    """bytes_eq should be symmetric: a == b implies b == a"""
    result1 = constant_time.bytes_eq(a, b)
    result2 = constant_time.bytes_eq(b, a)
    assert result1 == result2


@given(st.binary(min_size=1))
def test_constant_time_single_bit_flip(data):
    """Flipping any single bit should make bytes unequal"""
    for i in range(len(data)):
        for bit_pos in range(8):
            modified = bytearray(data)
            modified[i] ^= (1 << bit_pos)
            assert constant_time.bytes_eq(data, bytes(modified)) is False


# Test 2: AES Key Wrap/Unwrap round-trip properties
@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32),
    key_to_wrap=st.binary(min_size=16).filter(lambda x: len(x) % 8 == 0)
)
def test_aes_key_wrap_unwrap_roundtrip(wrapping_key, key_to_wrap):
    """wrap(unwrap(key)) should equal key"""
    wrapped = keywrap.aes_key_wrap(wrapping_key, key_to_wrap)
    unwrapped = keywrap.aes_key_unwrap(wrapping_key, wrapped)
    assert unwrapped == key_to_wrap


@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32),
    key_to_wrap=st.binary(min_size=1, max_size=1000)
)
def test_aes_key_wrap_unwrap_with_padding_roundtrip(wrapping_key, key_to_wrap):
    """wrap_with_padding(unwrap_with_padding(key)) should equal key"""
    wrapped = keywrap.aes_key_wrap_with_padding(wrapping_key, key_to_wrap)
    unwrapped = keywrap.aes_key_unwrap_with_padding(wrapping_key, wrapped)
    assert unwrapped == key_to_wrap


@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32),
    wrapped_key=st.binary(min_size=24).filter(lambda x: len(x) % 8 == 0)
)
def test_aes_key_unwrap_tamper_detection(wrapping_key, wrapped_key):
    """Unwrapping random data should fail with InvalidUnwrap"""
    # Random data is extremely unlikely to be a valid wrapped key
    with pytest.raises(InvalidUnwrap):
        keywrap.aes_key_unwrap(wrapping_key, wrapped_key)


@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32),
    key_to_wrap=st.binary(min_size=16).filter(lambda x: len(x) % 8 == 0)
)
def test_aes_key_wrap_deterministic(wrapping_key, key_to_wrap):
    """Key wrapping should be deterministic"""
    wrapped1 = keywrap.aes_key_wrap(wrapping_key, key_to_wrap)
    wrapped2 = keywrap.aes_key_wrap(wrapping_key, key_to_wrap)
    assert wrapped1 == wrapped2


@given(
    wrapping_key=st.binary(min_size=16, max_size=16) | 
                  st.binary(min_size=24, max_size=24) | 
                  st.binary(min_size=32, max_size=32),
    key_to_wrap=st.binary(min_size=16).filter(lambda x: len(x) % 8 == 0)
)
def test_aes_key_wrap_output_size(wrapping_key, key_to_wrap):
    """Wrapped key should be 8 bytes longer than original"""
    wrapped = keywrap.aes_key_wrap(wrapping_key, key_to_wrap)
    assert len(wrapped) == len(key_to_wrap) + 8


# Test 3: PKCS7 Padding properties
@given(
    block_size=st.integers(min_value=8, max_value=2040).filter(lambda x: x % 8 == 0),
    data=st.binary(min_size=0, max_size=10000)
)
def test_pkcs7_padding_roundtrip(block_size, data):
    """pad(unpad(data)) should equal data"""
    padder = padding.PKCS7(block_size).padder()
    unpadder = padding.PKCS7(block_size).unpadder()
    
    # Pad the data
    padded_data = padder.update(data) + padder.finalize()
    
    # Unpad the data
    unpadded_data = unpadder.update(padded_data) + unpadder.finalize()
    
    assert unpadded_data == data


@given(
    block_size=st.integers(min_value=8, max_value=2040).filter(lambda x: x % 8 == 0),
    data=st.binary(min_size=0, max_size=10000)
)
def test_pkcs7_padded_length(block_size, data):
    """Padded data length should be multiple of block_size bytes"""
    block_size_bytes = block_size // 8
    padder = padding.PKCS7(block_size).padder()
    padded_data = padder.update(data) + padder.finalize()
    
    assert len(padded_data) % block_size_bytes == 0
    assert len(padded_data) >= len(data)
    assert len(padded_data) - len(data) <= block_size_bytes


@given(
    block_size=st.integers(min_value=8, max_value=2040).filter(lambda x: x % 8 == 0),
    data=st.binary(min_size=0, max_size=10000)
)
def test_ansix923_padding_roundtrip(block_size, data):
    """pad(unpad(data)) should equal data for ANSIX923"""
    padder = padding.ANSIX923(block_size).padder()
    unpadder = padding.ANSIX923(block_size).unpadder()
    
    # Pad the data
    padded_data = padder.update(data) + padder.finalize()
    
    # Unpad the data
    unpadded_data = unpadder.update(padded_data) + unpadder.finalize()
    
    assert unpadded_data == data


@given(
    block_size=st.integers(min_value=8, max_value=2040).filter(lambda x: x % 8 == 0),
    data=st.binary(min_size=0, max_size=10000)
)
def test_ansix923_padded_length(block_size, data):
    """Padded data length should be multiple of block_size bytes for ANSIX923"""
    block_size_bytes = block_size // 8
    padder = padding.ANSIX923(block_size).padder()
    padded_data = padder.update(data) + padder.finalize()
    
    assert len(padded_data) % block_size_bytes == 0
    assert len(padded_data) >= len(data)
    assert len(padded_data) - len(data) <= block_size_bytes


# Test 4: Edge cases and validation
@given(st.integers())
def test_invalid_block_sizes(block_size):
    """Invalid block sizes should raise ValueError"""
    assume(block_size < 0 or block_size > 2040 or block_size % 8 != 0)
    
    with pytest.raises(ValueError):
        padding.PKCS7(block_size)
    
    with pytest.raises(ValueError):
        padding.ANSIX923(block_size)


@given(st.binary().filter(lambda x: len(x) not in [16, 24, 32]))
def test_invalid_wrapping_key_length(wrapping_key):
    """Invalid AES key lengths should raise ValueError"""
    with pytest.raises(ValueError, match="wrapping key must be a valid AES key length"):
        keywrap.aes_key_wrap(wrapping_key, b"x" * 16)


@given(st.binary(max_size=15))
def test_key_too_short_to_wrap(key_to_wrap):
    """Keys shorter than 16 bytes cannot be wrapped without padding"""
    wrapping_key = os.urandom(16)
    with pytest.raises(ValueError, match="key to wrap must be at least 16 bytes"):
        keywrap.aes_key_wrap(wrapping_key, key_to_wrap)


@given(st.binary(min_size=16).filter(lambda x: len(x) % 8 != 0))
def test_key_not_multiple_of_8(key_to_wrap):
    """Keys must be multiple of 8 bytes to wrap without padding"""
    wrapping_key = os.urandom(16)
    with pytest.raises(ValueError, match="key to wrap must be a multiple of 8 bytes"):
        keywrap.aes_key_wrap(wrapping_key, key_to_wrap)


# Test 5: Type checking
@given(st.one_of(st.text(), st.integers(), st.lists(st.integers())))
def test_bytes_eq_type_checking(non_bytes):
    """bytes_eq should reject non-bytes types"""
    with pytest.raises(TypeError, match="a and b must be bytes"):
        constant_time.bytes_eq(non_bytes, b"test")
    
    with pytest.raises(TypeError, match="a and b must be bytes"):
        constant_time.bytes_eq(b"test", non_bytes)