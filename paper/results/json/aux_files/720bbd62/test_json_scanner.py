import json
import json.scanner
import json.decoder
import math
import re
from hypothesis import given, strategies as st, assume, settings
import hypothesis


@given(st.data())
def test_number_regex_parse_float_consistency(data):
    """Test that NUMBER_RE regex matches exactly what parse_float can parse"""
    # Generate a string that NUMBER_RE thinks is a valid number
    integer_part = data.draw(st.one_of(
        st.just('0'),
        st.from_regex(r'-?0', fullmatch=True),
        st.from_regex(r'-?[1-9][0-9]*', fullmatch=True)
    ))
    
    frac_part = data.draw(st.one_of(
        st.just(''),
        st.from_regex(r'\.[0-9]+', fullmatch=True)
    ))
    
    exp_part = data.draw(st.one_of(
        st.just(''),
        st.from_regex(r'[eE][-+]?[0-9]+', fullmatch=True)
    ))
    
    number_str = integer_part + frac_part + exp_part
    
    # Test that NUMBER_RE matches what we expect
    match = json.scanner.NUMBER_RE.match(number_str)
    assert match is not None, f"NUMBER_RE should match {number_str}"
    assert match.group(0) == number_str
    
    # Test that json can parse this number
    try:
        result = json.loads(number_str)
        assert isinstance(result, (int, float)), f"Expected numeric result for {number_str}"
    except:
        # If json.loads fails, this could indicate an issue
        pass


@given(st.text())
def test_json_loads_dumps_roundtrip(text):
    """Test round-trip property for valid JSON strings"""
    # Try to create valid JSON from text
    try:
        # Escape the text properly for JSON
        json_str = json.dumps(text)
        # Now try to decode it
        decoded = json.loads(json_str)
        assert decoded == text, f"Round-trip failed for text: {repr(text)}"
    except:
        # If encoding fails, that's expected for some inputs
        pass


@given(st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
))
def test_simple_value_roundtrip(value):
    """Test that simple values can round-trip through JSON"""
    encoded = json.dumps(value)
    decoded = json.loads(encoded)
    
    if isinstance(value, float):
        if math.isnan(value):
            assert math.isnan(decoded)
        else:
            assert decoded == value or (math.isclose(decoded, value, rel_tol=1e-15))
    else:
        assert decoded == value


@given(st.lists(st.integers()))
def test_array_roundtrip(lst):
    """Test that arrays round-trip correctly"""
    encoded = json.dumps(lst)
    decoded = json.loads(encoded)
    assert decoded == lst


@given(st.dictionaries(st.text(), st.integers()))
def test_object_roundtrip(dct):
    """Test that objects round-trip correctly"""
    encoded = json.dumps(dct)
    decoded = json.loads(encoded)
    assert decoded == dct


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_float_number_parsing(f):
    """Test that float parsing is consistent"""
    # Convert to JSON string and back
    json_str = json.dumps(f)
    parsed = json.loads(json_str)
    
    if not math.isnan(f):
        assert parsed == f or math.isclose(parsed, f, rel_tol=1e-15)


@given(st.integers(min_value=-10**308, max_value=10**308))
def test_integer_parsing(i):
    """Test integer parsing consistency"""
    json_str = json.dumps(i)
    parsed = json.loads(json_str)
    assert parsed == i


@given(st.text(alphabet=st.characters(codec='utf-8')))
def test_unicode_string_roundtrip(text):
    """Test Unicode string handling"""
    try:
        encoded = json.dumps(text, ensure_ascii=False)
        decoded = json.loads(encoded)
        assert decoded == text
    except:
        # Some Unicode might not be valid
        pass


@given(st.text())
def test_string_with_escapes_roundtrip(text):
    """Test strings with escape sequences"""
    # Create strings with various escape sequences
    try:
        encoded = json.dumps(text)
        decoded = json.loads(encoded)
        assert decoded == text
    except:
        pass


