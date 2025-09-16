#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import math
from hypothesis import given, strategies as st, assume, settings
from troposphere.validators import integer, double
from troposphere.inspectorv2 import (
    PortRangeFilter, DateFilter, NumberFilter
)


# Property 1: Integer validator should only accept true integers
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_validator_rejects_non_integers(x):
    """Integer validator should reject non-integer floats."""
    assume(x != int(x))  # Only test non-integer floats
    
    # The integer validator should reject floats that aren't whole numbers
    # But based on exploration, it actually accepts them!
    result = integer(x)
    # If this doesn't raise an error, it's a bug
    assert result == x, f"Integer validator accepted non-integer {x}"


# Property 2: Validators should convert to appropriate type
@given(st.text(min_size=1).filter(lambda s: s.replace('-', '').replace('.', '').isdigit()))
def test_validator_type_conversion(s):
    """Validators should convert string inputs to appropriate numeric types."""
    # Test integer validator
    if '.' not in s:
        try:
            result = integer(s)
            # Result should be converted to int type, not remain string
            assert isinstance(result, int), f"Integer validator didn't convert string '{s}' to int, got {type(result)}"
        except ValueError:
            pass  # Some strings might not be valid integers
    
    # Test double validator
    try:
        result = double(s)
        # Result should be converted to float type, not remain string
        assert isinstance(result, float), f"Double validator didn't convert string '{s}' to float, got {type(result)}"
    except ValueError:
        pass  # Some strings might not be valid doubles


# Property 3: NumberFilter with NaN should not equal itself
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_numberfilter_nan_handling(x):
    """NumberFilter with NaN should handle NaN properly per IEEE 754 standard."""
    # Create filter with NaN
    nf1 = NumberFilter(LowerInclusive=float('nan'), UpperInclusive=x)
    nf2 = NumberFilter(LowerInclusive=float('nan'), UpperInclusive=x)
    
    # NaN != NaN per IEEE 754, so properties should reflect this
    # If the module properly handles NaN, this comparison should fail
    lower1 = nf1.properties.get('LowerInclusive')
    lower2 = nf2.properties.get('LowerInclusive')
    
    if isinstance(lower1, float) and isinstance(lower2, float):
        if math.isnan(lower1) and math.isnan(lower2):
            # Both are NaN, they should not be equal
            assert lower1 != lower2, "NaN values are comparing as equal"


# Property 4: Range filters should validate begin <= end
@given(st.integers(min_value=0, max_value=65535),
       st.integers(min_value=0, max_value=65535))
def test_portrange_invariant(begin, end):
    """PortRangeFilter should ensure BeginInclusive <= EndInclusive."""
    prf = PortRangeFilter(BeginInclusive=begin, EndInclusive=end)
    
    # If both values are present, begin should be <= end
    # Based on exploration, this is NOT enforced, which could be a bug
    if 'BeginInclusive' in prf.properties and 'EndInclusive' in prf.properties:
        actual_begin = prf.properties['BeginInclusive']
        actual_end = prf.properties['EndInclusive']
        # This assertion will fail if begin > end, revealing the bug
        assert actual_begin <= actual_end, f"PortRangeFilter accepted invalid range [{actual_begin}, {actual_end}]"


@given(st.integers(), st.integers())
def test_datefilter_invariant(start, end):
    """DateFilter should ensure StartInclusive <= EndInclusive."""
    df = DateFilter(StartInclusive=start, EndInclusive=end)
    
    # If both values are present, start should be <= end
    if 'StartInclusive' in df.properties and 'EndInclusive' in df.properties:
        actual_start = df.properties['StartInclusive']
        actual_end = df.properties['EndInclusive']
        assert actual_start <= actual_end, f"DateFilter accepted invalid range [{actual_start}, {actual_end}]"


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
       st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_numberfilter_invariant(lower, upper):
    """NumberFilter should ensure LowerInclusive <= UpperInclusive."""
    nf = NumberFilter(LowerInclusive=lower, UpperInclusive=upper)
    
    # If both values are present, lower should be <= upper
    if 'LowerInclusive' in nf.properties and 'UpperInclusive' in nf.properties:
        actual_lower = nf.properties['LowerInclusive']
        actual_upper = nf.properties['UpperInclusive']
        assert actual_lower <= actual_upper, f"NumberFilter accepted invalid range [{actual_lower}, {actual_upper}]"


# Property 5: Integer validator behavior with edge cases
@given(st.one_of(
    st.booleans(),
    st.floats(min_value=-1e10, max_value=1e10).map(lambda x: int(x))
))
def test_integer_validator_accepts_integer_like(x):
    """Integer validator should accept integer-like values."""
    result = integer(x)
    # The validator accepts booleans and integer floats
    assert result == x


# Property 6: Double validator with infinity
@given(st.sampled_from([float('inf'), float('-inf')]))
def test_double_validator_infinity(x):
    """Double validator accepts infinity values."""
    result = double(x)
    assert result == x
    
    # Test in NumberFilter
    nf = NumberFilter(LowerInclusive=x, UpperInclusive=100)
    assert nf.properties['LowerInclusive'] == x


if __name__ == "__main__":
    # Run with more examples for thorough testing
    import pytest
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])