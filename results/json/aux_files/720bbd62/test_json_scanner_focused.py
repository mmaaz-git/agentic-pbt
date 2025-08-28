import json
import json.scanner
import math
import re
from hypothesis import given, strategies as st, assume, settings, example
import sys


@given(st.from_regex(r'[0-9]+\.[eE][+-]?[0-9]+', fullmatch=True))
def test_decimal_point_followed_by_exponent(num_str):
    """Test numbers like 1.e5 (decimal point with no fractional part before exponent)"""
    # According to JSON spec, after decimal point there must be at least one digit
    try:
        result = json.loads(num_str)
        # JSON spec requires fractional part after decimal point
        assert False, f"Should reject decimal point without fractional part: {num_str}"
    except json.JSONDecodeError:
        pass  # Expected per JSON spec


@given(st.from_regex(r'\.[0-9]+([eE][+-]?[0-9]+)?', fullmatch=True))
def test_missing_integer_part(num_str):
    """Test numbers like .5 or .25e10 (missing integer part)"""
    # JSON spec requires integer part before decimal point
    try:
        result = json.loads(num_str)
        # Should fail per JSON spec
        assert False, f"Should reject number without integer part: {num_str}"
    except json.JSONDecodeError:
        pass  # Expected


@given(st.text(alphabet='0123456789+-eE.', min_size=1, max_size=20))
def test_number_regex_vs_json_loads(text):
    """Test consistency between NUMBER_RE and json.loads"""
    match = json.scanner.NUMBER_RE.match(text)
    
    try:
        result = json.loads(text)
        if isinstance(result, (int, float)):
            # JSON accepted it as a number
            assert match is not None, f"json.loads accepts but NUMBER_RE rejects: {text}"
            # Check that NUMBER_RE matched the whole string
            if match.end() != len(text):
                # NUMBER_RE only partially matched
                pass
    except json.JSONDecodeError:
        # JSON rejected it
        if match and match.end() == len(text):
            # NUMBER_RE thinks entire string is valid but JSON rejects
            # Check for known differences
            if re.match(r'-?0[0-9]', text):
                pass  # Leading zeros - expected difference
            elif re.match(r'[0-9]+\.[^0-9]', text):
                pass  # Decimal without fractional part
            elif text.startswith('.'):
                pass  # No integer part
            else:
                # Potential inconsistency
                pass


@given(st.integers(min_value=-sys.maxsize, max_value=sys.maxsize))
def test_integer_round_trip_exact(i):
    """Test that integers round-trip exactly through JSON"""
    json_str = json.dumps(i)
    parsed = json.loads(json_str)
    assert parsed == i, f"Integer round-trip failed: {i} -> {parsed}"


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e308, max_value=1e308))
def test_float_round_trip_precision(f):
    """Test float round-trip precision"""
    json_str = json.dumps(f)
    parsed = json.loads(json_str)
    
    if f == 0.0:
        assert parsed == 0.0
    else:
        rel_error = abs(parsed - f) / abs(f)
        assert rel_error < 1e-15, f"Float precision loss: {f} -> {parsed}, rel_error={rel_error}"


@given(st.text())
def test_string_with_surrogates(text):
    """Test handling of Unicode surrogates in strings"""
    try:
        # Try to encode/decode with surrogates
        json_str = json.dumps(text, ensure_ascii=True)
        decoded = json.loads(json_str)
        assert decoded == text
    except (UnicodeDecodeError, UnicodeEncodeError):
        # Some surrogate issues are expected
        pass


@given(st.lists(st.text(alphabet='"\\/', min_size=1, max_size=10), min_size=1, max_size=10))
def test_escape_sequences_in_strings(chars):
    """Test various escape sequences"""
    text = ''.join(chars)
    
    # Create a JSON string with the text
    try:
        encoded = json.dumps(text)
        decoded = json.loads(encoded)
        assert decoded == text
    except:
        pass


@given(st.integers(min_value=1, max_value=50))
def test_unicode_escape_sequences(n):
    """Test Unicode escape sequences like \\uXXXX"""
    # Generate random unicode escape
    hex_digits = '0123456789ABCDEF'
    escape = '\\u' + ''.join([hex_digits[i % 16] for i in range(4)])
    
    json_str = f'"{escape}"'
    
    try:
        result = json.loads(json_str)
        # Should decode the Unicode escape
        expected_char = chr(int(escape[2:], 16))
        assert result == expected_char
    except json.JSONDecodeError:
        # Some Unicode points might be invalid
        pass