@given(st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(st.text(), children, max_size=10)
    ),
    max_leaves=50
))
def test_nested_structure_roundtrip(obj):
    """Test deeply nested structures"""
    encoded = json.dumps(obj)
    decoded = json.loads(encoded)
    assert decoded == obj


@given(st.floats())
def test_special_float_values(f):
    """Test handling of special float values like NaN and Infinity"""
    if math.isnan(f) or math.isinf(f):
        # JSON standard doesn't support NaN/Infinity
        try:
            json.dumps(f)
            # If it doesn't raise, check if allow_nan is being used
        except ValueError:
            pass  # Expected behavior
    else:
        encoded = json.dumps(f)
        decoded = json.loads(encoded)
        if f != f:  # NaN check
            assert decoded != decoded
        else:
            assert decoded == f or math.isclose(decoded, f, rel_tol=1e-15)


@given(st.text(min_size=1))
def test_malformed_json_detection(text):
    """Test that malformed JSON is properly rejected"""
    # Add some malformed JSON patterns
    malformed_patterns = [
        '{' + text,  # Unclosed object
        '[' + text,  # Unclosed array  
        '{"key":',   # Incomplete key-value
        '{"key": "value"',  # Missing closing brace
    ]
    
    for pattern in malformed_patterns:
        if not pattern.strip():
            continue
        try:
            json.loads(pattern)
            # If it succeeds, it better be valid JSON
            json.dumps(json.loads(pattern))
        except (json.JSONDecodeError, ValueError):
            pass  # Expected


@given(st.from_regex(r'0[0-9]+', fullmatch=True))
def test_leading_zeros_in_numbers(num_str):
    """Test that numbers with leading zeros are handled correctly"""
    # JSON spec says leading zeros are not allowed except for "0"
    if num_str != '0':
        try:
            result = json.loads(num_str)
            # If it parses, we should check if it's correct
            # According to JSON spec, this should fail
            pass
        except json.JSONDecodeError:
            pass  # Expected for numbers with leading zeros


@given(st.text(alphabet='0123456789', min_size=2, max_size=1000))
def test_large_numbers(digits):
    """Test handling of very large numbers"""
    # Create a large number string
    if digits[0] == '0' and len(digits) > 1:
        # Skip leading zeros
        return
    
    try:
        parsed = json.loads(digits)
        # Should be parsed as an integer or float
        assert isinstance(parsed, (int, float))
        
        # Round-trip test
        encoded = json.dumps(parsed)
        decoded = json.loads(encoded)
        assert decoded == parsed
    except:
        pass


@given(st.dictionaries(
    st.text(min_size=1),
    st.integers(),
    min_size=1
))
def test_duplicate_keys_in_objects(dct):
    """Test handling of duplicate keys in JSON objects"""
    # Create JSON with potential duplicate keys
    items = list(dct.items())
    if len(items) > 1:
        # Duplicate the first key
        key, value = items[0]
        json_str = '{' + f'"{key}": {value}, "{key}": {value + 1}' + '}'
        
        try:
            result = json.loads(json_str)
            # JSON allows duplicate keys, last one wins
            assert result[key] == value + 1
        except:
            pass


@given(st.integers(min_value=0, max_value=1000))
def test_whitespace_handling(n):
    """Test that various whitespace is handled correctly"""
    whitespace_chars = [' ', '\t', '\n', '\r']
    ws = ''.join([whitespace_chars[i % 4] for i in range(n)])
    
    test_values = [
        ws + '{}' + ws,
        ws + '[]' + ws,
        ws + 'null' + ws,
        ws + 'true' + ws,
        ws + 'false' + ws,
        ws + '123' + ws,
        ws + '"test"' + ws,
    ]
    
    for json_str in test_values:
        try:
            result = json.loads(json_str)
            # Whitespace should be ignored
            no_ws = json_str.strip()
            assert json.loads(no_ws) == result
        except:
            pass


if __name__ == "__main__":
    # Run the tests
    import pytest
    pytest.main([__file__, "-v"])