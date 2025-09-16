"""Property-based tests for aws_lambda_powertools.tracing module using Hypothesis."""

import sys
import re
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.shared.functions import (
    strtobool,
    resolve_truthy_env_var_choice,
    base64_decode,
    bytes_to_base64_string,
    slice_dictionary,
    sanitize_xray_segment_name,
)
from aws_lambda_powertools.shared.constants import INVALID_XRAY_NAME_CHARACTERS


# Test 1: Base64 round-trip property
@given(st.binary(min_size=0, max_size=10000))
def test_base64_round_trip(data):
    """Test that base64 encoding and decoding is a perfect round-trip."""
    encoded = bytes_to_base64_string(data)
    decoded = base64_decode(encoded)
    assert decoded == data, f"Round-trip failed: {data[:50]}... != {decoded[:50]}..."


# Test 2: sanitize_xray_segment_name idempotence
@given(st.text(min_size=0, max_size=1000))
def test_sanitize_xray_segment_name_idempotence(name):
    """Test that sanitizing a name twice is the same as sanitizing once."""
    once = sanitize_xray_segment_name(name)
    twice = sanitize_xray_segment_name(once)
    assert once == twice, f"Not idempotent: {repr(once)} != {repr(twice)}"


# Test 3: sanitize_xray_segment_name only removes invalid characters
@given(st.text(min_size=0, max_size=1000))
def test_sanitize_xray_segment_name_invariant(name):
    """Test that sanitization only removes characters from INVALID_XRAY_NAME_CHARACTERS."""
    sanitized = sanitize_xray_segment_name(name)
    
    # Check that no invalid characters remain
    invalid_pattern = re.compile(INVALID_XRAY_NAME_CHARACTERS)
    assert not invalid_pattern.search(sanitized), f"Invalid characters remain in: {repr(sanitized)}"
    
    # Check that all removed characters were invalid
    removed_chars = set(name) - set(sanitized)
    invalid_chars = set(re.findall(INVALID_XRAY_NAME_CHARACTERS, name))
    assert removed_chars <= invalid_chars, f"Valid characters were removed: {removed_chars - invalid_chars}"
    
    # Check that length only decreases
    assert len(sanitized) <= len(name), f"Length increased: {len(name)} -> {len(sanitized)}"


# Test 4: strtobool known values
@given(st.sampled_from([
    ("1", True), ("y", True), ("yes", True), ("t", True), ("true", True), ("on", True),
    ("Y", True), ("YES", True), ("T", True), ("TRUE", True), ("ON", True),
    ("0", False), ("n", False), ("no", False), ("f", False), ("false", False), ("off", False),
    ("N", False), ("NO", False), ("F", False), ("FALSE", False), ("OFF", False),
]))
def test_strtobool_known_values(value_and_expected):
    """Test that strtobool correctly converts known string values."""
    value, expected = value_and_expected
    assert strtobool(value) == expected, f"strtobool('{value}') should be {expected}"


# Test 5: strtobool invalid values
@given(st.text(min_size=1, max_size=50).filter(
    lambda x: x.lower() not in ["1", "y", "yes", "t", "true", "on", "0", "n", "no", "f", "false", "off"]
))
def test_strtobool_invalid_values(value):
    """Test that strtobool raises ValueError for invalid inputs."""
    with pytest.raises(ValueError, match=f"invalid truth value"):
        strtobool(value)


# Test 6: resolve_truthy_env_var_choice consistency
@given(
    env=st.sampled_from(["true", "false", "1", "0", "yes", "no"]),
    choice=st.one_of(st.none(), st.booleans())
)
def test_resolve_truthy_env_var_choice_consistency(env, choice):
    """Test that explicit choice always overrides env value."""
    result = resolve_truthy_env_var_choice(env, choice)
    
    if choice is not None:
        assert result == choice, f"Explicit choice {choice} not returned"
    else:
        assert result == strtobool(env), f"Env value not converted correctly"


# Test 7: slice_dictionary confluence - chunks reconstruct to original
@given(
    data=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(st.integers(), st.text(), st.booleans()),
        min_size=0,
        max_size=100
    ),
    chunk_size=st.integers(min_value=1, max_value=20)
)
def test_slice_dictionary_confluence(data, chunk_size):
    """Test that sliced dictionary chunks can be reconstructed to the original."""
    chunks = list(slice_dictionary(data, chunk_size))
    
    # Reconstruct the dictionary from chunks
    reconstructed = {}
    for chunk in chunks:
        reconstructed.update(chunk)
    
    assert reconstructed == data, f"Reconstruction failed: {data} != {reconstructed}"
    
    # Verify no keys are lost or duplicated
    all_keys = set()
    for chunk in chunks:
        chunk_keys = set(chunk.keys())
        assert len(all_keys & chunk_keys) == 0, f"Duplicate keys found: {all_keys & chunk_keys}"
        all_keys.update(chunk_keys)
    
    assert all_keys == set(data.keys()), f"Keys mismatch: {all_keys} != {set(data.keys())}"


