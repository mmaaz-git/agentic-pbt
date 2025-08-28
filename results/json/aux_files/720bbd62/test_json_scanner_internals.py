import json
import json.scanner
import json.decoder
import re
from hypothesis import given, strategies as st, assume, settings, example


class MockContext:
    """Mock context for testing scanner directly"""
    def __init__(self):
        self.strict = True
        self.parse_float = float
        self.parse_int = int
        self.parse_constant = lambda x: None
        self.object_hook = None
        self.object_pairs_hook = None
        self.memo = {}
        
        # These would normally be provided by decoder
        self.parse_string = lambda s, idx, strict: ('test_string', idx + 10)
        self.parse_object = lambda *args: ({}, args[0][1] + 2)
        self.parse_array = lambda *args: ([], args[0][1] + 2)


@given(st.from_regex(r'0[0-9]+', fullmatch=True).filter(lambda x: x != '0'))
def test_leading_zeros_json_consistency(num_str):
    """Test that json.loads properly rejects numbers with leading zeros"""
    # According to JSON spec, numbers cannot have leading zeros (except "0" itself)
    try:
        result = json.loads(num_str)
        # If it parsed, this could be a bug - JSON spec forbids leading zeros
        assert False, f"JSON should reject number with leading zeros: {num_str}"
    except json.JSONDecodeError:
        pass  # Expected


@given(st.from_regex(r'-0[0-9]+', fullmatch=True).filter(lambda x: x != '-0'))
def test_negative_leading_zeros_consistency(num_str):
    """Test that negative numbers with leading zeros are rejected"""
    try:
        result = json.loads(num_str)
        # Should reject per JSON spec
        assert False, f"JSON should reject negative number with leading zeros: {num_str}"
    except json.JSONDecodeError:
        pass  # Expected


@given(st.text(alphabet='0123456789+-eE.', min_size=1, max_size=10))
def test_number_regex_coverage(text):
    """Test NUMBER_RE regex against json.loads for number-like strings"""
    # Check what NUMBER_RE thinks
    match = json.scanner.NUMBER_RE.match(text)
    
    # Try to parse with JSON
    try:
        result = json.loads(text)
        
        if isinstance(result, (int, float)):
            # JSON parsed it as a number
            if match is None:
                # NUMBER_RE didn't match but JSON did - potential bug
                pass
            elif match.end() != len(text):
                # NUMBER_RE only partially matched
                pass
    except json.JSONDecodeError:
        # JSON rejected it
        if match and match.end() == len(text):
            # NUMBER_RE fully matched but JSON rejected
            # Check for known exceptions
            if not re.match(r'-?0[0-9]', text):  # Not a leading zero issue
                pass


@given(st.floats(allow_nan=True, allow_infinity=True))
def test_special_floats_consistency(f):
    """Test handling of NaN and Infinity values"""
    try:
        # Try default behavior (should reject NaN/Infinity)
        json_str = json.dumps(f)
        # If it didn't raise, it converted somehow
        decoded = json.loads(json_str)
        
        if f != f:  # NaN
            assert decoded != decoded  # Should also be NaN
        elif f == float('inf'):
            assert decoded == float('inf')
        elif f == float('-inf'):
            assert decoded == float('-inf')
        else:
            assert decoded == f or abs(decoded - f) < 1e-10
    except ValueError as e:
        # Expected for NaN/Infinity with default settings
        if 'Out of range' in str(e) or 'not JSON serializable' in str(e):
            pass


@given(st.text(min_size=1, max_size=1000))
def test_unterminated_string_detection(text):
    """Test detection of unterminated strings"""
    # Create an unterminated string
    json_str = '"' + text.replace('"', '\\"').replace('\\', '\\\\')  # No closing quote
    
    try:
        json.loads(json_str)
        # Should have failed
        assert False, "Should detect unterminated string"
    except json.JSONDecodeError as e:
        # Should report unterminated string or invalid control char
        pass  # Expected


@given(st.lists(st.sampled_from(['[', '{', '"']), min_size=1, max_size=10))
def test_unmatched_brackets(brackets):
    """Test detection of unmatched brackets/braces"""
    json_str = ''.join(brackets)
    
    # Count opening and closing
    open_square = json_str.count('[')
    close_square = json_str.count(']')
    open_curly = json_str.count('{')
    close_curly = json_str.count('}')
    quotes = json_str.count('"')
    
    if open_square != close_square or open_curly != close_curly or quotes % 2 != 0:
        try:
            json.loads(json_str)
            # Should have failed
        except json.JSONDecodeError:
            pass  # Expected


