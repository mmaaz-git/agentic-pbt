import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
from decimal import Decimal, Context
import base64
import pytest
from datetime import datetime, timedelta

# Import the modules we're testing
from aws_lambda_powertools.shared.cache_dict import LRUDict
from aws_lambda_powertools.shared.dynamodb_deserializer import TypeDeserializer, DYNAMODB_CONTEXT
from aws_lambda_powertools.shared.cookies import Cookie, SameSite
from aws_lambda_powertools.shared.functions import (
    strtobool, base64_decode, bytes_to_base64_string,
    slice_dictionary, decode_header_bytes
)
from aws_lambda_powertools.shared.json_encoder import Encoder
import json
import math


# Test 1: LRUDict.get() doesn't properly track access for falsy values
@given(
    st.one_of(
        st.just(0),
        st.just(False),
        st.just(""),
        st.just([]),
        st.just({}),
        st.just(None)
    )
)
def test_lrudict_get_falsy_values_not_moved_to_end(falsy_value):
    """Test that LRUDict.get() doesn't properly move falsy values to end, breaking LRU ordering"""
    cache = LRUDict(max_items=3)
    
    # Add three items including our falsy value
    cache["a"] = "first"
    cache["b"] = falsy_value  # falsy value in the middle
    cache["c"] = "third"
    
    # Access the falsy value using get()
    retrieved = cache.get("b")
    assert retrieved == falsy_value
    
    # Add a fourth item to trigger eviction
    cache["d"] = "fourth"
    
    # In a correct LRU, "a" should be evicted (oldest)
    # But since "b" wasn't moved to end, it might be evicted instead
    # The bug is that get() doesn't call move_to_end for falsy values
    
    # Check which key was evicted
    if "b" not in cache and "a" in cache:
        # Bug confirmed: falsy value was evicted despite being accessed
        assert False, f"Falsy value {falsy_value!r} was evicted despite recent access via get()"


# Test 2: DynamoDB Number deserializer precision handling
@given(
    st.text(alphabet="0123456789", min_size=39, max_size=100)
)
def test_dynamodb_number_deserializer_precision_loss(number_str):
    """Test DynamoDB number deserializer with values over 38 digits"""
    deserializer = TypeDeserializer()
    
    # Ensure we have a valid number string (not all zeros)
    assume(not all(c == '0' for c in number_str))
    
    # Create a DynamoDB number type
    dynamodb_value = {"N": number_str}
    
    # Deserialize it
    result = deserializer.deserialize(dynamodb_value)
    
    # Check that result is a Decimal with at most 38 significant digits
    assert isinstance(result, Decimal)
    
    # The implementation truncates to 38 digits, removing trailing zeros if present
    # Let's verify the truncation logic
    stripped = number_str.lstrip("0")
    if len(stripped) > 38:
        # Count trailing zeros after 38th character
        tail = len(stripped[38:]) - len(stripped[38:].rstrip("0"))
        expected_str = stripped[:-tail] if tail > 0 else stripped[:38]
        
        # The result should match our expected truncation
        result_str = str(result).lstrip("0")
        if result_str == "":
            result_str = "0"
        assert result_str == expected_str or result_str == expected_str.rstrip("0")


# Test 3: Cookie max_age property - negative values should set to 0
@given(st.integers(max_value=-1))
def test_cookie_negative_max_age_becomes_zero(max_age):
    """Test that negative max_age values are serialized as Max-Age=0"""
    cookie = Cookie(
        name="test",
        value="value",
        max_age=max_age
    )
    
    cookie_str = str(cookie)
    
    # According to the code, negative max_age should become "Max-Age=0"
    assert "; Max-Age=0" in cookie_str
    assert f"; Max-Age={max_age}" not in cookie_str


# Test 4: Base64 round-trip property
@given(st.binary(min_size=0, max_size=10000))
def test_base64_round_trip(original_bytes):
    """Test that base64 encoding and decoding is a perfect round-trip"""
    # Encode to base64 string
    encoded = bytes_to_base64_string(original_bytes)
    
    # Decode back to bytes
    decoded = base64_decode(encoded)
    
    # Should be identical
    assert decoded == original_bytes