# Test 8: slice_dictionary chunk size invariant
@given(
    data=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.integers(),
        min_size=1,
        max_size=100
    ),
    chunk_size=st.integers(min_value=1, max_value=50)
)
def test_slice_dictionary_chunk_size_invariant(data, chunk_size):
    """Test that all chunks except possibly the last one have the correct size."""
    chunks = list(slice_dictionary(data, chunk_size))
    
    if not chunks:
        assert len(data) == 0
        return
    
    # All chunks except the last should have size == chunk_size
    for i, chunk in enumerate(chunks[:-1]):
        assert len(chunk) == chunk_size, f"Chunk {i} has size {len(chunk)}, expected {chunk_size}"
    
    # Last chunk should have size <= chunk_size
    last_chunk = chunks[-1]
    assert 0 < len(last_chunk) <= chunk_size, f"Last chunk has invalid size {len(last_chunk)}"
    
    # Total number of items should match
    total_items = sum(len(chunk) for chunk in chunks)
    assert total_items == len(data), f"Total items {total_items} != original {len(data)}"


# Test 9: bytes_to_base64_string produces valid base64
@given(st.binary(min_size=0, max_size=10000))
def test_bytes_to_base64_string_valid_output(data):
    """Test that bytes_to_base64_string produces valid base64 strings."""
    import base64
    
    encoded = bytes_to_base64_string(data)
    
    # Should be a string
    assert isinstance(encoded, str)
    
    # Should be valid base64 (can be decoded)
    try:
        decoded = base64.b64decode(encoded)
        assert decoded == data
    except Exception as e:
        pytest.fail(f"Invalid base64 produced: {e}")
    
    # Base64 should only contain valid characters
    import string
    valid_chars = set(string.ascii_letters + string.digits + '+/=')
    assert all(c in valid_chars for c in encoded), f"Invalid characters in base64: {set(encoded) - valid_chars}"


# Test 10: Test edge cases for sanitize_xray_segment_name
@given(st.text(alphabet=INVALID_XRAY_NAME_CHARACTERS.strip('[]'), min_size=0, max_size=100))
def test_sanitize_xray_segment_name_all_invalid(name):
    """Test that a name consisting only of invalid characters becomes empty."""
    sanitized = sanitize_xray_segment_name(name)
    assert sanitized == "", f"Name with only invalid chars should be empty, got: {repr(sanitized)}"


# Test 11: Metamorphic property for sanitize_xray_segment_name
@given(
    prefix=st.text(min_size=0, max_size=50).map(lambda x: x.replace('?', '').replace(';', '')),
    suffix=st.text(min_size=0, max_size=50).map(lambda x: x.replace('?', '').replace(';', '')),
    invalid_part=st.text(alphabet='?;*()!$~^<>', min_size=1, max_size=20)
)
def test_sanitize_xray_segment_name_metamorphic(prefix, suffix, invalid_part):
    """Test that adding invalid characters doesn't affect valid parts."""
    # Clean name without invalid characters
    clean_name = prefix + suffix
    clean_sanitized = sanitize_xray_segment_name(clean_name)
    
    # Name with invalid characters inserted
    dirty_name = prefix + invalid_part + suffix
    dirty_sanitized = sanitize_xray_segment_name(dirty_name)
    
    # The sanitized versions should be the same
    assert clean_sanitized == dirty_sanitized, f"Metamorphic property violated: {repr(clean_sanitized)} != {repr(dirty_sanitized)}"


# Test 12: Test decode_header_bytes function
try:
    from aws_lambda_powertools.shared.functions import decode_header_bytes
    
    @given(st.lists(st.integers(min_value=-128, max_value=255), min_size=0, max_size=1000))
    def test_decode_header_bytes_handles_signed(byte_list):
        """Test that decode_header_bytes correctly handles signed and unsigned bytes."""
        result = decode_header_bytes(byte_list)
        assert isinstance(result, bytes)
        
        # Convert negative values to unsigned for comparison
        expected_bytes = bytes((b & 0xFF) if b < 0 else b for b in byte_list)
        assert result == expected_bytes
        
    @given(st.lists(st.integers(min_value=0, max_value=255), min_size=0, max_size=1000))
    def test_decode_header_bytes_unsigned_only(byte_list):
        """Test that decode_header_bytes works correctly with only unsigned bytes."""
        result = decode_header_bytes(byte_list)
        assert isinstance(result, bytes)
        assert result == bytes(byte_list)
        
except ImportError:
    pass  # Function might not be exported


if __name__ == "__main__":
    # Run all tests with increased examples for better coverage
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))