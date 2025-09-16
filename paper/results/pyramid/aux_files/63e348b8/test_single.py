#!/usr/bin/env python3
"""Test a single property to check for bugs."""

import sys
import base64
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

import trino.client as client
from trino.client import InlineSegment

# Test 1: Simple base64 round-trip test
def test_base64_simple():
    """Manual test of base64 encoding in InlineSegment."""
    
    # Test with simple binary data
    original_data = b"Hello, World!"
    encoded = base64.b64encode(original_data).decode('utf-8')
    
    segment_data = {
        "type": "inline",
        "data": encoded,
        "metadata": {"segmentSize": str(len(original_data))}
    }
    
    segment = InlineSegment(segment_data)
    decoded_data = segment.data
    
    print(f"Original: {original_data}")
    print(f"Encoded: {encoded}")
    print(f"Decoded: {decoded_data}")
    print(f"Match: {original_data == decoded_data}")
    
    assert original_data == decoded_data, "Base64 round-trip failed!"
    print("✓ Base64 test passed")
    
    # Test with empty data
    original_data = b""
    encoded = base64.b64encode(original_data).decode('utf-8')
    
    segment_data = {
        "type": "inline",
        "data": encoded,
        "metadata": {"segmentSize": "0"}
    }
    
    segment = InlineSegment(segment_data)
    decoded_data = segment.data
    
    assert original_data == decoded_data, "Empty data round-trip failed!"
    print("✓ Empty data test passed")


# Test 2: URL encoding test
def test_url_encoding():
    """Test URL encoding/decoding used in headers."""
    import urllib.parse
    
    test_cases = [
        "",  # empty string
        "simple",
        "with spaces",
        "special!@#$%^&*()",
        "unicode: 你好",
        "=equals=in=string=",
    ]
    
    for text in test_cases:
        encoded = urllib.parse.quote_plus(text)
        decoded = urllib.parse.unquote_plus(encoded)
        print(f"Text: '{text}' -> '{encoded}' -> '{decoded}'")
        assert decoded == text, f"Round-trip failed for: {text}"
    
    print("✓ URL encoding tests passed")


# Test 3: Header parsing
def test_header_parsing():
    """Test header value parsing functions."""
    from trino.client import get_header_values, get_session_property_values
    
    # Test simple comma-separated values
    headers = {'X-Test': 'value1, value2, value3'}
    parsed = get_header_values(headers, 'X-Test')
    print(f"Parsed values: {parsed}")
    assert parsed == ['value1', 'value2', 'value3']
    
    # Test with extra spaces
    headers = {'X-Test': ' value1 , value2 , value3 '}
    parsed = get_header_values(headers, 'X-Test')
    print(f"Parsed with spaces: {parsed}")
    assert parsed == ['value1', 'value2', 'value3']
    
    # Test session properties parsing
    headers = {'X-Session': 'key1=value1,key2=value2'}
    parsed = get_session_property_values(headers, 'X-Session')
    print(f"Parsed session props: {parsed}")
    assert parsed == [('key1', 'value1'), ('key2', 'value2')]
    
    # Test with URL-encoded values
    import urllib.parse
    encoded_value = urllib.parse.quote_plus("value with spaces")
    headers = {'X-Session': f'key={encoded_value}'}
    parsed = get_session_property_values(headers, 'X-Session')
    print(f"Parsed URL-encoded: {parsed}")
    assert parsed == [('key', 'value with spaces')]
    
    print("✓ Header parsing tests passed")


# Test 4: Exponential backoff
def test_exponential_backoff():
    """Test exponential backoff calculation."""
    from trino.client import _DelayExponential
    
    # Test without jitter
    calc = _DelayExponential(base=0.1, exponent=2, jitter=False, max_delay=10)
    
    delays = []
    for attempt in range(5):
        delay = calc(attempt)
        delays.append(delay)
        print(f"Attempt {attempt}: delay = {delay}")
    
    # Check that delays are increasing exponentially
    assert delays[0] == 0.1  # 0.1 * 2^0 = 0.1
    assert delays[1] == 0.2  # 0.1 * 2^1 = 0.2
    assert delays[2] == 0.4  # 0.1 * 2^2 = 0.4
    assert delays[3] == 0.8  # 0.1 * 2^3 = 0.8
    assert delays[4] == 1.6  # 0.1 * 2^4 = 1.6
    
    # Test max delay
    calc = _DelayExponential(base=1, exponent=2, jitter=False, max_delay=5)
    delay = calc(10)  # Would be 1024 without max
    print(f"Delay with max: {delay}")
    assert delay == 5, "Max delay not respected"
    
    print("✓ Exponential backoff tests passed")


# Test 5: Extra credential validation
def test_credential_validation():
    """Test extra credential key validation."""
    
    # Test valid keys
    valid_keys = [
        "simple_key",
        "key-with-dashes",
        "KEY_WITH_UNDERSCORES",
        "key123",
    ]
    
    for key in valid_keys:
        try:
            client.TrinoRequest._verify_extra_credential((key, "value"))
            print(f"✓ Valid key accepted: {key}")
        except ValueError as e:
            print(f"✗ Valid key rejected: {key} - {e}")
            raise
    
    # Test invalid keys
    invalid_keys = [
        "key with spaces",  # spaces not allowed
        "key=with=equals",  # equals not allowed
        "key\twith\ttabs",  # tabs not allowed
        " leadingspace",    # leading space
        "trailingspace ",   # trailing space
        "unicode_你好",      # non-ASCII
    ]
    
    for key in invalid_keys:
        try:
            client.TrinoRequest._verify_extra_credential((key, "value"))
            print(f"✗ Invalid key accepted: {key}")
            assert False, f"Should have rejected key: {key}"
        except ValueError:
            print(f"✓ Invalid key rejected: {key}")
    
    print("✓ Credential validation tests passed")


if __name__ == "__main__":
    print("Running manual property tests...\n")
    
    test_base64_simple()
    print()
    
    test_url_encoding()
    print()
    
    test_header_parsing()
    print()
    
    test_exponential_backoff()
    print()
    
    test_credential_validation()
    print()
    
    print("\n" + "=" * 60)
    print("All manual tests passed!")