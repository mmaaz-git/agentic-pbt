"""Property-based tests for Python's built-in format() function."""

import math
from hypothesis import assume, given, strategies as st
import pytest


# Strategy for various Python objects
python_objects = st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.booleans(),
    st.none(),
    st.lists(st.integers(), max_size=3),
    st.dictionaries(st.text(min_size=1, max_size=3), st.integers(), max_size=2)
)


@given(python_objects)
def test_default_format_equals_str(value):
    """Property: format(x) with no format_spec should equal str(x)"""
    result = format(value)
    expected = str(value)
    assert result == expected


@given(st.text(min_size=0, max_size=20), st.integers(min_value=0, max_value=100))
def test_width_ensures_minimum_length(text, width):
    """Property: format with width specification ensures minimum output length"""
    format_spec = str(width)
    result = format(text, format_spec)
    assert len(result) >= width


@given(st.integers(min_value=0, max_value=2**63-1))
def test_binary_round_trip(num):
    """Property: Converting to binary and back preserves the integer"""
    binary_str = format(num, 'b')
    recovered = int(binary_str, 2)
    assert recovered == num


@given(st.integers(min_value=0, max_value=2**63-1))
def test_octal_round_trip(num):
    """Property: Converting to octal and back preserves the integer"""
    octal_str = format(num, 'o')
    recovered = int(octal_str, 8)
    assert recovered == num


@given(st.integers(min_value=0, max_value=2**63-1))
def test_hex_round_trip(num):
    """Property: Converting to hex and back preserves the integer"""
    hex_str = format(num, 'x')
    recovered = int(hex_str, 16)
    assert recovered == num
    
    # Also test uppercase
    hex_str_upper = format(num, 'X')
    recovered_upper = int(hex_str_upper, 16)
    assert recovered_upper == num


@given(st.text(min_size=0, max_size=10), st.integers(min_value=1, max_value=50))
def test_left_alignment_padding(text, width):
    """Property: Left alignment adds padding on the right"""
    if len(text) >= width:
        return  # No padding needed
    
    result = format(text, f'<{width}')
    assert len(result) == width
    assert result.startswith(text)
    assert result[len(text):] == ' ' * (width - len(text))


@given(st.text(min_size=0, max_size=10), st.integers(min_value=1, max_value=50))
def test_right_alignment_padding(text, width):
    """Property: Right alignment adds padding on the left"""
    if len(text) >= width:
        return  # No padding needed
    
    result = format(text, f'>{width}')
    assert len(result) == width
    assert result.endswith(text)
    assert result[:width - len(text)] == ' ' * (width - len(text))


@given(st.text(min_size=0, max_size=10), st.integers(min_value=1, max_value=50))
def test_center_alignment_length(text, width):
    """Property: Center alignment produces correct total length"""
    result = format(text, f'^{width}')
    assert len(result) == max(len(text), width)


@given(st.integers())
def test_sign_preservation_plus(num):
    """Property: '+' sign option shows sign for all numbers"""
    result = format(num, '+')
    if num >= 0:
        assert result.startswith('+')
    else:
        assert result.startswith('-')
    
    # The absolute value should be in the result
    assert str(abs(num)) in result


@given(st.integers())
def test_sign_preservation_space(num):
    """Property: ' ' sign option shows space for positive, minus for negative"""
    result = format(num, ' ')
    if num >= 0:
        assert result.startswith(' ') or result == '0'
    else:
        assert result.startswith('-')


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
       st.integers(min_value=0, max_value=10))
def test_float_precision_length(num, precision):
    """Property: Float precision controls decimal places"""
    result = format(num, f'.{precision}f')
    
    # Find the decimal point
    if '.' in result:
        decimal_part = result.split('.')[1]
        # Account for potential minus sign or other characters
        decimal_part = decimal_part.lstrip('-')
        assert len(decimal_part) == precision
    else:
        # No decimal point means precision was 0
        assert precision == 0


