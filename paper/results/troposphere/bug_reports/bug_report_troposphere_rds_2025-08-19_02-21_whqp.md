# Bug Report: troposphere.rds Floating-Point Precision Error in validate_v2_capacity

**Target**: `troposphere.rds.validate_v2_capacity`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `validate_v2_capacity` function incorrectly rejects values that are extremely close to valid half-steps due to floating-point precision issues, causing legitimate capacity values to be rejected.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import troposphere.rds as rds
import math

@given(st.floats(min_value=0.5, max_value=128, allow_nan=False, allow_infinity=False))
@settings(max_examples=1000)
def test_v2_capacity_accepts_values_close_to_half_steps(capacity):
    """
    Property: validate_v2_capacity should accept values that are extremely close 
    to valid half-steps (within floating-point precision tolerance).
    """
    nearest_half_step = round(capacity * 2) / 2
    distance_to_half_step = abs(capacity - nearest_half_step)
    is_close_to_half_step = distance_to_half_step < 1e-10
    
    try:
        result = rds.validate_v2_capacity(capacity)
    except ValueError as e:
        if is_close_to_half_step and 0.5 <= nearest_half_step <= 128:
            raise AssertionError(
                f"BUG: validate_v2_capacity rejected {capacity:.17f} which is "
                f"only {distance_to_half_step:.2e} away from valid half-step {nearest_half_step}"
            )
```

**Failing input**: `1.0000000000000002` (1.0 + sys.float_info.epsilon)

## Reproducing the Bug

```python
import sys
import troposphere.rds as rds

value = 1.0 + sys.float_info.epsilon
print(f"Testing value: {value}")

try:
    rds.validate_v2_capacity(value)
    print("Accepted")
except ValueError as e:
    print(f"Rejected: {e}")
```

## Why This Is A Bug

The function uses `(capacity * 10) % 5 != 0` to check for half-step increments, but this check fails for values with tiny floating-point errors. Values that are mathematically equivalent to valid half-steps (like 1.0 + epsilon) get rejected even though they should be accepted. This affects real-world usage when capacity values are computed through arithmetic operations or parsed from external sources.

## Fix

```diff
def validate_v2_capacity(capacity):
    """
    Validate ServerlessV2ScalingConfiguration capacity for serverless DBCluster
    Property: ServerlessV2ScalingConfiguration.MinCapacity
    """
    if capacity < 0.5:
        raise ValueError(
            "ServerlessV2ScalingConfiguration capacity {} cannot be smaller than 0.5.".format(
                capacity
            )
        )
    if capacity > 128:
        raise ValueError(
            "ServerlessV2ScalingConfiguration capacity {} cannot be larger than 128.".format(
                capacity
            )
        )

-   if capacity * 10 % 5 != 0:
+   # Check if capacity is close to a valid half-step (accounting for floating-point precision)
+   nearest_half_step = round(capacity * 2) / 2
+   if abs(capacity - nearest_half_step) > 1e-10:
        raise ValueError(
            "ServerlessV2ScalingConfiguration capacity {} cannot be only specific in half-step increments.".format(
                capacity
            )
        )

-   return capacity
+   return nearest_half_step  # Return normalized value to avoid propagating precision errors
```