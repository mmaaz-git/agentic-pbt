"""Property-based testing for cryptography.fernet module."""
import time
from hypothesis import given, strategies as st, assume, settings
from cryptography.fernet import Fernet, MultiFernet, InvalidToken
import pytest


@given(st.binary())
def test_fernet_round_trip(data):
    """Test that decrypt(encrypt(x)) == x for all valid byte sequences."""
    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted = f.encrypt(data)
    decrypted = f.decrypt(encrypted)
    assert decrypted == data


@given(st.binary(), st.integers(min_value=0, max_value=2**63-1))
def test_fernet_round_trip_at_time(data, current_time):
    """Test round-trip with specific timestamp."""
    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted = f.encrypt_at_time(data, current_time)
    decrypted = f.decrypt(encrypted)
    assert decrypted == data


@given(st.binary(), st.integers(min_value=0, max_value=2**63-1))
def test_fernet_extract_timestamp(data, current_time):
    """Test that extracted timestamp matches encryption time."""
    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted = f.encrypt_at_time(data, current_time)
    extracted_time = f.extract_timestamp(encrypted)
    assert extracted_time == current_time


@given(
    st.binary(), 
    st.integers(min_value=0, max_value=2**63-1),
    st.integers(min_value=1, max_value=86400)  # TTL from 1 second to 1 day
)
def test_fernet_ttl_valid(data, current_time, ttl):
    """Test TTL: decryption should work within time window."""
    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted = f.encrypt_at_time(data, current_time)
    
    # Decrypt at a time within TTL
    decrypt_time = current_time + ttl - 1
    decrypted = f.decrypt_at_time(encrypted, ttl, decrypt_time)
    assert decrypted == data


@given(
    st.binary(),
    st.integers(min_value=0, max_value=2**63-1000),
    st.integers(min_value=1, max_value=86400)
)
def test_fernet_ttl_expired(data, current_time, ttl):
    """Test that decryption fails after TTL expires."""
    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted = f.encrypt_at_time(data, current_time)
    
    # Try to decrypt after TTL expired
    decrypt_time = current_time + ttl + 1
    with pytest.raises(InvalidToken):
        f.decrypt_at_time(encrypted, ttl, decrypt_time)


@given(
    st.binary(),
    st.integers(min_value=62, max_value=2**63-1)
)
def test_fernet_clock_skew(data, current_time):
    """Test that future timestamps beyond clock skew are rejected."""
    key = Fernet.generate_key()
    f = Fernet(key)
    
    # Encrypt with future timestamp beyond allowed skew
    future_time = current_time + 61  # Beyond 60 second skew
    encrypted = f.encrypt_at_time(data, future_time)
    
    # Should fail when decrypting at current time with TTL check
    with pytest.raises(InvalidToken):
        f.decrypt_at_time(encrypted, 3600, current_time)


@given(st.lists(st.binary(), min_size=1, max_size=5))
def test_multifernet_round_trip(keys_data):
    """Test MultiFernet round-trip with multiple keys."""
    fernets = [Fernet(Fernet.generate_key()) for _ in range(len(keys_data))]
    mf = MultiFernet(fernets)
    
    data = b"test data"
    encrypted = mf.encrypt(data)
    decrypted = mf.decrypt(encrypted)
    assert decrypted == data


@given(st.binary())
def test_multifernet_rotate(data):
    """Test that rotation preserves data."""
    key1 = Fernet.generate_key()
    key2 = Fernet.generate_key()
    f1 = Fernet(key1)
    f2 = Fernet(key2)
    mf = MultiFernet([f1, f2])
    
    # Encrypt with second key
    encrypted = f2.encrypt(data)
    
    # Rotate should re-encrypt with first key
    rotated = mf.rotate(encrypted)
    
    # Should be decryptable and preserve data
    decrypted = mf.decrypt(rotated)
    assert decrypted == data
    
    # Verify it was re-encrypted with first key
    decrypted_f1 = f1.decrypt(rotated)
    assert decrypted_f1 == data


