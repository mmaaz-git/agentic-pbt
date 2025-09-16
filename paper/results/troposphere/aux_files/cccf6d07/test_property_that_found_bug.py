from hypothesis import given, strategies as st, settings
import troposphere.rds as rds
import math

@given(st.floats(min_value=0.5, max_value=128, allow_nan=False, allow_infinity=False))
@settings(max_examples=1000)
def test_v2_capacity_accepts_values_close_to_half_steps(capacity):
    """
    Property: validate_v2_capacity should accept values that are extremely close 
    to valid half-steps (within floating-point precision tolerance).
    
    This is important because values computed through arithmetic operations
    may have tiny floating-point errors but should still be accepted.
    """
    # Determine if this value is close enough to a valid half-step
    nearest_half_step = round(capacity * 2) / 2
    distance_to_half_step = abs(capacity - nearest_half_step)
    
    # Consider it "close enough" if within floating-point precision
    is_close_to_half_step = distance_to_half_step < 1e-10
    
    try:
        result = rds.validate_v2_capacity(capacity)
        # If accepted, it should either be a true half-step or very close to one
        # The current implementation fails this property
    except ValueError as e:
        # If rejected, check if it was incorrectly rejected
        if is_close_to_half_step and 0.5 <= nearest_half_step <= 128:
            # This is the bug: rejecting values extremely close to valid half-steps
            raise AssertionError(
                f"BUG: validate_v2_capacity rejected {capacity:.17f} which is "
                f"only {distance_to_half_step:.2e} away from valid half-step {nearest_half_step}"
            )

if __name__ == "__main__":
    test_v2_capacity_accepts_values_close_to_half_steps()