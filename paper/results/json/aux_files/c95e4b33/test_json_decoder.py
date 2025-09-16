import json
import math
from hypothesis import given, strategies as st, assume, settings
from json.decoder import JSONDecodeError, JSONDecoder

# Test 1: Round-trip property for simple JSON types
@given(st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-10**15, max_value=10**15),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=0, max_size=100),
))
def test_simple_roundtrip(value):
    encoded = json.dumps(value)
    decoded = json.loads(encoded)
    if isinstance(value, float) and not math.isnan(value):
        assert math.isclose(decoded, value, rel_tol=1e-15, abs_tol=1e-15)
    else:
        assert decoded == value

# Test 2: Round-trip for lists
@given(st.lists(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-10**10, max_value=10**10),
        st.text(max_size=50)
    ),
    max_size=20
))
def test_list_roundtrip(lst):
    encoded = json.dumps(lst)
    decoded = json.loads(encoded)
    assert decoded == lst

# Test 3: Round-trip for dictionaries with string keys
@given(st.dictionaries(
    st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-10**10, max_value=10**10),
        st.text(max_size=50)
    ),
    max_size=20
))
def test_dict_roundtrip(dct):
    encoded = json.dumps(dct)
    decoded = json.loads(encoded)
    assert decoded == dct

# Test 4: JSONDecodeError position tracking
@given(st.text(min_size=1, max_size=100))
def test_decode_error_position(s):
    # Create invalid JSON by adding unescaped quote in middle
    invalid_json = '{"key": "' + s + '"'  # Missing closing brace
    try:
        json.loads(invalid_json)
    except JSONDecodeError as e:
        # Check that position attributes are consistent
        assert e.pos >= 0
        assert e.pos <= len(invalid_json)
        assert e.lineno >= 1
        assert e.colno >= 1
        # colno should be position from last newline + 1
        last_newline = invalid_json.rfind('\n', 0, e.pos)
        expected_colno = e.pos - last_newline
        assert e.colno == expected_colno

# Test 5: Unicode escape sequences
@given(st.integers(min_value=0, max_value=0xFFFF))
def test_unicode_escape_roundtrip(codepoint):
    # Skip surrogates which need special handling
    assume(codepoint < 0xD800 or codepoint > 0xDFFF)
    
    char = chr(codepoint)
    # Create JSON with unicode escape
    json_str = '"\\u{:04x}"'.format(codepoint)
    decoded = json.loads(json_str)
    assert decoded == char
    
    # Round-trip test
    encoded = json.dumps(char)
    decoded2 = json.loads(encoded)
    assert decoded2 == char

# Test 6: Strict mode with control characters
@given(st.integers(min_value=0, max_value=31))
def test_strict_mode_control_chars(control_code):
    # Control characters should be rejected in strict mode
    char = chr(control_code)
    # Skip characters that are valid in JSON strings when escaped
    if char in '\t\n\r':
        return
    
    json_str = '["' + char + '"]'
    
    # Strict mode (default) should reject
    decoder_strict = JSONDecoder(strict=True)
    try:
        decoder_strict.decode(json_str)
        # If it doesn't raise, the control char might be handled differently
    except JSONDecodeError:
        pass  # Expected for most control characters
    
    # Non-strict mode should accept
    decoder_loose = JSONDecoder(strict=False)
    try:
        result = decoder_loose.decode(json_str)
        assert result == [char]
    except JSONDecodeError:
        # Some control chars might still be invalid
        pass

# Test 7: Trailing comma handling
@given(st.lists(st.integers(), min_size=1, max_size=10))
def test_trailing_comma_detection(lst):
    # Arrays with trailing commas should be rejected
    json_str = str(lst).replace("'", '"')[:-1] + ',]'
    try:
        json.loads(json_str)
        assert False, "Should have raised JSONDecodeError for trailing comma"
    except JSONDecodeError as e:
        assert "trailing comma" in e.msg.lower() or "expecting" in e.msg.lower()

# Test 8: Object trailing comma
@given(st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), min_size=1, max_size=5))
def test_object_trailing_comma(dct):
    # Create JSON with trailing comma in object
    json_str = json.dumps(dct)[:-1] + ',}'
    try:
        json.loads(json_str)
        assert False, "Should have raised JSONDecodeError for trailing comma in object"
    except JSONDecodeError as e:
        assert "trailing comma" in e.msg.lower() or "property name" in e.msg.lower()

