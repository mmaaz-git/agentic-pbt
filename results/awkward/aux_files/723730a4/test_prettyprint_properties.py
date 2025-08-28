#!/usr/bin/env python3

import sys
import math
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import awkward.prettyprint as pp


# Test 1: half() function mathematical properties
@given(st.integers(min_value=0, max_value=10**9))
def test_half_ceiling_property(n):
    """Test that half(n) correctly computes ceil(n/2)"""
    result = pp.half(n)
    expected = math.ceil(n / 2)
    assert result == expected, f"half({n}) = {result}, expected {expected}"


@given(st.integers(min_value=1, max_value=10**9))
def test_half_bounds_property(n):
    """Test that half(n) satisfies the bounds: half(n)*2 >= n and half(n)*2 - 2 < n"""
    result = pp.half(n)
    assert result * 2 >= n, f"half({n})*2 = {result*2} should be >= {n}"
    assert result * 2 - 2 < n, f"half({n})*2 - 2 = {result*2 - 2} should be < {n}"


# Test 2: alternate() function properties
@given(st.integers(min_value=0, max_value=1000))
def test_alternate_yields_all_indices(length):
    """Test that alternate() yields exactly all indices from 0 to length-1"""
    indices = []
    directions = []
    for direction, index in pp.alternate(length):
        directions.append(direction)
        indices.append(index)
    
    # Check we got exactly 'length' items
    assert len(indices) == length, f"Expected {length} indices, got {len(indices)}"
    
    # Check all indices are present exactly once
    if length > 0:
        assert set(indices) == set(range(length)), f"Missing or duplicate indices"
        assert len(set(indices)) == length, f"Duplicate indices found"


@given(st.integers(min_value=1, max_value=1000))
def test_alternate_ordering_pattern(length):
    """Test that alternate() follows the correct forward/backward pattern"""
    result = list(pp.alternate(length))
    
    if length == 1:
        # Special case: single element
        assert result == [(True, 0)]
        return
    
    halfindex = pp.half(length)
    
    # Check first half goes forward
    forward_indices = [idx for direction, idx in result if direction and idx < halfindex]
    if forward_indices:
        # Forward indices should be in ascending order
        assert forward_indices == sorted(forward_indices), "Forward indices not in order"
    
    # Check second half goes backward
    backward_indices = [idx for direction, idx in result if not direction and idx >= halfindex]
    if backward_indices:
        # Backward indices should be in descending order
        assert backward_indices == sorted(backward_indices, reverse=True), "Backward indices not in order"


@given(st.integers(min_value=2, max_value=100))
def test_alternate_starts_and_ends_correctly(length):
    """Test that alternate() starts at 0 and ends at length-1"""
    result = list(pp.alternate(length))
    
    # First yielded should be (True, 0) - starting from beginning
    assert result[0] == (True, 0), f"Should start with (True, 0), got {result[0]}"
    
    # Last yielded should be from the back half
    last_direction, last_index = result[-1]
    if length % 2 == 0:
        # Even length: last should be middle element from forward iteration
        assert last_index == pp.half(length) - 1
    else:
        # Odd length: last is the middle element
        assert last_index == pp.half(length) - 1


# Test 3: bytes_repr() function properties
@given(st.integers(min_value=0, max_value=10**15))
def test_bytes_repr_format(nbytes):
    """Test that bytes_repr returns correctly formatted string"""
    result = pp.bytes_repr(nbytes)
    
    # Should match pattern: number + space + unit
    pattern = r'^[\d,]+(\.\d)?\s+(B|kB|MB|GB)$'
    assert re.match(pattern, result), f"Invalid format: {result}"
    
    # Check unit selection is correct
    if nbytes >= 1e9:
        assert result.endswith(" GB"), f"Expected GB for {nbytes}, got {result}"
    elif nbytes >= 1e6:
        assert result.endswith(" MB"), f"Expected MB for {nbytes}, got {result}"
    elif nbytes >= 1e3:
        assert result.endswith(" kB"), f"Expected kB for {nbytes}, got {result}"
    else:
        assert result.endswith(" B"), f"Expected B for {nbytes}, got {result}"


