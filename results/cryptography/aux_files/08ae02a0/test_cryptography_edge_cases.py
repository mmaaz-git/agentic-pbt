import time
import base64
import struct
from hypothesis import given, strategies as st, assume, settings, note
from cryptography.fernet import Fernet, MultiFernet, InvalidToken
from cryptography.hazmat.primitives import padding, constant_time


# More aggressive testing with edge cases
@st.composite
def fernet_keys(draw):
    """Generate valid Fernet keys."""
    raw_key = draw(st.binary(min_size=32, max_size=32))
    return base64.urlsafe_b64encode(raw_key)


# Test with maximum timestamp values
@given(
    data=st.binary(min_size=0, max_size=1000),
    key=fernet_keys(),
    timestamp=st.one_of(
        st.just(0),  # minimum timestamp
        st.just(2**63 - 1),  # maximum signed 64-bit
        st.just(2**64 - 1),  # maximum unsigned 64-bit  
        st.integers(min_value=2**63, max_value=2**64 - 1)  # large timestamps
    )
)
@settings(max_examples=200)
def test_fernet_extreme_timestamps(data, key, timestamp):
    """Test Fernet with extreme timestamp values."""
    f = Fernet(key)
    
    # Test if large timestamps cause issues
    try:
        token = f.encrypt_at_time(data, timestamp)
        extracted = f.extract_timestamp(token)
        # Check if timestamp is preserved correctly
        assert extracted == timestamp, f"Timestamp mismatch: {extracted} != {timestamp}"
        
        # Try to decrypt
        decrypted = f._decrypt_data(
            base64.urlsafe_b64decode(token),
            timestamp,
            None
        )
        assert decrypted == data
    except (struct.error, OverflowError, ValueError) as e:
        # If it fails, this might be a bug with large timestamps
        note(f"Failed with timestamp {timestamp}: {e}")
        # Let's see if this is expected behavior
        if timestamp > 2**63 - 1:
            # Python's time functions typically use signed 64-bit
            pass  # This might be expected
        else:
            raise


# Test with manipulated tokens
@given(
    data=st.binary(min_size=1, max_size=1000),
    key=fernet_keys(),
    mutation_index=st.integers(min_value=0, max_value=100),
    mutation_byte=st.integers(min_value=0, max_value=255)
)
def test_fernet_token_integrity(data, key, mutation_index, mutation_byte):
    """Test that Fernet properly validates token integrity."""
    f = Fernet(key)
    token = f.encrypt(data)
    
    # Decode the token
    token_bytes = base64.urlsafe_b64decode(token)
    
    # Mutate a byte in the token
    if mutation_index < len(token_bytes):
        token_list = list(token_bytes)
        original_byte = token_list[mutation_index]
        
        # Make sure we're actually changing the byte
        if original_byte == mutation_byte:
            mutation_byte = (mutation_byte + 1) % 256
            
        token_list[mutation_index] = mutation_byte
        mutated_token = base64.urlsafe_b64encode(bytes(token_list))
        
        # Try to decrypt the mutated token - should fail
        try:
            f.decrypt(mutated_token)
            # If we get here, integrity check failed to catch corruption
            if mutation_index >= len(token_bytes) - 32:
                # HMAC area - must catch this
                assert False, f"Failed to detect HMAC corruption at index {mutation_index}"
        except InvalidToken:
            pass  # Expected - token validation worked


# Test constant_time with different length inputs
@given(
    len_a=st.integers(min_value=0, max_value=10000),
    len_b=st.integers(min_value=0, max_value=10000)
)
def test_constant_time_different_lengths(len_a, len_b):
    """Test constant_time.bytes_eq with different length inputs."""
    a = b'x' * len_a
    b = b'x' * len_b
    
    result = constant_time.bytes_eq(a, b)
    expected = (len_a == len_b)  # Can only be equal if same length
    assert result == expected


# Test padding with streaming data
@given(
    chunks=st.lists(st.binary(min_size=0, max_size=100), min_size=1, max_size=20),
    block_size=st.sampled_from([64, 128, 256])
)
def test_padding_streaming(chunks, block_size):
    """Test padding with data provided in chunks."""
    # Concatenate all chunks for reference
    full_data = b''.join(chunks)
    
    # PKCS7 streaming
    padder = padding.PKCS7(block_size).padder()
    padded_chunks = []
    for chunk in chunks:
        padded_chunks.append(padder.update(chunk))
    padded_chunks.append(padder.finalize())
    padded_streaming = b''.join(padded_chunks)
    
    # Compare with non-streaming
    padder2 = padding.PKCS7(block_size).padder()
    padded_direct = padder2.update(full_data) + padder2.finalize()
    
    assert padded_streaming == padded_direct
    
    # Verify unpadding works
    unpadder = padding.PKCS7(block_size).unpadder()
    unpadded = unpadder.update(padded_streaming) + unpadder.finalize()
    assert unpadded == full_data


