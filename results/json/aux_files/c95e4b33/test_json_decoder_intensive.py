import json
import math
from hypothesis import given, strategies as st, assume, settings, example
from json.decoder import JSONDecodeError, JSONDecoder, py_scanstring

# More intensive tests with edge cases

# Test for JSONDecodeError colno calculation edge case
@given(st.integers(min_value=0, max_value=1000))
@settings(max_examples=1000)
def test_decode_error_colno_edge_case(pos):
    # Create a document with newlines before the position
    doc = "x" * pos + "\n" + "y" * 10
    
    # Test different positions in the document
    for test_pos in [0, pos // 2, pos, pos + 1, pos + 5]:
        if test_pos > len(doc):
            continue
            
        try:
            raise JSONDecodeError("Test error", doc, test_pos)
        except JSONDecodeError as e:
            # Calculate expected column
            last_newline = doc.rfind('\n', 0, test_pos)
            expected_colno = test_pos - last_newline
            
            # Check the calculation
            assert e.colno == expected_colno
            assert e.pos == test_pos
            
            # For positions after newline, colno should be small
            if test_pos > pos:
                assert e.colno <= 11  # Max 10 'y's plus 1

# Test surrogate pair edge cases
@given(st.integers(min_value=0xD800, max_value=0xDFFF))
def test_invalid_lone_surrogates(surrogate):
    # Lone surrogates should not round-trip properly
    json_str = '"\\u{:04x}"'.format(surrogate)
    try:
        result = json.loads(json_str)
        # Python allows decoding lone surrogates
        assert ord(result) == surrogate
    except:
        pass  # Some versions might reject

# Test for position tracking with nested structures
@given(st.integers(min_value=1, max_value=10))
def test_nested_error_position(depth):
    # Create incomplete nested structure
    json_str = '[' * depth + '{'
    
    try:
        json.loads(json_str)
        assert False, "Should have raised error"
    except JSONDecodeError as e:
        # Error position is at the end of string (expecting more)
        assert e.pos == len(json_str)
        assert e.colno == len(json_str) + 1  # Column is 1-based

# Test py_scanstring directly with edge cases
@given(st.text(min_size=0, max_size=100))
@settings(max_examples=500)
def test_py_scanstring_direct(text):
    # Create a JSON string and try to scan it
    escaped = json.dumps(text)
    # Remove quotes to get the escaped content
    escaped_content = escaped[1:-1]
    
    # Add quotes back and try scanning from position 1
    full_string = '"' + escaped_content + '"'
    
    try:
        result, end_pos = py_scanstring(full_string, 1)
        assert result == text
        assert end_pos == len(full_string)
    except JSONDecodeError:
        # Some edge cases might fail
        pass

# Test whitespace handling edge cases
@given(st.text(alphabet=' \t\n\r\xa0\u2000\u3000', min_size=0, max_size=20))
def test_mixed_whitespace(ws):
    # Mix JSON whitespace with non-JSON whitespace
    json_str = '{}' + ws + '[]'
    
    try:
        result = json.loads(json_str)
        # Should fail due to extra data
        assert False, "Should have raised JSONDecodeError"
    except JSONDecodeError as e:
        assert "extra data" in e.msg.lower()
        # Check position points to first non-JSON-whitespace after {}
        json_ws = ' \t\n\r'
        expected_pos = 2  # After '{}'
        for char in ws:
            if char in json_ws:
                expected_pos += 1
            else:
                break
        assert e.pos == expected_pos

# Test number parsing edge cases
@given(st.text(alphabet='0123456789+-eE.', min_size=1, max_size=20))
def test_malformed_numbers(num_str):
    # Skip if it's actually valid JSON
    try:
        json.loads(num_str)
        return  # It's valid, skip
    except:
        pass
    
    # Check that error position is reasonable
    try:
        json.loads(num_str)
    except JSONDecodeError as e:
        assert 0 <= e.pos <= len(num_str)
        assert e.lineno == 1
        assert e.colno == e.pos + 1

# Test deeply nested dictionary/list combinations
@given(st.integers(min_value=1, max_value=50))
def test_mixed_nesting(depth):
    # Create alternating dict/list nesting
    json_str = ""
    for i in range(depth):
        if i % 2 == 0:
            json_str += '{"key":'
        else:
            json_str += '['
    
    json_str += '42'
    
    for i in range(depth - 1, -1, -1):
        if i % 2 == 0:
            json_str += '}'
        else:
            json_str += ']'
    
    try:
        result = json.loads(json_str)
        # Verify structure
        current = result
        for i in range(depth):
            if i % 2 == 0:
                assert isinstance(current, dict)
                current = current['key']
            else:
                assert isinstance(current, list)
                assert len(current) == 1
                current = current[0]
        assert current == 42
    except RecursionError:
        pass

# Test special float values
def test_special_floats():
    # Test NaN, Infinity, -Infinity
    decoder = JSONDecoder()
    
    assert math.isnan(decoder.decode('NaN'))
    assert decoder.decode('Infinity') == float('inf')
    assert decoder.decode('-Infinity') == float('-inf')
    
    # These should work in arrays too
    result = decoder.decode('[NaN, Infinity, -Infinity]')
    assert math.isnan(result[0])
    assert result[1] == float('inf')
    assert result[2] == float('-inf')

# Test object_pairs_hook
@given(st.lists(st.tuples(st.text(min_size=1, max_size=10), st.integers()), min_size=0, max_size=10))
def test_object_pairs_hook(pairs):
    # Convert pairs to dict for JSON
    data = dict(pairs)
    json_str = json.dumps(data)
    
    # Track what the hook sees
    seen_pairs = []
    
    def hook(pairs_list):
        seen_pairs.append(pairs_list)
        return dict(pairs_list)
    
    decoder = JSONDecoder(object_pairs_hook=hook)
    result = decoder.decode(json_str)
    
    # Hook should have been called
    if data:
        assert len(seen_pairs) == 1
        # Check order is preserved (though dict doesn't guarantee order in older Python)
        assert dict(seen_pairs[0]) == data

# Test parse_float and parse_int hooks
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_parse_float_hook(value):
    json_str = json.dumps(value)
    
    # Custom parser that adds 1
    def custom_float(s):
        return float(s) + 1
    
    decoder = JSONDecoder(parse_float=custom_float)
    result = decoder.decode(json_str)
    
    assert math.isclose(result, value + 1, rel_tol=1e-10)

@given(st.integers(min_value=-10**10, max_value=10**10))
def test_parse_int_hook(value):
    json_str = json.dumps(value)
    
    # Custom parser that doubles
    def custom_int(s):
        return int(s) * 2
    
    decoder = JSONDecoder(parse_int=custom_int)
    result = decoder.decode(json_str)
    
    assert result == value * 2

# Test memo functionality in JSONObject
def test_json_object_memo():
    # The memo is used to intern strings
    json_str = '{"key1": 1, "key1": 2, "key1": 3}'
    
    # This is technically invalid JSON (duplicate keys) but Python allows it
    result = json.loads(json_str)
    assert result == {"key1": 3}  # Last value wins

# Test raw_decode with extra data
@given(st.text(min_size=0, max_size=50))
def test_raw_decode_extra_data(extra):
    decoder = JSONDecoder()
    json_str = '{"test": 123}' + extra
    
    obj, end = decoder.raw_decode(json_str)
    assert obj == {"test": 123}
    assert end == 13  # Position after the '}'
    
    # The extra data is not consumed
    remaining = json_str[end:]
    assert remaining == extra

# Test BOM handling (from main module)
def test_bom_rejection():
    # UTF-8 BOM should be rejected by json.loads for strings
    bom_string = '\ufeff{"test": 123}'
    
    try:
        json.loads(bom_string)
        assert False, "Should reject BOM"
    except JSONDecodeError as e:
        assert "UTF-8 BOM" in e.msg

# Test bytes input with different encodings
def test_bytes_input():
    # json.loads should handle bytes
    data = {"test": "value"}
    json_bytes = json.dumps(data).encode('utf-8')
    
    result = json.loads(json_bytes)
    assert result == data
    
    # Test UTF-16
    json_bytes_16 = json.dumps(data).encode('utf-16')
    result16 = json.loads(json_bytes_16)
    assert result16 == data

# Edge case: Empty string at specific position
def test_empty_string_edge_case():
    # This specific case tests boundary conditions
    json_str = '[""]'
    result = json.loads(json_str)
    assert result == [""]
    
    json_str2 = '{"": ""}'
    result2 = json.loads(json_str2)
    assert result2 == {"": ""}

# Test control character in key
def test_control_char_in_key():
    # Control characters in keys should be rejected in strict mode
    json_str = '{"\x00": "value"}'
    
    decoder_strict = JSONDecoder(strict=True)
    try:
        decoder_strict.decode(json_str)
        assert False, "Should reject control char in strict mode"
    except JSONDecodeError:
        pass
    
    decoder_loose = JSONDecoder(strict=False)
    result = decoder_loose.decode(json_str)
    assert result == {"\x00": "value"}

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])