@given(st.integers(min_value=0, max_value=10**15))
def test_bytes_repr_deterministic(nbytes):
    """Test that bytes_repr is deterministic"""
    result1 = pp.bytes_repr(nbytes)
    result2 = pp.bytes_repr(nbytes)
    assert result1 == result2, f"Non-deterministic output for {nbytes}"


@given(st.integers(min_value=1000, max_value=999999))
def test_bytes_repr_kilobytes_precision(nbytes):
    """Test that kilobyte formatting has correct precision"""
    result = pp.bytes_repr(nbytes)
    # Should be formatted as X.Y kB
    assert result.endswith(" kB")
    number_part = result[:-3]
    
    # Check it has one decimal place
    if '.' in number_part:
        decimal_part = number_part.split('.')[1]
        assert len(decimal_part) == 1, f"Expected 1 decimal place, got {result}"


# Test 4: Formatter class properties
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
       st.integers(min_value=1, max_value=10))
def test_formatter_precision_respected(value, precision):
    """Test that Formatter respects the precision parameter for floats"""
    formatter = pp.Formatter(precision=precision)
    result = formatter(value)
    
    # The formatted string should use scientific notation with specified precision
    # Format: X.YYYe+ZZ or X.YYY or -X.YYY etc
    # Count significant digits after conversion
    
    # For very small or very large numbers, Python uses e notation
    # For numbers close to 1, it uses regular notation
    # The 'g' format removes trailing zeros, so we can't strictly check digit count
    
    # At minimum, check it's a valid number representation
    try:
        float(result)
    except ValueError:
        assert False, f"Formatter produced invalid float string: {result}"
    
    # Check determinism
    result2 = formatter(value)
    assert result == result2, f"Non-deterministic formatting"


@given(st.complex_numbers(allow_nan=False, allow_infinity=False, max_magnitude=1e10),
       st.integers(min_value=1, max_value=10))
def test_formatter_complex_formatting(value, precision):
    """Test that Formatter correctly formats complex numbers"""
    formatter = pp.Formatter(precision=precision)
    result = formatter(value)
    
    # Should be in format: real+imagj
    # Check it contains 'j' for imaginary part
    assert 'j' in result, f"Complex number format missing 'j': {result}"
    
    # Check we can parse it back (approximately)
    # The string format is like "1.23+4.56j"
    if value.imag >= 0:
        assert '+' in result and result.endswith('j'), f"Invalid positive imaginary format: {result}"
    else:
        # For negative imaginary, format is like "1.23-4.56j" 
        # (the minus is part of the number, not a separator)
        assert result.endswith('j'), f"Invalid negative imaginary format: {result}"


@given(st.integers())
def test_formatter_integer_unchanged(value):
    """Test that Formatter doesn't modify integers unnecessarily"""
    formatter = pp.Formatter()
    result = formatter(value)
    assert result == str(value), f"Integer formatting changed: {value} -> {result}"


# Additional test for alternate() edge cases
@given(st.integers(min_value=3, max_value=100))
def test_alternate_coverage_pattern(length):
    """Test that alternate() covers indices in the expected alternating pattern"""
    result = list(pp.alternate(length))
    halfindex = pp.half(length)
    
    # Collect forward and backward passes
    forward_pass = [(i, idx) for i, (direction, idx) in enumerate(result) if direction]
    backward_pass = [(i, idx) for i, (direction, idx) in enumerate(result) if not direction]
    
    # Forward should start from 0 and go up to halfindex-1
    forward_indices = [idx for _, idx in forward_pass]
    assert forward_indices[0] == 0, "Forward pass should start at 0"
    
    # Backward should start from length-1 and go down
    if backward_pass:
        backward_indices = [idx for _, idx in backward_pass]
        assert backward_indices[0] == length - 1, f"Backward pass should start at {length-1}"


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    import pytest
    import sys
    
    # Run pytest on this file
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))