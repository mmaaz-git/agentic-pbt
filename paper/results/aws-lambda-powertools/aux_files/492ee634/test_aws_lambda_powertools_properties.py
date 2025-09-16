"""Property-based tests for AWS Lambda Powertools"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
import pytest

# Test 1: Base64 round-trip properties for utilities.serialization
from aws_lambda_powertools.utilities.serialization import base64_encode, base64_decode

@given(st.text(min_size=0, max_size=10000))
def test_base64_roundtrip_serialization(text):
    """Test that base64_decode(base64_encode(x)) == x for serialization module"""
    encoded = base64_encode(text)
    decoded = base64_decode(encoded)
    assert decoded == text, f"Round-trip failed: {text!r} -> {encoded!r} -> {decoded!r}"


# Test 2: Base64 round-trip for shared.functions
from aws_lambda_powertools.shared.functions import base64_decode as shared_b64_decode
from aws_lambda_powertools.shared.functions import bytes_to_base64_string

@given(st.binary(min_size=0, max_size=10000))
def test_base64_roundtrip_shared_functions(data):
    """Test that base64_decode(bytes_to_base64_string(x)) == x for shared functions"""
    encoded = bytes_to_base64_string(data)
    decoded = shared_b64_decode(encoded)
    assert decoded == data, f"Round-trip failed for binary data"


# Test 3: strtobool valid inputs
from aws_lambda_powertools.shared.functions import strtobool

VALID_TRUE_VALUES = ["1", "y", "yes", "t", "true", "on", "Y", "YES", "T", "TRUE", "ON"]
VALID_FALSE_VALUES = ["0", "n", "no", "f", "false", "off", "N", "NO", "F", "FALSE", "OFF"]

@given(st.sampled_from(VALID_TRUE_VALUES))
def test_strtobool_true_values(value):
    """Test that strtobool returns True for valid true values"""
    result = strtobool(value)
    assert result is True, f"strtobool({value!r}) should return True"

@given(st.sampled_from(VALID_FALSE_VALUES))
def test_strtobool_false_values(value):
    """Test that strtobool returns False for valid false values"""
    result = strtobool(value)
    assert result is False, f"strtobool({value!r}) should return False"

@given(st.text(min_size=1).filter(lambda x: x.lower() not in ["1", "y", "yes", "t", "true", "on", "0", "n", "no", "f", "false", "off"]))
def test_strtobool_invalid_values(value):
    """Test that strtobool raises ValueError for invalid values"""
    with pytest.raises(ValueError, match="invalid truth value"):
        strtobool(value)


# Test 4: LRUDict max_items invariant
from aws_lambda_powertools.shared.cache_dict import LRUDict

@given(
    max_items=st.integers(min_value=1, max_value=100),
    items=st.lists(
        st.tuples(st.text(min_size=1, max_size=10), st.integers()),
        min_size=0,
        max_size=200
    )
)
def test_lrudict_max_items_invariant(max_items, items):
    """Test that LRUDict never exceeds max_items"""
    cache = LRUDict(max_items=max_items)
    
    for key, value in items:
        cache[key] = value
        assert len(cache) <= max_items, f"Cache exceeded max_items: {len(cache)} > {max_items}"
    
    # Final check
    assert len(cache) <= max_items, f"Final cache size {len(cache)} exceeds max_items {max_items}"


@given(
    items=st.lists(
        st.tuples(st.text(min_size=1, max_size=10), st.integers()),
        min_size=5,
        max_size=20,
        unique_by=lambda x: x[0]  # Ensure unique keys
    )
)
def test_lrudict_access_order(items):
    """Test that accessing an item moves it to the end (most recently used)"""
    if len(items) < 2:
        return  # Need at least 2 items for meaningful test
    
    cache = LRUDict(max_items=len(items) + 10)  # Ensure we don't hit limit
    
    # Insert all items
    for key, value in items:
        cache[key] = value
    
    # Access first item
    first_key = items[0][0]
    _ = cache[first_key]
    
    # The first key should now be at the end (most recently used)
    keys_list = list(cache.keys())
    assert keys_list[-1] == first_key, f"Accessed key {first_key} should be at end, but order is {keys_list}"


# Test 5: slice_dictionary concatenation property
from aws_lambda_powertools.shared.functions import slice_dictionary

@given(
    data=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.integers(),
        min_size=0,
        max_size=50
    ),
    chunk_size=st.integers(min_value=1, max_value=20)
)
def test_slice_dictionary_concatenation(data, chunk_size):
    """Test that concatenating sliced dictionary chunks recreates the original"""
    if not data:  # Empty dict edge case
        chunks = list(slice_dictionary(data, chunk_size))
        assert chunks == [], "Empty dict should produce no chunks"
        return
    
    chunks = list(slice_dictionary(data, chunk_size))
    
    # Each chunk should have at most chunk_size items
    for chunk in chunks:
        assert len(chunk) <= chunk_size, f"Chunk has {len(chunk)} items, exceeds chunk_size {chunk_size}"
    
    # Concatenating all chunks should give us back the original dictionary
    reconstructed = {}
    for chunk in chunks:
        reconstructed.update(chunk)
    
    assert reconstructed == data, f"Reconstructed dict doesn't match original"
    
    # All keys should be present exactly once
    all_keys = []
    for chunk in chunks:
        all_keys.extend(chunk.keys())
    assert sorted(all_keys) == sorted(data.keys()), "Keys mismatch after slicing"


# Test 6: decode_header_bytes property
from aws_lambda_powertools.shared.functions import decode_header_bytes

@given(st.lists(st.integers(min_value=0, max_value=255), min_size=0, max_size=1000))
def test_decode_header_bytes_positive(byte_list):
    """Test decode_header_bytes with positive bytes"""
    result = decode_header_bytes(byte_list)
    assert isinstance(result, bytes)
    assert len(result) == len(byte_list)
    # Verify each byte matches
    for i, b in enumerate(byte_list):
        assert result[i] == b

@given(st.lists(st.integers(min_value=-128, max_value=127), min_size=0, max_size=1000))
def test_decode_header_bytes_signed(byte_list):
    """Test decode_header_bytes with signed bytes"""
    result = decode_header_bytes(byte_list)
    assert isinstance(result, bytes)
    assert len(result) == len(byte_list)
    # Verify conversion from signed to unsigned
    for i, b in enumerate(byte_list):
        expected = b & 0xFF  # Convert to unsigned
        assert result[i] == expected


# Test 7: Check consistency between base64_encode and base64_from_str
from aws_lambda_powertools.utilities.serialization import base64_from_str

@given(st.text(min_size=0, max_size=1000))
def test_base64_encode_consistency(text):
    """Test that base64_encode and base64_from_str produce the same output"""
    result1 = base64_encode(text)
    result2 = base64_from_str(text)
    assert result1 == result2, f"Inconsistent encoding: base64_encode returned {result1!r}, base64_from_str returned {result2!r}"


# Test 8: JSON encoder with Decimal handling
from aws_lambda_powertools.shared.json_encoder import Encoder
import json
import decimal
import math

@given(st.decimals(allow_nan=False, allow_infinity=False))
def test_json_encoder_decimal_roundtrip(dec):
    """Test that non-NaN decimals can be encoded and decoded correctly"""
    encoder = Encoder()
    encoded = encoder.encode(dec)
    # The encoder converts Decimal to string
    decoded = json.loads(encoded)
    assert decoded == str(dec), f"Decimal {dec} encoded as {encoded}, decoded as {decoded}"

@given(st.just(decimal.Decimal('NaN')))
def test_json_encoder_decimal_nan(dec):
    """Test that NaN decimals are encoded as null (JSON's NaN representation)"""
    encoder = Encoder()
    encoded = encoder.encode(dec)
    decoded = json.loads(encoded)
    # According to the code, NaN should be encoded as math.nan, which becomes null in JSON
    assert decoded is None or math.isnan(decoded), f"NaN decimal should encode to null or NaN, got {decoded}"


if __name__ == "__main__":
    # Run property-based tests
    print("Running property-based tests for AWS Lambda Powertools...")
    print("-" * 60)
    
    try:
        print("Test 1: base64 round-trip (serialization module)...")
        test_base64_roundtrip_serialization()
        print("✓ Passed")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    try:
        print("\nTest 2: base64 round-trip (shared functions)...")
        test_base64_roundtrip_shared_functions()
        print("✓ Passed")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    try:
        print("\nTest 3a: strtobool true values...")
        test_strtobool_true_values()
        print("✓ Passed")
    except Exception as e:
        print(f"✗ Failed: {e}")
        
    try:
        print("\nTest 3b: strtobool false values...")
        test_strtobool_false_values()
        print("✓ Passed")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # For test with exceptions, we need to handle differently
    print("\nTest 3c: strtobool invalid values...")
    try:
        # Test a few invalid values manually
        for invalid in ["maybe", "2", "yesno", ""]:
            try:
                strtobool(invalid)
                print(f"✗ Failed: strtobool({invalid!r}) should raise ValueError")
            except ValueError:
                pass  # Expected
        print("✓ Passed")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    try:
        print("\nTest 4: LRUDict max_items invariant...")
        test_lrudict_max_items_invariant()
        print("✓ Passed")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    try:
        print("\nTest 5: LRUDict access order...")
        test_lrudict_access_order()
        print("✓ Passed")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    try:
        print("\nTest 6: slice_dictionary concatenation...")
        test_slice_dictionary_concatenation()
        print("✓ Passed")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    try:
        print("\nTest 7: decode_header_bytes (positive)...")
        test_decode_header_bytes_positive()
        print("✓ Passed")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    try:
        print("\nTest 8: decode_header_bytes (signed)...")
        test_decode_header_bytes_signed()
        print("✓ Passed")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    try:
        print("\nTest 9: base64_encode consistency...")
        test_base64_encode_consistency()
        print("✓ Passed")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    try:
        print("\nTest 10: JSON encoder decimal round-trip...")
        test_json_encoder_decimal_roundtrip()
        print("✓ Passed")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    try:
        print("\nTest 11: JSON encoder NaN handling...")
        test_json_encoder_decimal_nan()
        print("✓ Passed")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print("\n" + "-" * 60)
    print("Testing complete!")