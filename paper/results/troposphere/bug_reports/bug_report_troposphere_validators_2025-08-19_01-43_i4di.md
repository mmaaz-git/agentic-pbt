# Bug Report: troposphere.validators Integer Validators Don't Convert Floats to Integers

**Target**: `troposphere.validators.integer` and `troposphere.validators.positive_integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer` and `positive_integer` validators in troposphere accept float values but fail to convert them to integers, returning the float unchanged. This affects all integer properties across the entire troposphere library.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.greengrass as greengrass

@given(space=st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False))
def test_integer_property_validation(space):
    """Integer properties should convert float values to integers"""
    logger = greengrass.Logger(
        "TestLogger",
        Component="test",
        Id="logger-id",
        Level="INFO",
        Type="FileSystem"
    )
    
    # Set integer property to a float value
    logger.Space = space
    result = logger.to_dict()
    
    if 'Space' in result:
        # Bug: float values are not converted to integers
        assert isinstance(result['Space'], int), f"Expected int, got {type(result['Space'])}"
```

**Failing input**: `space=0.0` (or any float value)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer

# Direct test of the validator
result = integer(42.0)
print(f"integer(42.0) = {result} (type: {type(result).__name__})")
# Output: integer(42.0) = 42.0 (type: float)

# The validator accepts the float but doesn't convert it
assert result == 42.0
assert isinstance(result, float)  # Bug: should be int

# Test with troposphere resources
import troposphere.greengrass as greengrass

logger = greengrass.Logger(
    "TestLogger",
    Component="test",
    Id="logger-id",
    Level="INFO",
    Type="FileSystem",
    Space=100.0
)

logger_dict = logger.to_dict()
print(f"Logger.Space: {logger_dict['Space']} (type: {type(logger_dict['Space']).__name__})")
# Output: Logger.Space: 100.0 (type: float)
```

## Why This Is A Bug

The integer validator is designed to ensure properties receive integer values. The validator checks that the input can be converted to an integer (line 48 in validators/__init__.py) but then returns the original value unchanged (line 52). This violates the expected behavior that integer properties should contain integer values, not floats.

This affects CloudFormation template generation where integer properties might be serialized as floats (e.g., `100.0` instead of `100`), which could cause issues with strict CloudFormation parsers or downstream tools expecting integer types.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -46,10 +46,10 @@ def boolean(x: Any) -> bool:
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
         int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
-        return x
+        return int(x)
 
 
 def positive_integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     p = integer(x)
     if int(p) < 0:
         raise ValueError("%r is not a positive integer" % x)
-    return x
+    return p
```