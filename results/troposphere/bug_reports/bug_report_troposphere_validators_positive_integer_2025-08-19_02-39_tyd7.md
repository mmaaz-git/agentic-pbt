# Bug Report: troposphere.validators.positive_integer Accepts Negative Floats

**Target**: `troposphere.validators.positive_integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `positive_integer` function incorrectly accepts negative float values that truncate to non-negative integers, violating its contract to only accept positive (non-negative) integers.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.validators as validators
import pytest

@given(st.floats(min_value=-100, max_value=100))
def test_positive_integer_with_floats(value):
    """Test positive_integer behavior with float inputs."""
    if value >= 0 and value == int(value):
        result = validators.positive_integer(value)
        assert int(result) == int(value)
    elif value < 0:
        with pytest.raises(ValueError):
            validators.positive_integer(value)
```

**Failing input**: `-0.5`

## Reproducing the Bug

```python
import troposphere.validators as validators

result = validators.positive_integer(-0.5)
print(f"positive_integer(-0.5) = {result}")
print(f"int(result) = {int(result)}")

assert result == -0.5
assert int(result) == 0
```

## Why This Is A Bug

The function is named `positive_integer` and should reject all negative values. However, it accepts negative floats like -0.5, -0.9, etc. that truncate to 0 when converted to int. The function checks `if int(p) < 0` instead of checking if the actual value is negative. This allows negative values to pass through, which violates the expected behavior of a positive integer validator.

## Fix

```diff
def positive_integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    p = integer(x)
-   if int(p) < 0:
+   if float(p) < 0:
        raise ValueError("%r is not a positive integer" % x)
    return x
```