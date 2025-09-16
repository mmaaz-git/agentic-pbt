"""More aggressive property-based tests for format() to find edge cases."""

import math
import sys
from hypothesis import assume, given, strategies as st, settings
import pytest


@given(st.integers())
def test_format_spec_with_zero_width(num):
    """Property: Zero width should still format correctly"""
    result = format(num, '0')
    assert result == str(num)
    
    # With alignment
    result = format(num, '<0')
    assert result == str(num)


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_percentage_format(num):
    """Property: Percentage format multiplies by 100 and adds %"""
    result = format(num, '%')
    
    # Should end with %
    assert result.endswith('%')
    
    # The number should be approximately 100x the original
    if num != 0 and abs(num) < 1e10:  # Avoid overflow/precision issues
        # Parse the percentage value
        percent_str = result.rstrip('%')
        percent_val = float(percent_str)
        
        # % format has 6 decimal places by default, which causes rounding
        # The rounding error can be up to 0.5 * 10^-6 in the percentage value
        # For very small numbers, this can be a large relative error
        expected = num * 100
        
        # Use absolute tolerance based on the precision of % format (6 decimal places)
        # The error should be at most 0.5 * 10^-6 due to rounding
        assert math.isclose(percent_val, expected, abs_tol=5e-7)


@given(st.integers(min_value=-sys.maxsize, max_value=sys.maxsize))
def test_alternate_form_with_bases(num):
    """Property: Alternate form (#) adds prefix for non-zero numbers"""
    if num != 0:
        # Binary with #
        result = format(num, '#b')
        if num > 0:
            assert result.startswith('0b')
        else:
            assert result.startswith('-0b')
        
        # Octal with #
        result = format(num, '#o')
        if num > 0:
            assert result.startswith('0o')
        else:
            assert result.startswith('-0o')
        
        # Hex with #
        result = format(num, '#x')
        if num > 0:
            assert result.startswith('0x')
        else:
            assert result.startswith('-0x')


@given(st.integers(min_value=0, max_value=10**15))
def test_thousands_separator(num):
    """Property: Comma separator appears every 3 digits from right"""
    result = format(num, ',')
    
    # Remove commas and should get original number string
    without_commas = result.replace(',', '')
    assert without_commas == str(num)
    
    # Check comma placement
    if num >= 1000:
        assert ',' in result
        # Commas should appear every 3 digits from the right
        parts = result.split(',')
        # First part can be 1-3 digits, rest should be exactly 3
        for i, part in enumerate(parts):
            if i == 0:
                assert 1 <= len(part) <= 3
            else:
                assert len(part) == 3


@given(st.integers(min_value=0, max_value=10**15))
def test_underscore_separator(num):
    """Property: Underscore separator appears every 3 digits from right"""
    result = format(num, '_')
    
    # Remove underscores and should get original number string
    without_underscores = result.replace('_', '')
    assert without_underscores == str(num)
    
    # Check underscore placement for decimal
    if num >= 1000:
        assert '_' in result


@given(st.integers(), st.integers(min_value=1, max_value=100))
def test_zero_padding_with_sign(num, width):
    """Property: Zero padding with sign handling"""
    result = format(num, f'0{width}')
    
    # Result should be at least width characters
    assert len(result) >= min(width, len(str(num)))
    
    # For negative numbers, minus sign should be at the start
    if num < 0:
        assert result[0] == '-'
        # Rest should be digits (possibly with leading zeros)
        assert all(c.isdigit() for c in result[1:])


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_general_format_chooses_best(num):
    """Property: 'g' format chooses between fixed and exponential"""
    result_g = format(num, 'g')
    result_G = format(num, 'G')
    
    # Both should be valid string representations
    assert isinstance(result_g, str)
    assert isinstance(result_G, str)
    
    # G format should use uppercase E if exponential
    if 'e' in result_g:
        assert 'E' in result_G
        assert 'e' not in result_G


