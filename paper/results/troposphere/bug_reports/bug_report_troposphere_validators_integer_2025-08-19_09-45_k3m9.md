# Bug Report: troposphere.validators Integer Validator Type Inconsistency

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer` validator function in troposphere validates that input can be converted to an integer but returns the original input unchanged, causing string values to remain as strings instead of being converted to integers.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import validators

@given(st.text().filter(lambda x: x.lstrip('-').isdigit()))
def test_integer_validator_returns_integer_type(str_value):
    """Test that integer validator returns actual integer type."""
    result = validators.integer(str_value)
    assert isinstance(result, int), f"Expected int, got {type(result).__name__}"
```

**Failing input**: `"123"`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators
from troposphere import licensemanager

# Direct validator test
result = validators.integer("123")
print(f"validators.integer('123') = {result!r}")
print(f"Type: {type(result).__name__}")
assert result == "123"  # Still a string!
assert isinstance(result, str)  # Not converted to int!

# Real-world usage example
config = licensemanager.BorrowConfiguration(
    AllowEarlyCheckIn=True,
    MaxTimeToLiveInMinutes="60"
)
config_dict = config.to_dict()
print(f"MaxTimeToLiveInMinutes = {config_dict['MaxTimeToLiveInMinutes']!r}")
assert config_dict['MaxTimeToLiveInMinutes'] == "60"  # String, not int!
```

## Why This Is A Bug

This violates the contract implied by the function name "integer" - developers expect a validator named `integer` to return an integer type, not just validate that the input could be converted to an integer. The function validates the input can be converted but then returns the original unchanged value. This causes:

1. Type confusion - string "123" and integer 123 are treated differently in many contexts
2. Unexpected behavior when the validated value is used in mathematical operations
3. Potential issues with type checkers and IDEs that expect integer types
4. Inconsistency with user expectations from a function named "integer"

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -44,10 +44,10 @@ def boolean(x: Any) -> bool:
     raise ValueError
 
 
-def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
+def integer(x: Any) -> int:
     try:
-        int(x)
+        return int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
-    else:
-        return x
```