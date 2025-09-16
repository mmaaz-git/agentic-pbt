"""Additional property tests for edge cases."""
from hypothesis import given, strategies as st, assume, settings
from cryptography.fernet import Fernet, MultiFernet, InvalidToken
import pytest
import time

@given(st.integers(min_value=2**63, max_value=2**64-1))
def test_fernet_large_timestamp_overflow(large_time):
    """Test behavior with timestamps that might overflow."""
    key = Fernet.generate_key()
    f = Fernet(key)
    data = b"test"
    
    # This should handle large timestamps gracefully
    try:
        encrypted = f.encrypt_at_time(data, large_time)
        # If encryption succeeds, decryption should work
        decrypted = f.decrypt(encrypted)
        assert decrypted == data
    except (OverflowError, ValueError, struct.error):
        # These are acceptable errors for overflow
        pass


@given(st.binary(min_size=44, max_size=44))
def test_fernet_key_validation(potential_key):
    """Test that only valid base64 keys are accepted."""
    try:
        f = Fernet(potential_key)
        # If it accepts the key, it should be usable
        test_data = b"test"
        encrypted = f.encrypt(test_data)
        decrypted = f.decrypt(encrypted)
        assert decrypted == test_data
    except ValueError:
        # Invalid key format - expected
        pass


@given(st.lists(st.just(Fernet(Fernet.generate_key())), min_size=1, max_size=100))
def test_multifernet_many_keys(fernets):
    """Test MultiFernet with many keys."""
    mf = MultiFernet(fernets)
    data = b"test data"
    
    encrypted = mf.encrypt(data)
    decrypted = mf.decrypt(encrypted)
    assert decrypted == data


@given(st.binary(), st.integers(min_value=0, max_value=100))
def test_fernet_ttl_zero(data, current_time):
    """Test TTL with zero value."""
    key = Fernet.generate_key()
    f = Fernet(key)
    
    encrypted = f.encrypt_at_time(data, current_time)
    
    # TTL of 0 should only work at exact same time
    decrypted = f.decrypt_at_time(encrypted, 0, current_time)
    assert decrypted == data
    
    # Should fail with any time difference
    with pytest.raises(InvalidToken):
        f.decrypt_at_time(encrypted, 0, current_time + 1)


@given(st.binary())
def test_fernet_multiple_encrypt_decrypt_cycles(data):
    """Test multiple encrypt/decrypt cycles don't corrupt data."""
    key = Fernet.generate_key()
    f = Fernet(key)
    
    # Multiple cycles
    result = data
    for _ in range(5):
        encrypted = f.encrypt(result)
        result = f.decrypt(encrypted)
    
    assert result == data


@given(st.binary(min_size=1, max_size=100))
def test_fernet_token_uniqueness(data):
    """Test that encrypting same data twice produces different tokens."""
    key = Fernet.generate_key()
    f = Fernet(key)
    
    token1 = f.encrypt(data)
    token2 = f.encrypt(data)
    
    # Tokens should be different due to random IV
    assert token1 != token2
    
    # But both should decrypt to same data
    assert f.decrypt(token1) == data
    assert f.decrypt(token2) == data


if __name__ == "__main__":
    print("Running additional property tests...")
    test_fernet_large_timestamp_overflow()
    test_fernet_key_validation()
    test_multifernet_many_keys()
    test_fernet_ttl_zero()
    test_fernet_multiple_encrypt_decrypt_cycles()
    test_fernet_token_uniqueness()
    print("All additional tests completed!")