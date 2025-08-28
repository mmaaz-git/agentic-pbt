# Bug Report: troposphere.cloudformation validate_int_to_str Unicode Digit Crash

**Target**: `troposphere.validators.cloudformation.validate_int_to_str`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `validate_int_to_str` function crashes with ValueError when given Unicode digit characters (like '²') that pass Python's `isdigit()` check but cannot be parsed by `int()`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators.cloudformation import validate_int_to_str

@given(st.text(min_size=1).filter(lambda s: s.strip() and s.strip().lstrip('-+').isdigit()))
def test_validate_int_to_str_with_numeric_strings(s):
    """Test that validate_int_to_str handles numeric strings correctly."""
    try:
        int_val = int(s)
        result = validate_int_to_str(s)
        assert isinstance(result, str)
        assert result == str(int_val)
    except ValueError:
        with pytest.raises(TypeError):
            validate_int_to_str(s)
```

**Failing input**: `'²'`

## Reproducing the Bug

```python
from troposphere.validators.cloudformation import validate_int_to_str

unicode_digit = '²'
result = validate_int_to_str(unicode_digit)
```

## Why This Is A Bug

The function is meant to handle string-to-string conversion for backward compatibility but fails on valid Unicode digit characters. The docstring states it handles "int or str" but crashes on certain string inputs that are technically digits according to Python's `isdigit()` method.

## Fix

```diff
def validate_int_to_str(x):
    """
    Backward compatibility - field was int and now str.
    Property: WaitCondition.Timeout
    """

    if isinstance(x, int):
        return str(x)
    if isinstance(x, str):
-       return str(int(x))
+       try:
+           return str(int(x))
+       except ValueError:
+           raise TypeError(f"Value {x} of type {type(x)} must be a valid numeric string")

    raise TypeError(f"Value {x} of type {type(x)} must be either int or str")
```