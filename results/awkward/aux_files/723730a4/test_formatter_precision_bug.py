#!/usr/bin/env python3
"""
Property-based test that reveals the Formatter precision bug.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
import awkward.prettyprint as pp
import numpy as np

@given(
    st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100)
def test_formatter_respects_precision_for_python_floats(value, precision):
    """
    Test that Formatter respects precision for Python's built-in float type.
    
    The Formatter should format floats with the specified precision using
    the 'g' format specifier, which should limit significant digits.
    """
    formatter = pp.Formatter(precision=precision)
    
    # Format both Python float and numpy float64
    python_float_result = formatter(value)
    numpy_float_result = formatter(np.float64(value))
    
    # The numpy float should respect precision
    # Check that numpy result has reasonable length for the precision
    # (allowing some extra for exponent notation)
    max_expected_len = precision + 10  # precision digits + sign + decimal + exponent
    
    # Key assertion: Python float and numpy float64 of same value 
    # should produce similar output when formatted with same precision
    print(f"\nValue: {value}")
    print(f"Precision: {precision}")
    print(f"Python float result: {python_float_result}")
    print(f"NumPy float64 result: {numpy_float_result}")
    
    # They should be formatted similarly - if numpy respects precision,
    # Python float should too
    assert len(numpy_float_result) <= max_expected_len, \
        f"NumPy result too long: {numpy_float_result}"
    
    # THE BUG: Python float doesn't respect precision!
    assert len(python_float_result) <= max_expected_len, \
        f"Python float ignores precision setting! Got: {python_float_result} (length: {len(python_float_result)})"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])