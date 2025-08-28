import time
import base64
from hypothesis import given, strategies as st, assume, settings
from cryptography.fernet import Fernet, MultiFernet, InvalidToken
from cryptography.hazmat.primitives import padding, constant_time
from cryptography.hazmat.primitives.ciphers import algorithms


# Strategy for valid Fernet keys
@st.composite
def fernet_keys(draw):
    """Generate valid Fernet keys."""
    # Fernet keys are 32 bytes, base64url encoded
    raw_key = draw(st.binary(min_size=32, max_size=32))
    return base64.urlsafe_b64encode(raw_key)


# Test 1: Fernet encrypt/decrypt round-trip property
@given(
    data=st.binary(min_size=0, max_size=10000),
    key=fernet_keys()
)
def test_fernet_encrypt_decrypt_roundtrip(data, key):
    """Test that Fernet encryption followed by decryption returns original data."""
    f = Fernet(key)
    encrypted = f.encrypt(data)
    decrypted = f.decrypt(encrypted)
    assert decrypted == data


# Test 2: Fernet with TTL - should fail for expired tokens
@given(
    data=st.binary(min_size=0, max_size=1000),
    key=fernet_keys(),
    ttl=st.integers(min_value=1, max_value=10),
    past_time=st.integers(min_value=1, max_value=3600)
)
def test_fernet_ttl_expiry(data, key, ttl, past_time):
    """Test that Fernet correctly rejects expired tokens."""
    f = Fernet(key)
    current_time = int(time.time())
    # Encrypt at a past time
    token = f.encrypt_at_time(data, current_time - past_time)
    
    if past_time > ttl:
        # Token should be expired
        try:
            f.decrypt_at_time(token, ttl, current_time)
            assert False, "Should have raised InvalidToken for expired token"
        except InvalidToken:
            pass  # Expected
    else:
        # Token should still be valid
        decrypted = f.decrypt_at_time(token, ttl, current_time)
        assert decrypted == data


# Test 3: MultiFernet should decrypt messages from any of its Fernets
@given(
    data=st.binary(min_size=0, max_size=1000),
    keys=st.lists(fernet_keys(), min_size=1, max_size=5, unique=True),
    encrypt_index=st.integers(min_value=0)
)
def test_multifernet_compatibility(data, keys, encrypt_index):
    """Test that MultiFernet can decrypt messages from any of its Fernets."""
    assume(len(keys) > 0)
    encrypt_index = encrypt_index % len(keys)
    
    # Create individual Fernet instances
    fernets = [Fernet(key) for key in keys]
    
    # Encrypt with one specific Fernet
    encrypted = fernets[encrypt_index].encrypt(data)
    
    # MultiFernet should be able to decrypt it
    multi = MultiFernet(fernets)
    decrypted = multi.decrypt(encrypted)
    assert decrypted == data


# Test 4: MultiFernet rotate should preserve data
@given(
    data=st.binary(min_size=0, max_size=1000),
    old_key=fernet_keys(),
    new_key=fernet_keys()
)
def test_multifernet_rotate_preserves_data(data, old_key, new_key):
    """Test that MultiFernet.rotate preserves the original data."""
    assume(old_key != new_key)
    
    # Encrypt with old key
    old_fernet = Fernet(old_key)
    token = old_fernet.encrypt(data)
    
    # Create MultiFernet with new key first (for rotation)
    new_fernet = Fernet(new_key)
    multi = MultiFernet([new_fernet, old_fernet])
    
    # Rotate the token
    rotated_token = multi.rotate(token)
    
    # Should decrypt to same data
    decrypted = multi.decrypt(rotated_token)
    assert decrypted == data
    
    # New key alone should be able to decrypt rotated token
    assert new_fernet.decrypt(rotated_token) == data