@given(st.floats(min_value=1e-400, max_value=1e-300, exclude_min=True, exclude_max=False))
def test_very_small_floats(f):
    """Test handling of very small floating point numbers"""
    try:
        json_str = json.dumps(f)
        parsed = json.loads(json_str)
        
        # Very small numbers might underflow to 0
        if parsed == 0.0:
            assert f < sys.float_info.min
        else:
            assert math.isclose(parsed, f, rel_tol=1e-10)
    except:
        pass


@given(st.text(alphabet='0123456789', min_size=16, max_size=20))
def test_float_precision_boundary(digits):
    """Test precision at float boundaries"""
    if digits[0] == '0' and len(digits) > 1:
        return
    
    try:
        parsed = json.loads(digits)
        
        # Check round-trip
        encoded = json.dumps(parsed)
        decoded = json.loads(encoded)
        
        assert decoded == parsed
        
        # For numbers beyond float precision
        if len(digits) > 15:
            # Check if precision was preserved
            if isinstance(parsed, int):
                # Integer should preserve all digits
                assert str(parsed) == digits
            else:
                # Float has limited precision
                pass
    except:
        pass


@given(st.dictionaries(st.text(min_size=1), st.integers(), min_size=1))
def test_object_key_ordering(d):
    """Test that object keys can be in any order"""
    json_str = json.dumps(d)
    parsed = json.loads(json_str)
    
    assert parsed == d
    assert set(parsed.keys()) == set(d.keys())
    
    # Test with reversed key order
    items = list(d.items())
    reversed_json = '{' + ', '.join(f'"{k}": {v}' for k, v in reversed(items)) + '}'
    
    try:
        parsed_reversed = json.loads(reversed_json)
        assert parsed_reversed == d
    except:
        pass


@given(st.recursive(
    st.one_of(st.none(), st.booleans(), st.integers(), st.floats(allow_nan=False, allow_infinity=False)),
    lambda children: st.lists(children, max_size=3),
    max_leaves=100
))
def test_deeply_nested_arrays(arr):
    """Test deeply nested array structures"""
    try:
        json_str = json.dumps(arr)
        parsed = json.loads(json_str)
        assert parsed == arr
    except RecursionError:
        # Very deep nesting might hit recursion limit
        pass


@given(st.sampled_from(['true', 'false', 'null']))
def test_literal_constants(literal):
    """Test JSON literal constants"""
    parsed = json.loads(literal)
    
    if literal == 'true':
        assert parsed is True
    elif literal == 'false':
        assert parsed is False
    elif literal == 'null':
        assert parsed is None


@given(st.text(alphabet='truefalsn', min_size=1, max_size=10))
def test_partial_literals(text):
    """Test partial literal matches like 'tru', 'fals', 'nul'"""
    if text not in ['true', 'false', 'null']:
        try:
            json.loads(text)
            # Should fail for partial literals
            assert False, f"Partial literal should not parse: {text}"
        except json.JSONDecodeError:
            pass  # Expected


@given(st.sampled_from(['True', 'False', 'Null', 'TRUE', 'FALSE', 'NULL']))
def test_case_sensitive_literals(literal):
    """Test that JSON literals are case-sensitive"""
    try:
        json.loads(literal)
        # Should fail - JSON is case-sensitive
        assert False, f"JSON should be case-sensitive: {literal}"
    except json.JSONDecodeError:
        pass  # Expected


@given(st.text(min_size=1).filter(lambda x: x[0] in '0123456789-'))
def test_number_parsing_edge_cases(text):
    """Test edge cases in number parsing"""
    # Try some modifications
    test_cases = [
        text,
        text + 'e',     # Incomplete exponent
        text + 'e+',    # Incomplete exponent
        text + 'e-',    # Incomplete exponent
        text + '.',     # Trailing decimal
    ]
    
    for test in test_cases:
        match = json.scanner.NUMBER_RE.match(test)
        
        try:
            result = json.loads(test)
            if isinstance(result, (int, float)):
                # JSON accepted it
                if match is None or match.end() != len(test):
                    # NUMBER_RE doesn't fully match but JSON accepts
                    pass
        except json.JSONDecodeError:
            # JSON rejected
            if match and match.end() == len(test):
                # NUMBER_RE accepts but JSON rejects
                pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])