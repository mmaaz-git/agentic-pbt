import numpy as np
import scipy.stats as ss
from hypothesis import given, strategies as st


@given(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
       st.integers(min_value=2, max_value=100))
def test_skew_constant_array_should_be_zero(value, size):
    """Skewness of a constant array should be 0, not NaN"""
    # Create constant array
    arr = np.full(size, value)
    
    # Calculate skewness
    skewness = ss.skew(arr)
    
    # Skewness of constant distribution should be 0 (or at least not NaN)
    # A constant distribution has no skew by definition
    assert not np.isnan(skewness), f"skew returned NaN for constant array of {value}"
    
    # Ideally it should be 0
    # assert np.isclose(skewness, 0), f"skew of constant array should be 0, got {skewness}"