# Test MultiFernet with many keys
@given(
    data=st.binary(min_size=0, max_size=1000),
    num_keys=st.integers(min_value=10, max_value=100)
)
@settings(max_examples=50)
def test_multifernet_many_keys(data, num_keys):
    """Test MultiFernet with many keys."""
    keys = [Fernet.generate_key() for _ in range(num_keys)]
    fernets = [Fernet(key) for key in keys]
    
    multi = MultiFernet(fernets)
    
    # Encrypt with the MultiFernet
    encrypted = multi.encrypt(data)
    
    # Should decrypt successfully
    decrypted = multi.decrypt(encrypted)
    assert decrypted == data
    
    # Any individual Fernet from index 1+ should fail to decrypt
    # (since MultiFernet uses the first key for encryption)
    for i in range(1, num_keys):
        try:
            fernets[i].decrypt(encrypted)
            assert False, f"Fernet at index {i} shouldn't decrypt token from index 0"
        except InvalidToken:
            pass  # Expected


# Test for clock skew edge cases
@given(
    data=st.binary(min_size=0, max_size=1000),
    key=fernet_keys(),
    future_seconds=st.integers(min_value=61, max_value=3600)
)
def test_fernet_future_timestamp_rejection(data, key, future_seconds):
    """Test that Fernet rejects tokens from too far in the future."""
    f = Fernet(key)
    current_time = int(time.time())
    
    # Encrypt with a future timestamp
    future_token = f.encrypt_at_time(data, current_time + future_seconds)
    
    # Should fail to decrypt with TTL check due to clock skew
    try:
        f.decrypt_at_time(future_token, ttl=86400, current_time=current_time)
        # If future_seconds > 60 (MAX_CLOCK_SKEW), should have failed
        assert future_seconds <= 60, f"Should reject token from {future_seconds}s in future"
    except InvalidToken:
        # Expected for future_seconds > 60
        assert future_seconds > 60


# Test empty token handling
@given(key=fernet_keys())
def test_fernet_empty_token(key):
    """Test Fernet handling of empty tokens."""
    f = Fernet(key)
    
    # Empty string token
    try:
        f.decrypt(b"")
        assert False, "Should reject empty token"
    except InvalidToken:
        pass  # Expected
    
    # Empty base64
    try:
        f.decrypt(base64.urlsafe_b64encode(b""))
        assert False, "Should reject empty base64 token"
    except InvalidToken:
        pass  # Expected


# Test malformed base64 tokens
@given(
    key=fernet_keys(),
    bad_token=st.text(min_size=1, max_size=100).filter(lambda x: not x.isspace())
)
def test_fernet_malformed_tokens(key, bad_token):
    """Test Fernet handling of malformed tokens."""
    f = Fernet(key)
    
    try:
        f.decrypt(bad_token)
        # If we get here, check if it was accidentally valid base64
        try:
            base64.urlsafe_b64decode(bad_token)
            # It decoded, but should still be invalid format
            assert False, "Accepted malformed token structure"
        except:
            assert False, "Should have rejected non-base64 token"
    except (InvalidToken, TypeError):
        pass  # Expected


# Test padding edge case: single byte less than block size
@given(
    block_size=st.sampled_from([64, 128, 256]),
    offset=st.integers(min_value=1, max_value=127)
)
def test_padding_one_byte_short(block_size, offset):
    """Test padding when data is one byte short of block boundary."""
    block_size_bytes = block_size // 8
    offset = offset % block_size_bytes
    if offset == 0:
        offset = 1
    
    # Data that's one byte short of a block boundary
    data = b'x' * (block_size_bytes - offset)
    
    # PKCS7
    padder = padding.PKCS7(block_size).padder()
    padded = padder.update(data) + padder.finalize()
    assert len(padded) == block_size_bytes  # Should pad to exactly one block
    
    unpadder = padding.PKCS7(block_size).unpadder()
    unpadded = unpadder.update(padded) + unpadder.finalize()
    assert unpadded == data


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])