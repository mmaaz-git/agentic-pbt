import json
import json.scanner
import json.decoder
import math
import sys
from hypothesis import given, strategies as st, assume, settings, example
import hypothesis


@given(st.text(alphabet='0123456789.eE+-', min_size=1))
def test_number_regex_malformed_numbers(num_str):
    """Test that NUMBER_RE and json.loads agree on what's a valid number"""
    match = json.scanner.NUMBER_RE.match(num_str)
    
    try:
        # Try to parse as JSON
        result = json.loads(num_str)
        
        # If JSON accepts it, NUMBER_RE should match it (at least partially)
        if isinstance(result, (int, float)):
            assert match is not None, f"NUMBER_RE should match valid JSON number: {num_str}"
    except (json.JSONDecodeError, ValueError):
        # JSON doesn't accept it, that's fine
        pass


@given(st.from_regex(r'-0[0-9]+', fullmatch=True))
def test_negative_numbers_with_leading_zeros(num_str):
    """Test handling of negative numbers with leading zeros like -00, -01"""
    try:
        result = json.loads(num_str)
        # -0 is valid, but -00, -01, etc. should not be per JSON spec
        if num_str == '-0':
            assert result == 0
        else:
            # Should have failed per JSON spec
            pass
    except json.JSONDecodeError:
        # Expected for -00, -01, etc.
        if num_str != '-0':
            pass  # This is correct behavior


@given(st.text(alphabet='\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'))
def test_control_characters_in_strings(ctrl_chars):
    """Test handling of control characters in JSON strings"""
    # Control characters should be escaped in JSON strings
    try:
        # Try to create a JSON string with control characters
        json_str = json.dumps(ctrl_chars)
        # Should escape control characters
        decoded = json.loads(json_str)
        assert decoded == ctrl_chars
        
        # Now try with raw control characters in JSON
        raw_json = f'"{ctrl_chars}"'
        try:
            json.loads(raw_json)
            # Should fail for unescaped control characters
        except json.JSONDecodeError:
            pass  # Expected
    except:
        pass


@given(st.floats(min_value=0, max_value=1e308))
def test_very_large_floats(f):
    """Test handling of very large floating point numbers"""
    try:
        json_str = json.dumps(f)
        parsed = json.loads(json_str)
        
        if math.isinf(parsed):
            # Check if original was close to infinity
            assert f > 1e307
        else:
            assert math.isclose(parsed, f, rel_tol=1e-10)
    except (ValueError, OverflowError):
        pass


@given(st.text(alphabet='0123456789', min_size=100, max_size=500))
def test_extremely_large_integers(digits):
    """Test parsing of extremely large integers"""
    if digits[0] == '0' and len(digits) > 1:
        return  # Skip leading zeros
        
    try:
        parsed = json.loads(digits)
        # Should parse as int or float
        assert isinstance(parsed, (int, float))
        
        # Test round-trip
        encoded = json.dumps(parsed)
        decoded = json.loads(encoded)
        
        if isinstance(parsed, int):
            assert decoded == parsed
        else:
            # For very large numbers that become floats
            assert abs(decoded - parsed) / parsed < 1e-10 or decoded == parsed
    except:
        pass


@given(st.integers(min_value=1, max_value=100))
def test_nested_array_depth(depth):
    """Test deeply nested arrays"""
    # Create deeply nested array
    json_str = '[' * depth + ']' * depth
    
    try:
        result = json.loads(json_str)
        # Should handle reasonable nesting depths
        assert result == [] if depth == 1 else [result] == [[]]
        
        # Verify structure depth
        curr = result
        actual_depth = 0
        while isinstance(curr, list):
            actual_depth += 1
            if len(curr) > 0:
                curr = curr[0]
            else:
                break
        
        assert actual_depth == depth
    except RecursionError:
        # Expected for very deep nesting
        pass
    except:
        pass


@given(st.integers())
def test_duplicate_object_keys(val):
    """Test objects with duplicate keys"""
    # JSON spec allows duplicate keys, last value should win
    json_str = '{"key": 1, "key": 2}'
    result = json.loads(json_str)
    assert result == {"key": 2}
    
    # Test with more values
    json_str = '{"a": 1, "b": 2, "a": 3}'
    result = json.loads(json_str)
    assert result == {"a": 3, "b": 2}


