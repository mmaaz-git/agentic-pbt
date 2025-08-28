import numpy as np
from hypothesis import given, strategies as st, settings
import pytest


@given(st.floats(min_value=1e-162, max_value=1e-160, allow_nan=False, allow_infinity=False))
@settings(max_examples=1000)
def test_sqrt_square_subnormal_precision(x):
    """Test sqrt(square(x)) for numbers that produce subnormal squares"""
    squared = np.square(x)
    
    # Skip if underflowed to exactly zero
    if squared == 0:
        return
        
    result = np.sqrt(squared)
    
    if result == 0:
        # sqrt returned zero for non-zero squared value - definitely a problem
        assert False, f"sqrt({squared}) returned 0, but squared was non-zero"
    
    # Check relative error
    relative_error = abs(result - x) / x
    
    # For subnormal results, we expect some loss of precision, but not this much
    # IEEE 754 subnormals should still maintain reasonable precision
    assert relative_error < 0.1, f"Excessive relative error {relative_error} for x={x}, squared={squared}, result={result}"


@given(st.floats(min_value=1e-200, max_value=1e-150, allow_nan=False, allow_infinity=False))
def test_square_underflow_consistency(x):
    """Test that square handles underflow consistently"""
    squared = np.square(x)
    squared_alt = x * x
    
    assert squared == squared_alt, f"np.square({x}) != {x}*{x}: {squared} != {squared_alt}"


@given(st.floats(min_value=1e-170, max_value=1e-150, allow_nan=False, allow_infinity=False))
def test_sqrt_square_precision_degradation(x):
    """Measure precision degradation in sqrt(square(x)) for very small numbers"""
    squared = np.square(x)
    
    if squared == 0:
        # Complete underflow
        return
    
    result = np.sqrt(squared)
    
    if result == 0:
        # This shouldn't happen if squared != 0
        pytest.fail(f"sqrt returned 0 for non-zero input {squared}")
    
    relative_error = abs(result - x) / x
    
    # Collect data about precision loss
    if relative_error > 0.01:  # More than 1% error
        print(f"\nSignificant precision loss:")
        print(f"  x = {x}")
        print(f"  x^2 = {squared}")
        print(f"  sqrt(x^2) = {result}")
        print(f"  Relative error = {relative_error:.2%}")
        print(f"  x^2 is subnormal: {squared < np.finfo(np.float64).tiny}")


if __name__ == "__main__":
    print("Testing NumPy subnormal number handling...")
    pytest.main([__file__, "-v", "-s", "--tb=short"])