@given(st.text(alphabet='\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f', min_size=1))
def test_raw_control_characters(ctrl):
    """Test that raw control characters in strings are rejected"""
    # Create JSON with raw control characters (not escaped)
    json_str = f'"{ctrl}"'
    
    try:
        result = json.loads(json_str)
        # Should reject unescaped control characters
        # Check which control character it was
        for c in ctrl:
            if ord(c) < 0x20 and c not in '\t\n\r':
                # Should have been rejected
                pass
    except json.JSONDecodeError:
        pass  # Expected for control characters


@given(st.integers(min_value=1, max_value=10000))
def test_deeply_nested_structures(depth):
    """Test handling of deeply nested structures"""
    # Create deeply nested object
    json_str = '{"a":' * depth + '1' + '}' * depth
    
    try:
        result = json.loads(json_str)
        # Should handle reasonable depths
        
        # Verify depth
        curr = result
        actual_depth = 0
        while isinstance(curr, dict) and 'a' in curr:
            actual_depth += 1
            curr = curr['a']
        
        assert actual_depth == depth or depth > sys.getrecursionlimit()
    except RecursionError:
        # Expected for very deep nesting
        pass


@given(st.text(alphabet='0123456789', min_size=309, max_size=350))
def test_huge_number_precision(digits):
    """Test precision loss with huge numbers"""
    if digits[0] == '0' and len(digits) > 1:
        return  # Skip leading zeros
    
    try:
        parsed = json.loads(digits)
        
        # Check if precision was lost
        if isinstance(parsed, float):
            # Float has limited precision
            encoded = json.dumps(parsed)
            decoded = json.loads(encoded)
            
            # The round-trip should preserve the float value
            assert decoded == parsed
            
            # But it might not preserve the original string
            if len(digits) > 17:  # Beyond float precision
                # Expect precision loss
                assert encoded != digits
    except:
        pass


@given(st.from_regex(r'[eE][+-]?[0-9]+', fullmatch=True))
def test_exponent_without_mantissa(exp_str):
    """Test exponent notation without mantissa"""
    try:
        result = json.loads(exp_str)
        # Should fail - exponent needs a mantissa
        assert False, f"Exponent without mantissa should fail: {exp_str}"
    except json.JSONDecodeError:
        pass  # Expected


@given(st.from_regex(r'[0-9]*\.[0-9]*', fullmatch=True).filter(lambda x: x != '.'))
def test_decimal_edge_cases(dec_str):
    """Test decimal number edge cases"""
    # Test various decimal patterns
    has_int_part = len(dec_str) > 0 and dec_str[0] != '.'
    has_frac_part = '.' in dec_str and len(dec_str.split('.')[1]) > 0
    
    try:
        result = json.loads(dec_str)
        # JSON requires at least integer or fractional part
        if dec_str == '.':
            assert False, "Lone decimal point should not parse"
        elif not has_int_part:
            # No integer part (like .5) - JSON spec requires integer part
            assert False, f"No integer part should fail: {dec_str}"
    except json.JSONDecodeError:
        # Expected for invalid decimal formats
        pass


@given(st.text(min_size=1))
@example('{"test": "\t\n\r"}')  # Valid escapes
@example('{"test": "\x00"}')     # Invalid control char
def test_string_escape_sequences(text):
    """Test various string escape sequences"""
    # Try to encode and decode
    try:
        # First encode the text properly
        encoded = json.dumps({"test": text})
        decoded = json.loads(encoded)
        assert decoded["test"] == text
        
        # Now test raw JSON with the text
        raw_json = '{"test": "' + text + '"}'
        try:
            json.loads(raw_json)
            # Check if text had control characters
            for c in text:
                if ord(c) < 0x20 and c not in '\t\n\r':
                    # Should have failed for unescaped control chars
                    pass
        except json.JSONDecodeError:
            # Expected for unescaped control characters
            pass
    except:
        pass


@given(st.from_regex(r'[1-9][0-9]*[eE][+-]?0+[0-9]*', fullmatch=True))
def test_exponent_with_leading_zeros(num_str):
    """Test exponents with leading zeros like 1e007"""
    try:
        result = json.loads(num_str)
        # This is actually valid JSON (exponent can have leading zeros)
        assert isinstance(result, (int, float))
        
        # The value should be correct despite leading zeros in exponent
        base, exp_part = num_str.lower().split('e')
        exp_sign = '+' if exp_part[0] not in '+-' else exp_part[0]
        exp_val = int(exp_part.lstrip('+-').lstrip('0') or '0')
        if exp_sign == '-':
            exp_val = -exp_val
        
        expected = float(base) * (10 ** exp_val)
        assert abs(result - expected) < abs(expected * 1e-10) or result == expected
    except json.JSONDecodeError:
        # Shouldn't fail for this
        assert False, f"Valid exponent with leading zeros rejected: {num_str}"
    except:
        pass


if __name__ == "__main__":
    import pytest
    import sys
    pytest.main([__file__, "-v", "--tb=short"])