"""Intensive property-based testing with more examples."""

from hypothesis import given, strategies as st, settings
import math

# Test with 1000 examples each
@settings(max_examples=1000)
@given(st.integers())
def test_intensive_number_bases(num):
    """Intensive test of number base conversions"""
    if num >= 0:
        # Test all bases
        binary = format(num, 'b')
        octal = format(num, 'o')
        decimal = format(num, 'd')
        hex_lower = format(num, 'x')
        hex_upper = format(num, 'X')
        
        # All should convert back correctly
        assert int(binary, 2) == num
        assert int(octal, 8) == num
        assert int(decimal, 10) == num
        assert int(hex_lower, 16) == num
        assert int(hex_upper, 16) == num


@settings(max_examples=1000)
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e100, max_value=1e100),
       st.integers(min_value=0, max_value=20))
def test_intensive_float_formatting(num, precision):
    """Intensive test of float formatting with various precisions"""
    # Test fixed-point notation
    result_f = format(num, f'.{precision}f')
    parsed_f = float(result_f)
    
    # Test exponential notation
    result_e = format(num, f'.{precision}e')
    parsed_e = float(result_e)
    
    # Both should parse back to approximately the same value
    if abs(num) > 1e-100 and abs(num) < 1e100:
        assert math.isclose(parsed_f, num, rel_tol=1e-6, abs_tol=1e-10)
        assert math.isclose(parsed_e, num, rel_tol=1e-6, abs_tol=1e-10)


@settings(max_examples=1000)
@given(st.text(min_size=0, max_size=50),
       st.integers(min_value=0, max_value=100))
def test_intensive_alignment(text, width):
    """Intensive test of text alignment"""
    # Test all alignments
    for align in ['<', '>', '^']:
        result = format(text, f'{align}{width}')
        
        # Length should be correct
        assert len(result) == max(len(text), width)
        
        # Text should be present
        assert text in result
        
        # Padding should be spaces
        padding = result.replace(text, '')
        assert all(c == ' ' for c in padding)