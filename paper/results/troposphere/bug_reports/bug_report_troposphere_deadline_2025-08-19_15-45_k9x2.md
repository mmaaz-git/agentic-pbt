# Bug Report: troposphere.deadline integer validator accepts non-integer floats

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer()` validator function in troposphere accepts float values with decimal parts (e.g., 1.5, 2.7) when it should reject them, violating the contract of integer validation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.deadline as deadline

@given(st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x)))
def test_range_classes_reject_non_integers(float_val):
    """Test that Range classes reject non-integer values through the integer validator."""
    # AcceleratorCountRange should reject non-integers
    with pytest.raises(TypeError) as exc_info:
        deadline.AcceleratorCountRange(Min=float_val)
    assert "Min" in str(exc_info.value)
```

**Failing input**: `float_val=1.5`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

from troposphere.validators import integer

# These should raise ValueError but don't
result1 = integer(1.5)  
print(f"integer(1.5) = {result1}")  # Returns 1.5 (float)

result2 = integer(2.7)
print(f"integer(2.7) = {result2}")  # Returns 2.7 (float)

# This causes Range classes to accept non-integers
from troposphere.deadline import AcceleratorCountRange

range_obj = AcceleratorCountRange(Min=1.5, Max=10.7)
print(f"AcceleratorCountRange created with Min={range_obj.properties['Min']}, Max={range_obj.properties['Max']}")
print(f"Types: Min is {type(range_obj.properties['Min'])}, Max is {type(range_obj.properties['Max'])}")
```

## Why This Is A Bug

The `integer()` validator is used throughout troposphere to validate integer-only properties. By accepting float values with decimal parts, it violates the expected behavior and allows invalid data in CloudFormation templates. Range classes like `AcceleratorCountRange`, `MemoryMiBRange`, and `VCpuCountRange` expect integer values for Min/Max but receive floats instead.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,7 +45,10 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        int_val = int(x)
+        # Check if conversion loses precision (for numeric types)
+        if isinstance(x, (int, float)) and x != int_val:
+            raise ValueError("%r is not a valid integer" % x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
```