@given(st.binary(min_size=0, max_size=0))
def test_fernet_empty_data(data):
    """Test encryption of empty data."""
    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted = f.encrypt(data)
    decrypted = f.decrypt(encrypted)
    assert decrypted == data
    assert decrypted == b""


@given(st.binary(min_size=1, max_size=1000000))
def test_fernet_large_data(data):
    """Test with varying data sizes."""
    key = Fernet.generate_key()
    f = Fernet(key)
    encrypted = f.encrypt(data)
    decrypted = f.decrypt(encrypted)
    assert decrypted == data


@given(st.text())
def test_fernet_invalid_key_format(key_str):
    """Test that invalid keys are rejected."""
    assume(len(key_str) != 44 or not all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=' for c in key_str))
    
    with pytest.raises(ValueError):
        Fernet(key_str)


@given(st.binary(min_size=32, max_size=32))
def test_fernet_raw_key_bytes(raw_key):
    """Test that raw 32-byte keys must be base64 encoded."""
    # Raw bytes should fail
    with pytest.raises(ValueError):
        Fernet(raw_key)


@given(st.one_of(st.integers(), st.floats(), st.none(), st.lists(st.integers())))
def test_fernet_token_type_checking(invalid_token):
    """Test type checking for decrypt token parameter."""
    key = Fernet.generate_key()
    f = Fernet(key)
    
    with pytest.raises(TypeError):
        f.decrypt(invalid_token)


@given(st.text(min_size=1).filter(lambda x: not x.startswith('\x80')))
def test_fernet_invalid_token_format(invalid_token):
    """Test that malformed tokens are rejected."""
    key = Fernet.generate_key()
    f = Fernet(key)
    
    with pytest.raises(InvalidToken):
        f.decrypt(invalid_token)


@given(st.binary(), st.integers(min_value=-2**63, max_value=-1))
def test_fernet_negative_timestamp(data, negative_time):
    """Test behavior with negative timestamps."""
    key = Fernet.generate_key()
    f = Fernet(key)
    
    # This should handle negative time gracefully
    with pytest.raises((OverflowError, ValueError)):
        f.encrypt_at_time(data, negative_time)


@given(st.binary())
def test_fernet_token_not_reusable_different_keys(data):
    """Test that tokens from one key cannot be decrypted with another."""
    key1 = Fernet.generate_key()
    key2 = Fernet.generate_key()
    f1 = Fernet(key1)
    f2 = Fernet(key2)
    
    encrypted = f1.encrypt(data)
    
    with pytest.raises(InvalidToken):
        f2.decrypt(encrypted)


@given(st.lists(st.binary(), min_size=2, max_size=5))
def test_multifernet_order_matters(data_list):
    """Test MultiFernet with different key orders."""
    keys = [Fernet.generate_key() for _ in range(len(data_list))]
    fernets = [Fernet(k) for k in keys]
    
    mf1 = MultiFernet(fernets)
    mf2 = MultiFernet(fernets[::-1])  # Reversed order
    
    data = b"test"
    encrypted = mf1.encrypt(data)
    
    # Both should decrypt successfully
    assert mf1.decrypt(encrypted) == data
    assert mf2.decrypt(encrypted) == data


@given(st.binary(), st.integers(min_value=0, max_value=10))
def test_fernet_ttl_boundary(data, ttl):
    """Test TTL boundary conditions."""
    key = Fernet.generate_key()
    f = Fernet(key)
    
    current_time = 1000
    encrypted = f.encrypt_at_time(data, current_time)
    
    # Exactly at TTL boundary
    boundary_time = current_time + ttl
    decrypted = f.decrypt_at_time(encrypted, ttl, boundary_time)
    assert decrypted == data


if __name__ == "__main__":
    # Run a quick test to ensure everything works
    test_fernet_round_trip()
    print("Basic test passed!")