@given(st.integers(min_value=-2**63+1, max_value=2**63-1))
def test_negative_number_bases(num):
    """Property: Negative numbers in different bases preserve magnitude"""
    if num < 0:
        # Python's format for negative numbers in bases adds a minus sign
        for base_spec in ['b', 'o', 'x', 'd']:
            result = format(num, base_spec)
            assert result.startswith('-')
            
            # The magnitude should be correct
            if base_spec == 'b':
                magnitude = int(result[1:], 2)
            elif base_spec == 'o':
                magnitude = int(result[1:], 8)
            elif base_spec == 'x':
                magnitude = int(result[1:], 16)
            else:  # 'd'
                magnitude = int(result[1:], 10)
            
            assert magnitude == abs(num)


@given(st.text(alphabet='0123456789', min_size=1, max_size=5))
def test_numeric_string_format(num_str):
    """Property: Numeric strings can be formatted with width but not numeric format specs"""
    # Width should work
    result = format(num_str, '10')
    assert len(result) >= 10 or len(result) == len(num_str)
    
    # Numeric format specs should raise errors
    for spec in ['d', 'b', 'o', 'x', '.2f']:
        with pytest.raises((ValueError, TypeError)):
            format(num_str, spec)


@given(st.integers(), st.text(alphabet='xyz', min_size=1, max_size=3))
def test_invalid_format_spec_for_numbers(num, invalid_spec):
    """Property: Invalid format specs should raise errors consistently"""
    # Some completely invalid specs should raise errors
    if invalid_spec not in ['', 'd', 'b', 'o', 'x', 'X', 'n', 'e', 'E', 'f', 'F', 'g', 'G', '%']:
        try:
            result = format(num, invalid_spec)
            # If it doesn't raise, it should at least produce a string
            assert isinstance(result, str)
        except (ValueError, TypeError):
            # This is expected for truly invalid specs
            pass


@given(st.integers(min_value=0, max_value=255))
def test_all_bases_consistency(num):
    """Property: All base conversions should be reversible and consistent"""
    # Test all standard bases
    binary = format(num, 'b')
    octal = format(num, 'o')
    decimal = format(num, 'd')
    hex_lower = format(num, 'x')
    hex_upper = format(num, 'X')
    
    # All should convert back to the same number
    assert int(binary, 2) == num
    assert int(octal, 8) == num
    assert int(decimal, 10) == num
    assert int(hex_lower, 16) == num
    assert int(hex_upper, 16) == num
    
    # Hex upper and lower should differ only in case
    assert hex_lower.lower() == hex_upper.lower()


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=0.0, max_value=1e6),
       st.integers(min_value=1, max_value=10))
def test_float_format_types(num, precision):
    """Property: Different float format types should produce valid representations"""
    # Test different float format types
    formats = [
        f'.{precision}f',  # Fixed point
        f'.{precision}e',  # Scientific notation lowercase
        f'.{precision}E',  # Scientific notation uppercase
        f'.{precision}g',  # General format lowercase
        f'.{precision}G',  # General format uppercase
    ]
    
    for fmt in formats:
        result = format(num, fmt)
        assert isinstance(result, str)
        
        # For scientific notation, check format
        if 'e' in fmt or 'E' in fmt:
            if 'e' in fmt:
                assert 'e' in result.lower() or num == 0.0
            else:
                assert 'E' in result or num == 0.0


@given(st.text(min_size=1, max_size=10), 
       st.text(alphabet=' !@#$%^&*', min_size=1, max_size=1),
       st.integers(min_value=1, max_value=30))
def test_fill_character_with_alignment(text, fill_char, width):
    """Property: Fill character should be used for padding"""
    if len(text) >= width:
        return  # No padding needed
    
    # Skip test if text contains the fill character (makes counting ambiguous)
    if fill_char in text:
        return
    
    # Test with different alignments
    for align in ['<', '>', '^']:
        format_spec = f'{fill_char}{align}{width}'
        result = format(text, format_spec)
        
        assert len(result) == width
        assert text in result
        
        # Check that fill character is used for padding
        padding_count = width - len(text)
        assert result.count(fill_char) == padding_count