# Test 5: strtobool function edge cases
@given(st.text())
def test_strtobool_invalid_inputs(text):
    """Test strtobool with invalid inputs"""
    valid_true = {"1", "y", "yes", "t", "true", "on"}
    valid_false = {"0", "n", "no", "f", "false", "off"}
    
    if text.lower() not in valid_true and text.lower() not in valid_false:
        with pytest.raises(ValueError):
            strtobool(text)


# Test 6: JSON Encoder Decimal NaN handling
def test_json_encoder_decimal_nan():
    """Test that Decimal NaN is encoded as math.nan"""
    encoder = Encoder()
    
    # Create a Decimal NaN
    nan_decimal = Decimal('NaN')
    
    # Encode it
    result = encoder.default(nan_decimal)
    
    # Should be math.nan
    assert math.isnan(result)


# Test 7: slice_dictionary generator property
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.integers(),
        min_size=0,
        max_size=20
    ),
    st.integers(min_value=1, max_value=10)
)
def test_slice_dictionary_preserves_all_items(data, chunk_size):
    """Test that slice_dictionary preserves all dictionary items"""
    chunks = list(slice_dictionary(data, chunk_size))
    
    # Reconstruct the dictionary from chunks
    reconstructed = {}
    for chunk in chunks:
        reconstructed.update(chunk)
    
    # Should have all original items
    assert reconstructed == data


# Test 8: decode_header_bytes with signed bytes
@given(st.lists(st.integers(min_value=-128, max_value=255), min_size=0, max_size=100))
def test_decode_header_bytes_signed_unsigned(byte_list):
    """Test decode_header_bytes handles signed and unsigned bytes correctly"""
    result = decode_header_bytes(byte_list)
    
    # Result should be bytes
    assert isinstance(result, bytes)
    
    # If there are negative values, they should be converted to unsigned
    has_negative = any(b < 0 for b in byte_list)
    
    if has_negative:
        # Check conversion of signed to unsigned
        expected_bytes = bytes((b & 0xFF) for b in byte_list)
        assert result == expected_bytes
    else:
        # Should be normal bytes construction
        expected_bytes = bytes(b for b in byte_list if 0 <= b <= 255)
        assert result == expected_bytes


# Test 9: Cookie date formatting
@given(
    st.datetimes(
        min_value=datetime(1970, 1, 1),
        max_value=datetime(2100, 1, 1)
    )
)
def test_cookie_expires_date_format(dt):
    """Test that Cookie expires date is formatted correctly"""
    cookie = Cookie(
        name="test",
        value="value",
        expires=dt
    )
    
    cookie_str = str(cookie)
    
    # Check that the date is formatted according to spec
    expected_format = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
    assert f"; Expires={expected_format}" in cookie_str


if __name__ == "__main__":
    # Run the tests
    print("Running property-based tests for aws_lambda_powertools.shared...")
    
    # Test 1: LRUDict falsy values bug
    print("\n1. Testing LRUDict.get() with falsy values...")
    test_lrudict_get_falsy_values_not_moved_to_end()
    
    # Test 2: DynamoDB precision
    print("2. Testing DynamoDB number deserializer precision...")
    test_dynamodb_number_deserializer_precision_loss()
    
    # Test 3: Cookie max_age
    print("3. Testing Cookie negative max_age...")
    test_cookie_negative_max_age_becomes_zero()
    
    # Test 4: Base64 round-trip
    print("4. Testing base64 round-trip...")
    test_base64_round_trip()
    
    # Test 5: strtobool
    print("5. Testing strtobool invalid inputs...")
    test_strtobool_invalid_inputs()
    
    # Test 6: JSON Encoder Decimal NaN
    print("6. Testing JSON Encoder Decimal NaN...")
    test_json_encoder_decimal_nan()
    
    # Test 7: slice_dictionary
    print("7. Testing slice_dictionary...")
    test_slice_dictionary_preserves_all_items()
    
    # Test 8: decode_header_bytes
    print("8. Testing decode_header_bytes...")
    test_decode_header_bytes_signed_unsigned()
    
    # Test 9: Cookie date format
    print("9. Testing Cookie expires date format...")
    test_cookie_expires_date_format()
    
    print("\nAll tests completed!")