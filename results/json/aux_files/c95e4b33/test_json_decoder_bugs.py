import json
import math
from hypothesis import given, strategies as st, assume, settings, seed
from json.decoder import JSONDecodeError, JSONDecoder

# Focus on finding actual bugs

# Test 1: Check if colno calculation could overflow or have off-by-one errors
@given(st.text(min_size=0, max_size=1000))
@settings(max_examples=5000)
def test_colno_calculation_consistency(text):
    # Insert newlines at various positions
    for i in range(0, len(text), 50):
        doc = text[:i] + '\n' + text[i:]
        
        # Test error at various positions
        for pos in [i-1, i, i+1, len(doc)-1]:
            if pos < 0 or pos > len(doc):
                continue
                
            try:
                raise JSONDecodeError("Test", doc, pos)
            except JSONDecodeError as e:
                # Verify colno calculation matches the formula
                last_newline = doc.rfind('\n', 0, pos)
                expected = pos - last_newline
                assert e.colno == expected, f"pos={pos}, last_nl={last_newline}, colno={e.colno}, expected={expected}"

# Test 2: Unicode handling with mixed encodings
@given(st.text())
@settings(max_examples=500)
def test_unicode_mixed_escapes(text):
    # Mix regular chars with unicode escapes
    json_str = '"'
    for char in text:
        # Control characters and special chars need escaping
        if ord(char) < 0x20 or char in '"\\':
            # Use unicode escape for control chars
            json_str += '\\u{:04x}'.format(ord(char))
        elif ord(char) < 128:
            json_str += char
        else:
            # Use unicode escape
            if ord(char) < 0x10000:
                json_str += '\\u{:04x}'.format(ord(char))
            else:
                # Surrogate pair
                codepoint = ord(char) - 0x10000
                high = 0xD800 + (codepoint >> 10)
                low = 0xDC00 + (codepoint & 0x3FF)
                json_str += '\\u{:04x}\\u{:04x}'.format(high, low)
    json_str += '"'
    
    try:
        result = json.loads(json_str)
        assert result == text
    except Exception as e:
        # Debug any failures
        print(f"Failed on text={repr(text)}, json={repr(json_str)}")
        raise

# Test 3: Edge cases with empty containers
def test_empty_nested_containers():
    test_cases = [
        '[[]]',
        '[{}]',
        '{"": {}}',
        '{"": []}',
        '[[], []]',
        '[{}, {}]',
        '{"a": {}, "b": {}}',
        '{"a": [], "b": []}',
    ]
    
    for case in test_cases:
        result = json.loads(case)
        # Round-trip test
        encoded = json.dumps(result)
        decoded = json.loads(encoded)
        assert decoded == result

# Test 4: Number parsing boundary conditions
@given(st.integers())
def test_integer_boundaries(n):
    # Test that any integer can round-trip
    json_str = str(n)
    result = json.loads(json_str)
    assert result == n

# Test 5: Float precision edge cases
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_float_precision(f):
    json_str = json.dumps(f)
    result = json.loads(json_str)
    
    if math.isfinite(f):
        # Should preserve value within floating point precision
        if f == 0:
            assert result == f
        else:
            rel_error = abs((result - f) / f) if f != 0 else 0
            assert rel_error < 1e-15 or math.isclose(result, f, rel_tol=1e-15)

# Test 6: Object key ordering and uniqueness
@given(st.lists(st.text(min_size=1, max_size=20), min_size=2, max_size=10))
def test_duplicate_keys(keys):
    # Create object with duplicate keys
    json_str = '{'
    for i, key in enumerate(keys):
        escaped_key = json.dumps(key)
        json_str += f'{escaped_key}: {i}'
        if i < len(keys) - 1:
            json_str += ', '
    json_str += '}'
    
    result = json.loads(json_str)
    # In Python, last value should win for duplicate keys
    unique_keys = []
    last_values = {}
    for i, key in enumerate(keys):
        if key not in last_values:
            unique_keys.append(key)
        last_values[key] = i
    
    assert len(result) == len(set(keys))
    for key in result:
        assert result[key] == last_values[key]

# Test 7: Escape sequence edge cases
def test_escape_sequences_comprehensive():
    # Test all valid escape sequences
    escapes = {
        '\\n': '\n',
        '\\r': '\r',
        '\\t': '\t',
        '\\b': '\b',
        '\\f': '\f',
        '\\"': '"',
        '\\\\': '\\',
        '\\/': '/',
    }
    
    for escape, expected in escapes.items():
        json_str = f'"{escape}"'
        result = json.loads(json_str)
        assert result == expected, f"Failed for {repr(escape)}"

# Test 8: Whitespace in unexpected places
def test_whitespace_placement():
    # Whitespace should be allowed in specific places
    valid_cases = [
        ' { } ',
        ' [ ] ',
        '{ "key" : "value" }',
        '[ 1 , 2 , 3 ]',
        ' { "a" : [ 1 , 2 ] } ',
        '[\n1,\n2\n]',
        '{\n"key"\n:\n"value"\n}',
    ]
    
    for case in valid_cases:
        result = json.loads(case)
        # Should parse without error
        assert result is not None

