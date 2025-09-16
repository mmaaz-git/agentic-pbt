# Bug Report: troposphere.validators integer() Incorrectly Accepts Non-Integer Floats

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer()` validator incorrectly accepts float values with fractional parts, silently truncating them. This violates the semantic expectation that an "integer validator" should only accept actual integers.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere import validators

@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False).filter(lambda x: x != int(x)))
def test_integer_validator_accepts_non_integers(value):
    """Test that integer validator rejects non-integer floats."""
    # value has a fractional part (not equal to its integer conversion)
    assert value != int(value)
    
    # The integer validator should reject this
    with pytest.raises(ValueError):
        validators.integer(value)
```

**Failing input**: `1.5`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

result = validators.integer(1.5)
print(f"validators.integer(1.5) = {result}")  # Returns 1.5, should raise ValueError

port = validators.network_port(80.5) 
print(f"validators.network_port(80.5) = {port}")  # Returns 80.5, should raise ValueError
```

## Why This Is A Bug

The `integer()` function is semantically expected to validate that a value is an integer. However, it only checks if `int(x)` doesn't raise an exception, which succeeds for all floats (truncating fractional parts). This means:

1. `integer(1.5)` returns `1.5` instead of raising `ValueError`
2. Values with fractional parts are incorrectly accepted as "integers"
3. This propagates to functions using `integer()` internally, like `network_port()`
4. A network port of `80.5` is nonsensical but accepted, treating it as port `80`

This violates the principle of least surprise and can lead to silent data corruption where fractional values are unintentionally accepted and later truncated when used.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,7 +45,10 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        int_val = int(x)
+        # Check that the value is actually an integer (no truncation occurred)
+        if isinstance(x, float) and x != int_val:
+            raise ValueError("%r is not a valid integer" % x)
     except (ValueError, TypeError, OverflowError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```