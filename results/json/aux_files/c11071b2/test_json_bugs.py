import json
import math
from hypothesis import given, strategies as st


# Test control characters in strings within JSON values
@given(st.text(alphabet='\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'))
def test_control_chars_in_strings(s):
    # Control characters should be properly escaped and round-trip correctly
    json_str = json.dumps(s)
    result = json.loads(json_str)
    assert result == s


# Test that JSON strings with embedded raw control chars are rejected
@given(st.sampled_from(['\x00', '\x01', '\x08', '\x0c', '\x1f']))
def test_raw_control_chars_rejected(ctrl_char):
    # Create JSON with unescaped control character in string value
    bad_json = '{"key": "value' + ctrl_char + 'more"}'
    try:
        json.loads(bad_json)
        assert False, f"Should have rejected control char {repr(ctrl_char)}"
    except json.JSONDecodeError:
        pass  # Expected


# Test very large floats near the boundary
@given(st.floats(min_value=1e308, max_value=1.7e308))
def test_large_float_boundary(x):
    json_str = json.dumps(x)
    result = json.loads(json_str)
    assert math.isclose(result, x, rel_tol=1e-15)


# Test precision loss with large integers
@given(st.integers(min_value=2**53, max_value=2**64))
def test_large_integer_precision(x):
    # JavaScript's Number type can only safely represent integers up to 2^53-1
    # JSON spec doesn't limit integer size, but implementations might
    json_str = json.dumps(x)
    result = json.loads(json_str)
    assert result == x


# Test string containing only whitespace
@given(st.text(alphabet=' \t\n\r', min_size=1))
def test_whitespace_only_strings(s):
    assert json.loads(json.dumps(s)) == s


# Test dict with empty string keys
def test_empty_string_key():
    d = {"": "value"}
    assert json.loads(json.dumps(d)) == d


# Test surrogate pairs in Unicode
@given(st.text(min_size=1).filter(lambda s: any('\ud800' <= c <= '\udfff' for c in s)))
def test_surrogate_pairs(s):
    # Surrogate pairs in isolation are invalid Unicode but might appear
    try:
        json_str = json.dumps(s)
        result = json.loads(json_str)
        assert result == s
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass  # Some surrogate handling is implementation-dependent


# Test object_pairs_hook preserves duplicate keys
def test_duplicate_keys_preservation():
    json_str = '{"key": 1, "key": 2}'
    pairs = []
    json.loads(json_str, object_pairs_hook=lambda p: pairs.extend(p) or dict(p))
    # Check if duplicate keys were seen
    keys = [k for k, v in pairs]
    assert keys.count("key") == 2


# Test number formats
@given(st.sampled_from(['1e', '1e+', '1e-', '1.', '.1', '+1', '01']))
def test_number_edge_cases(num_str):
    try:
        result = json.loads(num_str)
        # These should either parse correctly or raise an error
        assert isinstance(result, (int, float))
    except json.JSONDecodeError:
        pass  # Some of these are invalid


# Test ensure_ascii with surrogates
def test_ensure_ascii_with_unpaired_surrogate():
    # Test unpaired surrogate handling
    try:
        s = '\ud800'  # Unpaired high surrogate
        json_str = json.dumps(s, ensure_ascii=True)
        result = json.loads(json_str)
        assert result == s
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass


# Test very deep nesting beyond default recursion limit
def test_extremely_deep_nesting():
    # Python's default recursion limit is typically 1000
    depth = 2000
    
    # Create deeply nested list
    s = '[' * depth + '1' + ']' * depth
    
    # This might hit recursion limit or other implementation limits
    try:
        result = json.loads(s)
        # Verify structure if it succeeds
        current = result
        for _ in range(depth - 1):
            assert isinstance(current, list) and len(current) == 1
            current = current[0]
        assert current == 1
    except (RecursionError, json.JSONDecodeError):
        pass  # Implementation limit reached


# Test interaction between parse_float and special values
def test_parse_float_with_infinity():
    json_str = json.dumps(float('inf'))
    
    def custom_float(s):
        if s == 'Infinity':
            return 'CUSTOM_INF'
        return float(s)
    
    result = json.loads(json_str, parse_float=custom_float)
    assert result == 'CUSTOM_INF'


# Test null bytes in strings
def test_null_bytes_in_strings():
    s = "hello\x00world"
    assert json.loads(json.dumps(s)) == s


# Test that leading zeros in numbers are rejected
def test_leading_zeros_rejected():
    invalid_numbers = ['01', '00', '0123', '-01', '-00']
    for num in invalid_numbers:
        json_str = f'{{{num}: "value"}}'
        try:
            json.loads(json_str)
            assert False, f"Should have rejected {num}"
        except json.JSONDecodeError:
            pass  # Expected
        
        # But in strings they're fine
        json_str = f'{{"key": "{num}"}}'
        result = json.loads(json_str)
        assert result == {"key": num}


# Test comma handling
def test_trailing_comma_rejected():
    invalid_jsons = [
        '[1, 2, 3,]',
        '{"a": 1, "b": 2,}',
        '[1, 2, 3, ]',
        '{"a": 1,}'
    ]
    for json_str in invalid_jsons:
        try:
            json.loads(json_str)
            assert False, f"Should have rejected trailing comma in {json_str}"
        except json.JSONDecodeError:
            pass  # Expected


# Test that duplicate keys use the last value
def test_duplicate_keys_last_wins():
    json_str = '{"key": 1, "key": 2, "key": 3}'
    result = json.loads(json_str)
    assert result == {"key": 3}


# Test very long strings
@given(st.integers(min_value=100000, max_value=1000000))
def test_very_long_strings(length):
    s = "x" * length
    assert json.loads(json.dumps(s)) == s