@given(st.integers(min_value=0, max_value=2**32))
def test_binary_with_width_and_zero_padding(num):
    """Property: Binary format with width and zero padding"""
    width = len(bin(num)) - 2 + 5  # Ensure we need padding
    result = format(num, f'0{width}b')
    
    assert len(result) == width
    # Should be all binary digits
    assert all(c in '01' for c in result)
    # Should convert back correctly
    assert int(result, 2) == num


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=1e-10, max_value=1e10))
def test_scientific_notation_precision(num):
    """Property: Scientific notation preserves precision"""
    for precision in range(0, 10):
        result = format(num, f'.{precision}e')
        
        # Should contain 'e' for exponent
        assert 'e' in result
        
        # Split into mantissa and exponent
        mantissa_str, exp_str = result.split('e')
        
        # Mantissa should have the right precision after decimal
        if '.' in mantissa_str and precision > 0:
            decimal_part = mantissa_str.split('.')[1]
            assert len(decimal_part) == precision


@given(st.integers(min_value=-10**10, max_value=10**10),
       st.integers(min_value=1, max_value=50))
def test_combining_format_options(num, width):
    """Property: Multiple format options can be combined"""
    # Try combining sign, zero padding, and width
    format_spec = f'+0{width}'
    result = format(num, format_spec)
    
    assert len(result) >= width or len(result) == len(str(num)) + 1  # +1 for sign
    
    # Should start with sign
    assert result[0] in ['+', '-']
    
    # Rest should be digits
    assert all(c.isdigit() for c in result[1:])


@given(st.text(min_size=0, max_size=10),
       st.integers(min_value=0, max_value=30))
def test_truncation_never_happens(text, width):
    """Property: Format never truncates the input"""
    result = format(text, str(width))
    
    # Result should always contain the full original text
    assert text in result
    
    # Length should be max of text length and width
    assert len(result) == max(len(text), width)


@given(st.floats(min_value=0.0, max_value=1.0, exclude_min=True))
def test_small_float_precision(num):
    """Property: Small floats should format correctly with high precision"""
    for precision in range(15, 20):
        result = format(num, f'.{precision}f')
        
        # Should be able to parse back
        parsed = float(result)
        
        # For numbers between 0 and 1, .Nf format gives N digits after decimal
        # But this doesn't guarantee N significant figures for small numbers
        # The parsed value should be close to original within float precision limits
        if num > 1e-10:
            # Use absolute tolerance for very small differences
            assert math.isclose(parsed, num, rel_tol=1e-9, abs_tol=1e-15)


@given(st.integers(min_value=2, max_value=36))
def test_invalid_base_format(base):
    """Property: Only certain bases are valid format specifiers"""
    # Only b, o, d, x, X are valid integer format type codes
    valid_bases = {'b': 2, 'o': 8, 'd': 10, 'x': 16, 'X': 16}
    
    num = 42
    # Try using the base number directly as format spec
    try:
        result = format(num, str(base))
        # If it works, it should be treating it as width
        assert len(result) >= base or len(result) == len(str(num))
    except ValueError:
        # This is fine - invalid format spec
        pass


@given(st.floats(allow_nan=False, allow_infinity=False),
       st.integers(min_value=0, max_value=100))
def test_precision_with_general_format(num, precision):
    """Property: 'g' format precision controls significant figures"""
    if precision == 0:
        precision = 1  # g format treats precision=0 as precision=1
    
    result = format(num, f'.{precision}g')
    
    # Should be a valid float representation
    parsed = float(result)
    
    # For non-zero numbers, check significant figures
    if num != 0 and abs(num) > 1e-100 and abs(num) < 1e100:
        # Remove signs, dots, and exponential notation for counting
        digits_only = result.replace('-', '').replace('+', '').replace('.', '')
        if 'e' in digits_only:
            mantissa = digits_only.split('e')[0]
        else:
            mantissa = digits_only
        
        # Significant figures should be at most precision
        # (may be less due to trailing zero removal in g format)
        significant_digits = len(mantissa.lstrip('0'))
        assert significant_digits <= precision


@given(st.one_of(
    st.just(float('nan')),
    st.just(float('inf')),
    st.just(float('-inf'))
))
def test_special_float_values(special_val):
    """Property: Special float values format correctly"""
    result = format(special_val)
    
    if math.isnan(special_val):
        assert result == 'nan'
    elif special_val == float('inf'):
        assert result == 'inf'
    elif special_val == float('-inf'):
        assert result == '-inf'
    
    # With width
    result_with_width = format(special_val, '10')
    assert len(result_with_width) == 10
    assert result in result_with_width