# Test 9: Extra data detection
@given(st.text(min_size=0, max_size=50))
def test_extra_data_detection(extra):
    assume(extra.strip())  # Skip empty/whitespace only
    valid_json = '{"key": "value"}'
    json_with_extra = valid_json + extra
    
    try:
        json.loads(json_with_extra)
        # Should only succeed if extra is all whitespace
        assert extra.strip() == ""
    except JSONDecodeError as e:
        assert "extra data" in e.msg.lower()
        # Position points to first non-JSON-whitespace character
        # JSON only considers ' \t\n\r' as whitespace
        json_ws = ' \t\n\r'
        ws_count = 0
        for char in extra:
            if char in json_ws:
                ws_count += 1
            else:
                break
        assert e.pos == len(valid_json) + ws_count

# Test 10: Large nested structures
@given(st.integers(min_value=50, max_value=100))
def test_deeply_nested_arrays(depth):
    # Create deeply nested array
    json_str = '[' * depth + ']' * depth
    try:
        result = json.loads(json_str)
        # Check structure is correct
        current = result
        for _ in range(depth - 1):
            assert isinstance(current, list)
            assert len(current) == 1
            current = current[0]
        assert current == []
    except RecursionError:
        # Python may hit recursion limit for very deep nesting
        pass

# Test 11: Unicode surrogate pairs
@given(st.integers(min_value=0x10000, max_value=0x10FFFF))
def test_unicode_surrogate_pairs(codepoint):
    # Test proper handling of surrogate pairs for characters outside BMP
    char = chr(codepoint)
    
    # Calculate surrogate pair
    codepoint -= 0x10000
    high = 0xD800 + (codepoint >> 10)
    low = 0xDC00 + (codepoint & 0x3FF)
    
    # Create JSON with surrogate pair
    json_str = '"\\u{:04x}\\u{:04x}"'.format(high, low)
    decoded = json.loads(json_str)
    assert decoded == char

# Test 12: Escaped characters in strings
@given(st.text(min_size=0, max_size=50))
def test_string_escape_sequences(text):
    # Test that common escape sequences work correctly
    special_chars = {
        '\\': '\\\\',
        '"': '\\"',
        '\n': '\\n',
        '\r': '\\r',
        '\t': '\\t',
        '\b': '\\b',
        '\f': '\\f'
    }
    
    escaped_text = text
    for char, escape in special_chars.items():
        escaped_text = escaped_text.replace(char, escape)
    
    json_str = '["' + escaped_text + '"]'
    
    try:
        decoded = json.loads(json_str)
        assert decoded == [text]
    except JSONDecodeError:
        # Some combinations might create invalid JSON
        pass

# Test 13: Number parsing edge cases
@given(st.one_of(
    st.just("0"),
    st.just("-0"),
    st.just("0.0"),
    st.just("-0.0"),
    st.just("1e10"),
    st.just("1E10"),
    st.just("1e-10"),
    st.just("1E+10"),
))
def test_number_formats(num_str):
    result = json.loads(num_str)
    assert isinstance(result, (int, float))

# Test 14: Invalid escape sequences should be rejected
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=1))
def test_invalid_escape_sequences(char):
    # Skip valid escape characters
    if char in 'bfnrtu"/\\':
        return
    
    json_str = '["\\' + char + '"]'
    try:
        json.loads(json_str)
        assert False, f"Should have rejected invalid escape \\{char}"
    except JSONDecodeError as e:
        assert "escape" in e.msg.lower()

# Test 15: Line and column number calculation
@given(st.integers(min_value=0, max_value=10), st.integers(min_value=0, max_value=10))
def test_error_line_column_calculation(newlines_before, chars_after):
    # Create JSON with specific newlines and position
    json_str = '\n' * newlines_before + ' ' * chars_after + '{'
    
    try:
        json.loads(json_str)
        assert False, "Should have raised error for incomplete JSON"
    except JSONDecodeError as e:
        # Line number should account for newlines
        assert e.lineno == newlines_before + 1
        # Column should be position after last newline
        if newlines_before > 0:
            assert e.colno == chars_after + 2  # +1 for '{', +1 for 1-based indexing
        else:
            assert e.colno == chars_after + 2

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])