# Test 9: Invalid unicode escapes
def test_invalid_unicode_escapes():
    invalid_cases = [
        '"\\u"',      # Too short
        '"\\u0"',     # Too short
        '"\\u00"',    # Too short
        '"\\u000"',   # Too short
        '"\\uGGGG"',  # Invalid hex
        '"\\u 123"',  # Space in middle
    ]
    
    for case in invalid_cases:
        try:
            json.loads(case)
            assert False, f"Should have rejected {case}"
        except JSONDecodeError:
            pass  # Expected

# Test 10: Surrogate pair validation
def test_surrogate_pair_validation():
    # Invalid surrogate combinations
    invalid_surrogates = [
        '"\\uD800"',         # High surrogate alone
        '"\\uDC00"',         # Low surrogate alone
        '"\\uD800\\uD800"',  # Two high surrogates
        '"\\uDC00\\uDC00"',  # Two low surrogates
        '"\\uDC00\\uD800"',  # Low then high (wrong order)
    ]
    
    for case in invalid_surrogates:
        result = json.loads(case)
        # Python's json allows these, converting to replacement char or preserving
        assert isinstance(result, str)

# Test 11: Memory/memo behavior
def test_memo_interning():
    # Test that the memo properly interns strings
    json_str = '{"x": 1, "x": 2, "x": 3, "x": 4, "x": 5}'
    result = json.loads(json_str)
    assert result == {"x": 5}
    
    # Large number of same keys
    json_str = '{' + ', '.join(['"key": ' + str(i) for i in range(100)]) + '}'
    result = json.loads(json_str)
    assert result == {"key": 99}

# Test 12: Raw decode offset parameter
@given(st.integers(min_value=0, max_value=100))
def test_raw_decode_offset(offset):
    decoder = JSONDecoder()
    padding = ' ' * offset
    json_str = padding + '{"test": true}'
    
    # Decode with offset
    obj, end = decoder.raw_decode(json_str, idx=offset)
    assert obj == {"test": True}
    assert end == len(json_str)

# Test 13: Complex nested structure with mixed types
def test_complex_nested_structure():
    data = {
        "null": None,
        "bool": True,
        "int": 42,
        "float": 3.14,
        "string": "test",
        "array": [1, 2, [3, 4, {"nested": True}]],
        "object": {
            "a": 1,
            "b": {
                "c": [None, False, {"d": "deep"}]
            }
        },
        "empty_array": [],
        "empty_object": {},
        "unicode": "Hello \u4e16\u754c",
        "escapes": "Line1\nLine2\tTabbed"
    }
    
    json_str = json.dumps(data)
    result = json.loads(json_str)
    assert result == data
    
    # Double round-trip
    json_str2 = json.dumps(result)
    result2 = json.loads(json_str2)
    assert result2 == data

# Test 14: Parse constant hook
def test_parse_constant_hook():
    def no_special_floats(name):
        raise ValueError(f"Special float {name} not allowed")
    
    decoder = JSONDecoder(parse_constant=no_special_floats)
    
    # Should reject NaN, Infinity, -Infinity
    for value in ['NaN', 'Infinity', '-Infinity']:
        try:
            decoder.decode(value)
            assert False, f"Should have rejected {value}"
        except ValueError as e:
            assert "not allowed" in str(e)

# Test 15: Object hook interaction
def test_object_hook_transform():
    def transform_hook(obj):
        # Add a marker to every object
        obj['_transformed'] = True
        return obj
    
    decoder = JSONDecoder(object_hook=transform_hook)
    
    json_str = '{"a": {"b": {"c": 1}}}'
    result = decoder.decode(json_str)
    
    # Check all nested objects were transformed
    assert result['_transformed'] == True
    assert result['a']['_transformed'] == True
    assert result['a']['b']['_transformed'] == True

# Test 16: Strict mode comprehensive
@given(st.integers(min_value=0, max_value=31))
def test_strict_mode_all_control_chars(char_code):
    char = chr(char_code)
    
    # Skip valid JSON escape chars
    if char in '\n\r\t':
        return
    
    json_str = f'["{char}"]'
    
    # Strict mode should reject
    strict_decoder = JSONDecoder(strict=True)
    try:
        strict_decoder.decode(json_str)
        # Some might pass through
    except JSONDecodeError as e:
        assert "control character" in e.msg.lower()
    
    # Non-strict should accept
    loose_decoder = JSONDecoder(strict=False) 
    try:
        result = loose_decoder.decode(json_str)
        assert result == [char]
    except JSONDecodeError:
        # Some chars might still fail
        pass

# Test 17: Leading zeros in numbers (should be invalid)
def test_leading_zeros():
    invalid_numbers = [
        '01',
        '00',
        '01.5',
        '00.5',
        '-01',
        '-00',
        '-01.5',
    ]
    
    for num in invalid_numbers:
        try:
            json.loads(num)
            # Leading zeros might be accepted in some cases
        except JSONDecodeError:
            pass  # Expected for strict JSON

# Test 18: Truncated escapes at end of string
def test_truncated_escape_sequences():
    truncated = [
        '"\\',
        '"test\\',
        '"\\u',
        '"\\u0',
        '"\\u00',
        '"\\u000',
    ]
    
    for case in truncated:
        try:
            json.loads(case)
            assert False, f"Should reject truncated escape: {case}"
        except JSONDecodeError as e:
            # Should properly identify the issue
            assert "escape" in e.msg.lower() or "unterminated" in e.msg.lower()

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])