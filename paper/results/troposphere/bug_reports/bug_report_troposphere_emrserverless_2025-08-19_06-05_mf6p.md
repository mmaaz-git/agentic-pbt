# Bug Report: troposphere.emrserverless Integer Validator Accepts Non-Integer Floats

**Target**: `troposphere.emrserverless.integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer()` validator function incorrectly accepts non-integer float values like 1.5, 2.3, etc., when it should only accept values that are actual integers.

## Property-Based Test

```python
import troposphere.emrserverless as emr
from hypothesis import given, strategies as st

@given(f=st.floats(allow_nan=False, allow_infinity=False, min_value=-10**10, max_value=10**10))
def test_integer_validator_with_floats(f):
    """Test integer validator behavior with float inputs"""
    try:
        result = emr.integer(f)
        # If it succeeds, the float should have been exactly representable as int
        assert f == int(f), f"Float {f} was accepted but is not exactly an integer"
        assert result is f
    except ValueError as e:
        # Should only fail for non-integer floats
        if f == int(f):
            raise AssertionError(f"integer() rejected integer-valued float {f}") from e
```

**Failing input**: `f=1.5`

## Reproducing the Bug

```python
import troposphere.emrserverless as emr

# These non-integer floats should raise ValueError but don't
test_values = [1.5, 2.3, -3.7, 0.1, 0.9999]

for val in test_values:
    result = emr.integer(val)
    print(f"integer({val}) = {result}")
    # Output: integer(1.5) = 1.5
    # This accepts non-integer floats when it shouldn't
```

## Why This Is A Bug

The `integer()` function is a validator that should ensure values are integers. However, it only checks if `int(x)` doesn't raise an exception, not if the value is actually an integer. Since Python's `int()` function truncates floats (e.g., `int(1.5)` returns `1`), the validator incorrectly accepts non-integer float values.

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    try:
-       int(x)
+       # Check if it's a float and if so, ensure it's an integer value
+       if isinstance(x, float):
+           if x != int(x):
+               raise ValueError("%r is not a valid integer" % x)
+       int(x)
    except (ValueError, TypeError):
        raise ValueError("%r is not a valid integer" % x)
    else:
        return x
```