# Test 5: PKCS7 padding round-trip
@given(
    data=st.binary(min_size=0, max_size=10000),
    block_size=st.sampled_from([64, 128, 256])  # Common block sizes in bits
)
def test_pkcs7_padding_roundtrip(data, block_size):
    """Test PKCS7 padding and unpadding round-trip."""
    padder = padding.PKCS7(block_size).padder()
    padded = padder.update(data) + padder.finalize()
    
    # Verify padding added correct amount
    assert len(padded) % (block_size // 8) == 0
    
    unpadder = padding.PKCS7(block_size).unpadder()
    unpadded = unpadder.update(padded) + unpadder.finalize()
    
    assert unpadded == data


# Test 6: ANSIX923 padding round-trip
@given(
    data=st.binary(min_size=0, max_size=10000),
    block_size=st.sampled_from([64, 128, 256])
)
def test_ansix923_padding_roundtrip(data, block_size):
    """Test ANSIX923 padding and unpadding round-trip."""
    padder = padding.ANSIX923(block_size).padder()
    padded = padder.update(data) + padder.finalize()
    
    # Verify padding added correct amount
    assert len(padded) % (block_size // 8) == 0
    
    unpadder = padding.ANSIX923(block_size).unpadder()
    unpadded = unpadder.update(padded) + unpadder.finalize()
    
    assert unpadded == data


# Test 7: Constant time comparison invariants
@given(
    a=st.binary(min_size=0, max_size=1000),
    b=st.binary(min_size=0, max_size=1000)
)
def test_constant_time_bytes_eq_consistency(a, b):
    """Test that constant_time.bytes_eq is consistent with regular equality."""
    result = constant_time.bytes_eq(a, b)
    expected = (a == b)
    assert result == expected


# Test 8: Constant time comparison reflexivity
@given(data=st.binary(min_size=0, max_size=1000))
def test_constant_time_bytes_eq_reflexive(data):
    """Test that constant_time.bytes_eq is reflexive."""
    assert constant_time.bytes_eq(data, data) is True


# Test 9: Fernet generate_key produces valid keys
@given(st.integers(min_value=1, max_value=10))
def test_fernet_generate_key_validity(n):
    """Test that Fernet.generate_key always produces valid keys."""
    for _ in range(n):
        key = Fernet.generate_key()
        # Key should be valid for creating a Fernet instance
        f = Fernet(key)
        # And should work for encryption/decryption
        test_data = b"test"
        encrypted = f.encrypt(test_data)
        decrypted = f.decrypt(encrypted)
        assert decrypted == test_data


# Test 10: Invalid block sizes for padding should raise ValueError
@given(
    block_size=st.one_of(
        st.integers(min_value=-1000, max_value=-1),  # negative
        st.integers(min_value=2041, max_value=10000),  # too large
        st.integers(min_value=1, max_value=2040).filter(lambda x: x % 8 != 0)  # not multiple of 8
    )
)
def test_padding_invalid_block_size(block_size):
    """Test that invalid block sizes raise ValueError."""
    try:
        padding.PKCS7(block_size)
        assert False, f"Should have raised ValueError for block_size={block_size}"
    except ValueError:
        pass  # Expected
    
    try:
        padding.ANSIX923(block_size)
        assert False, f"Should have raised ValueError for block_size={block_size}"
    except ValueError:
        pass  # Expected


# Test 11: Fernet extract_timestamp consistency
@given(
    data=st.binary(min_size=0, max_size=1000),
    key=fernet_keys(),
    timestamp=st.integers(min_value=0, max_value=2**63-1)
)
def test_fernet_timestamp_consistency(data, key, timestamp):
    """Test that Fernet preserves timestamps correctly."""
    f = Fernet(key)
    token = f.encrypt_at_time(data, timestamp)
    extracted = f.extract_timestamp(token)
    assert extracted == timestamp


# Test 12: Empty MultiFernet should raise ValueError
def test_multifernet_empty_list():
    """Test that MultiFernet requires at least one Fernet."""
    try:
        MultiFernet([])
        assert False, "Should have raised ValueError for empty list"
    except ValueError as e:
        assert "at least one" in str(e)


# Test 13: Fernet should handle empty data
@given(key=fernet_keys())
def test_fernet_empty_data(key):
    """Test that Fernet correctly handles empty data."""
    f = Fernet(key)
    encrypted = f.encrypt(b"")
    decrypted = f.decrypt(encrypted)
    assert decrypted == b""


# Test 14: Test padding with data that's already block-aligned
@given(
    block_size=st.sampled_from([64, 128, 256]),
    multiplier=st.integers(min_value=1, max_value=100)
)
def test_padding_block_aligned_data(block_size, multiplier):
    """Test padding with data that's already a multiple of block size."""
    block_size_bytes = block_size // 8
    data = b"x" * (block_size_bytes * multiplier)
    
    # PKCS7
    padder = padding.PKCS7(block_size).padder()
    padded = padder.update(data) + padder.finalize()
    # PKCS7 always adds padding, even for aligned data
    assert len(padded) == len(data) + block_size_bytes
    
    unpadder = padding.PKCS7(block_size).unpadder()
    unpadded = unpadder.update(padded) + unpadder.finalize()
    assert unpadded == data
    
    # ANSIX923
    padder = padding.ANSIX923(block_size).padder()
    padded = padder.update(data) + padder.finalize()
    # ANSIX923 also always adds padding
    assert len(padded) == len(data) + block_size_bytes
    
    unpadder = padding.ANSIX923(block_size).unpadder()
    unpadded = unpadder.update(padded) + unpadder.finalize()
    assert unpadded == data


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])