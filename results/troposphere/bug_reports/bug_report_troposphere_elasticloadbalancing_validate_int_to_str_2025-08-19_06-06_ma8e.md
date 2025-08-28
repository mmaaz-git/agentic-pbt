# Bug Report: troposphere.elasticloadbalancing.validate_int_to_str Raises Wrong Exception Type

**Target**: `troposphere.elasticloadbalancing.validate_int_to_str`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `validate_int_to_str` function raises ValueError instead of TypeError when given a string that cannot be converted to an integer, violating its implied contract.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.elasticloadbalancing as elb

@given(st.text())
def test_validate_int_to_str_from_str(s):
    """Test that string inputs behave correctly"""
    try:
        int_val = int(s)
        result = elb.validate_int_to_str(s)
        assert isinstance(result, str)
        assert result == str(int_val)
    except ValueError:
        # String doesn't represent an integer - should raise TypeError
        try:
            elb.validate_int_to_str(s)
            assert False, f"Should have raised TypeError for non-integer string: {repr(s)}"
        except TypeError as e:
            assert "must be either int or str" in str(e)
```

**Failing input**: `''` (empty string)

## Reproducing the Bug

```python
import troposphere.elasticloadbalancing as elb

# All of these raise ValueError instead of TypeError
elb.validate_int_to_str('')     # ValueError: invalid literal for int() with base 10: ''
elb.validate_int_to_str('abc')  # ValueError: invalid literal for int() with base 10: 'abc'
elb.validate_int_to_str('  ')   # ValueError: invalid literal for int() with base 10: '  '
```

## Why This Is A Bug

The function explicitly raises TypeError with the message "Value {x} of type {type(x)} must be either int or str" for non-int, non-str types. For consistency and proper error handling, it should also raise TypeError (not ValueError) when given a string that cannot be converted to an integer. The current behavior creates inconsistent error handling where:
- Non-string/non-int types → TypeError (correct)
- Invalid string content → ValueError (inconsistent)

## Fix

```diff
def validate_int_to_str(x):
    """
    Backward compatibility - field was int and now str.
    Property: HealthCheck.Interval
    Property: HealthCheck.Timeout
    """

    if isinstance(x, int):
        return str(x)
    if isinstance(x, str):
-       return str(int(x))
+       try:
+           return str(int(x))
+       except ValueError:
+           raise TypeError(f"Value {x!r} of type {type(x)} must be either int or valid numeric str")

    raise TypeError(f"Value {x} of type {type(x)} must be either int or str")
```