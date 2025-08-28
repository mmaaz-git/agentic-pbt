# Bug Report: troposphere.validators positive_integer Accepts Zero

**Target**: `troposphere.validators.positive_integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `positive_integer` validator incorrectly accepts 0 as a valid positive integer, when by definition a positive integer should be greater than 0.

## Property-Based Test

```python
@given(
    adjustment_type=st.sampled_from([
        emr_validators.CHANGE_IN_CAPACITY,
        emr_validators.PERCENT_CHANGE_IN_CAPACITY,
        emr_validators.EXACT_CAPACITY
    ]),
    scaling_adjustment=st.one_of(
        st.integers(min_value=-1000, max_value=1000),
        st.floats(min_value=-2.0, max_value=2.0, allow_nan=False, allow_infinity=False)
    )
)
def test_simple_scaling_policy_configuration_validation(adjustment_type, scaling_adjustment):
    try:
        config = emr.SimpleScalingPolicyConfiguration(
            AdjustmentType=adjustment_type,
            ScalingAdjustment=scaling_adjustment
        )
        config.validate()
        
        if adjustment_type == emr_validators.EXACT_CAPACITY:
            assert int(scaling_adjustment) > 0
    except (ValueError, TypeError):
        if adjustment_type == emr_validators.EXACT_CAPACITY:
            assert scaling_adjustment <= 0
```

**Failing input**: `adjustment_type='EXACT_CAPACITY', scaling_adjustment=0`

## Reproducing the Bug

```python
from troposphere import emr
from troposphere.validators import emr as emr_validators

config = emr.SimpleScalingPolicyConfiguration(
    AdjustmentType=emr_validators.EXACT_CAPACITY,
    ScalingAdjustment=0
)
config.validate()
print("BUG: ScalingAdjustment=0 with EXACT_CAPACITY was accepted")
```

## Why This Is A Bug

The EXACT_CAPACITY adjustment type uses the `positive_integer` validator which should reject zero. In mathematics and most programming contexts, positive integers are defined as integers greater than zero (1, 2, 3, ...). Zero is neither positive nor negative. This could lead to invalid AWS EMR cluster scaling configurations.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -54,7 +54,7 @@ def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
 
 def positive_integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     p = integer(x)
-    if int(p) < 0:
+    if int(p) <= 0:
         raise ValueError("%r is not a positive integer" % x)
     return x
```