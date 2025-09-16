import numpy as np
from hypothesis import given, strategies as st, settings
import math


@given(st.floats(min_value=2.2e-162, max_value=2.6e-162, allow_nan=False, allow_infinity=False))
@settings(max_examples=500)
def test_sqrt_square_extreme_precision_loss(x):
    """Find cases of extreme precision loss in sqrt(square(x))"""
    squared = np.square(x)
    
    if squared == 0:
        return
        
    result = np.sqrt(squared)
    
    if result == 0:
        return
    
    relative_error = abs(result - x) / x
    
    # Document extreme cases
    if relative_error > 0.15:  # More than 15% error
        print(f"\nEXTREME precision loss found:")
        print(f"  Input x: {x}")
        print(f"  square(x): {squared} ({squared.hex()})")
        print(f"  sqrt(square(x)): {result}")
        print(f"  Relative error: {relative_error:.1%}")
        print(f"  Lost precision: {x} -> {result}")
        
        # Check if this violates any mathematical properties
        # For positive x: sqrt(x^2) should equal x
        assert False, f"Extreme precision loss: {relative_error:.1%} error for x={x}"


@given(st.floats(min_value=1e-162, max_value=3e-162, allow_nan=False, allow_infinity=False))
def test_sqrt_square_monotonicity(x):
    """Test if sqrt(square(x)) preserves monotonicity for tiny positive numbers"""
    # For very small positive numbers
    epsilon = x * 0.1  # 10% larger
    y = x + epsilon
    
    if y > 3e-162:  # Stay in range
        return
    
    # Square both
    x_squared = np.square(x)
    y_squared = np.square(y)
    
    # If both squared values are distinct and non-zero
    if x_squared != y_squared and x_squared > 0 and y_squared > 0:
        x_result = np.sqrt(x_squared)
        y_result = np.sqrt(y_squared)
        
        # Check monotonicity: if x < y, then sqrt(square(x)) should be < sqrt(square(y))
        if x < y:
            if not (x_result <= y_result):
                print(f"\nMonotonicity violation:")
                print(f"  x={x}, y={y} (x < y)")
                print(f"  But sqrt(square(x))={x_result} > sqrt(square(y))={y_result}")
                assert False, "Monotonicity violated"


if __name__ == "__main__":
    import pytest
    print("Testing for extreme precision loss cases...")
    pytest.main([__file__, "-v", "-s", "--tb=short", "-x"])