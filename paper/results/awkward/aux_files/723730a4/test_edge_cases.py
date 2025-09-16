#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
import awkward.prettyprint as pp
import math

# Test for potential integer overflow or precision issues
@given(st.integers(min_value=-10, max_value=-1))
def test_half_negative_numbers(n):
    """Test half() with negative numbers"""
    result = pp.half(n)
    expected = math.ceil(n / 2)
    assert result == expected, f"half({n}) = {result}, expected {expected}"

# Test bytes_repr with boundary values
@given(st.sampled_from([999, 1000, 1001, 999999, 1000000, 1000001,
                        999999999, 1000000000, 1000000001]))
def test_bytes_repr_boundaries(nbytes):
    """Test bytes_repr at unit boundaries"""
    result = pp.bytes_repr(nbytes)
    print(f"{nbytes:11,} -> {result}")
    
    # Verify the boundaries are consistent
    if nbytes <= 1000:
        # Should be bytes  
        assert result.endswith(" B"), f"Expected B for {nbytes}, got {result}"
    elif nbytes <= 1000000:
        # Could be kB or B depending on exact boundary
        assert result.endswith((" B", " kB")), f"Unexpected unit for {nbytes}: {result}"
    elif nbytes <= 1000000000:
        # Could be MB or kB
        assert result.endswith((" kB", " MB")), f"Unexpected unit for {nbytes}: {result}"
    else:
        # Should be GB or MB
        assert result.endswith((" MB", " GB")), f"Unexpected unit for {nbytes}: {result}"

# Test Formatter with edge case numbers
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_formatter_handles_all_floats(value):
    """Test that Formatter handles all valid floats without crashing"""
    formatter = pp.Formatter()
    result = formatter(value)
    # Should produce a string
    assert isinstance(result, str)
    # Should be parseable back to float (approximately)
    if result not in ['inf', '-inf', 'nan']:
        try:
            float(result)
        except ValueError:
            assert False, f"Formatter produced unparseable float: {result} from {value}"

# Test for potential issues with alternate() at boundaries
@given(st.integers(min_value=-5, max_value=-1))
def test_alternate_negative_length(length):
    """Test alternate() with negative length - should it handle this?"""
    # This might reveal if there's missing validation
    try:
        result = list(pp.alternate(length))
        # If it doesn't raise an error, check if result makes sense
        print(f"alternate({length}) succeeded: {result}")
        # Negative length should probably return empty or raise error
    except Exception as e:
        print(f"alternate({length}) raised: {type(e).__name__}: {e}")

# Test special float values
def test_formatter_special_floats():
    """Test Formatter with special float values"""
    formatter = pp.Formatter(precision=3)
    
    # Test very small numbers
    small_nums = [1e-100, 1e-50, 1e-10, 1e-5]
    for num in small_nums:
        result = formatter(num)
        print(f"Format {num}: {result}")
    
    # Test very large numbers  
    large_nums = [1e10, 1e50, 1e100, 1e200]
    for num in large_nums:
        result = formatter(num)
        print(f"Format {num}: {result}")
    
    # Test numbers that might cause precision issues
    tricky_nums = [0.1 + 0.2, 1/3, 2/3, 7/9]
    for num in tricky_nums:
        result = formatter(num)
        print(f"Format {num}: {result}")

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s", "--tb=short"])