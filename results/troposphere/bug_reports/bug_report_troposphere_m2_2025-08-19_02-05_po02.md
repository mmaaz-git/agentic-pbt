# Bug Report: troposphere.m2 DesiredCapacity Accepts Invalid Range

**Target**: `troposphere.m2.HighAvailabilityConfig`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `DesiredCapacity` property in `troposphere.m2.HighAvailabilityConfig` accepts any integer value, violating AWS CloudFormation's requirement that it must be between 1 and 100.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.m2 as m2

@given(st.one_of(
    st.integers(max_value=0),  # <= 0 should be invalid
    st.integers(min_value=101)  # > 100 should be invalid
))
def test_high_availability_config_invalid_capacity(capacity):
    """Test that HighAvailabilityConfig accepts invalid DesiredCapacity values."""
    config = m2.HighAvailabilityConfig(DesiredCapacity=capacity)
    
    serialized = config.to_dict()
    assert 'DesiredCapacity' in serialized
```

**Failing input**: `0` (below minimum) or `101` (above maximum)

## Reproducing the Bug

```python
import troposphere.m2 as m2

config1 = m2.HighAvailabilityConfig(DesiredCapacity=-5)
print("Negative capacity:", config1.to_dict())

config2 = m2.HighAvailabilityConfig(DesiredCapacity=0)
print("Zero capacity:", config2.to_dict())

config3 = m2.HighAvailabilityConfig(DesiredCapacity=1000)
print("Excessive capacity:", config3.to_dict())
```

## Why This Is A Bug

According to AWS CloudFormation documentation, the DesiredCapacity property must be between 1 and 100 (inclusive). The troposphere library uses the generic `integer` validator which doesn't enforce these constraints. This allows invalid CloudFormation templates to be generated that will fail when deployed to AWS.

## Fix

```diff
--- a/troposphere/m2.py
+++ b/troposphere/m2.py
@@ -8,7 +8,7 @@
 
 
 from . import AWSObject, AWSProperty, PropsDictType
-from .validators import boolean, integer
+from .validators import boolean, integer, integer_range
 
 
 class Definition(AWSProperty):
@@ -59,7 +59,7 @@ class HighAvailabilityConfig(AWSProperty):
     """
 
     props: PropsDictType = {
-        "DesiredCapacity": (integer, True),
+        "DesiredCapacity": (integer_range(1, 100), True),
     }
```