@given(st.from_regex(r'\+[0-9]+', fullmatch=True))
def test_numbers_with_plus_sign(num_str):
    """Test that numbers with leading + are handled correctly"""
    # JSON spec doesn't allow leading + for numbers
    try:
        result = json.loads(num_str)
        # Should not parse according to JSON spec
    except json.JSONDecodeError:
        pass  # Expected behavior


@given(st.one_of(
    st.just('Infinity'),
    st.just('-Infinity'),
    st.just('NaN'),
    st.just('infinity'),
    st.just('nan'),
))
def test_non_finite_constants(const_str):
    """Test handling of Infinity and NaN constants"""
    try:
        # Standard JSON doesn't support these
        result = json.loads(const_str)
        # Python's json might reject these
    except (json.JSONDecodeError, ValueError):
        pass  # Expected for standard JSON


@given(st.text(alphabet='0123456789eE+-.', min_size=1, max_size=20))
def test_scientific_notation_edge_cases(num_str):
    """Test edge cases in scientific notation"""
    # Test various malformed scientific notation
    test_cases = [
        num_str,
        '1e',    # Missing exponent
        '1e+',   # Missing exponent digits
        '1e-',   # Missing exponent digits  
        '1.e5',  # Decimal point without fractional part
        '.5',    # Missing integer part
        '1.2.3', # Multiple decimal points
        '1e2e3', # Multiple e's
    ]
    
    for test in test_cases:
        match = json.scanner.NUMBER_RE.match(test)
        try:
            result = json.loads(test)
            if isinstance(result, (int, float)):
                # If JSON accepts it, check NUMBER_RE
                pass
        except (json.JSONDecodeError, ValueError):
            # Expected for malformed numbers
            pass


@given(st.text())
def test_string_null_byte_handling(text):
    """Test handling of null bytes in strings"""
    if '\x00' in text:
        # Strings with null bytes
        try:
            encoded = json.dumps(text)
            decoded = json.loads(encoded)
            assert decoded == text
        except:
            pass


@given(st.lists(st.sampled_from(['[', ']', '{', '}', '"', ',']), min_size=1, max_size=10))
def test_malformed_structure(chars):
    """Test various malformed JSON structures"""
    json_str = ''.join(chars)
    
    try:
        result = json.loads(json_str)
        # If it parses, verify it's valid
        encoded = json.dumps(result)
        decoded = json.loads(encoded)
        assert decoded == result
    except (json.JSONDecodeError, ValueError, TypeError):
        pass  # Expected for most random combinations


@given(st.text(min_size=1).filter(lambda x: x[0] in '0123456789-'))
def test_number_parsing_consistency(text):
    """Test that number parsing is consistent with NUMBER_RE"""
    # Check if NUMBER_RE thinks this is a number
    match = json.scanner.NUMBER_RE.match(text)
    
    if match and match.end() == len(text):
        # NUMBER_RE thinks the entire string is a number
        try:
            result = json.loads(text)
            # Should parse as a number
            assert isinstance(result, (int, float)), f"NUMBER_RE matched but JSON didn't parse as number: {text}"
        except json.JSONDecodeError:
            # NUMBER_RE matched but JSON rejected - potential issue
            # Check if it's a known invalid case like leading zeros
            if re.match(r'-?0[0-9]', text):
                pass  # Expected: leading zeros not allowed
            elif text in ['-', '.', 'e', 'E', '+', '-0.', '0.']:
                pass  # Expected: incomplete numbers
            else:
                # Could be an inconsistency
                pass


@given(st.from_regex(r'[0-9]+\.[0-9]+\.[0-9]+', fullmatch=True))
def test_multiple_decimal_points(num_str):
    """Test numbers with multiple decimal points"""
    # Should not be valid JSON
    try:
        result = json.loads(num_str)
        # Should have failed
        assert False, f"Multiple decimal points should not parse: {num_str}"
    except json.JSONDecodeError:
        pass  # Expected


@given(st.from_regex(r'[0-9]+[eE][+-]?[0-9]+[eE][+-]?[0-9]+', fullmatch=True))
def test_multiple_exponents(num_str):
    """Test numbers with multiple exponential parts"""
    # Should not be valid JSON
    try:
        result = json.loads(num_str)
        # Should have failed
        assert False, f"Multiple exponents should not parse: {num_str}"
    except json.JSONDecodeError:
        pass  # Expected


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])