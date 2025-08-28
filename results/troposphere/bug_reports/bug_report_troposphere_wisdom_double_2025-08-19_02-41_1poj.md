# Bug Report: troposphere.wisdom.double Tuple Formatting Error

**Target**: `troposphere.wisdom.double`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `double` function produces incorrect error messages when given single-element tuples as input due to a Python string formatting bug.

## Property-Based Test

```python
@given(st.tuples(st.integers()))
def test_error_message_format(x):
    """Test that invalid inputs produce correctly formatted error messages."""
    try:
        wisdom.double(x)
    except ValueError as e:
        expected_msg = f"{x!r} is not a valid double"
        assert str(e) == expected_msg
```

**Failing input**: `(42,)`

## Reproducing the Bug

```python
import troposphere.wisdom as wisdom

input_value = (42,)

try:
    wisdom.double(input_value)
except ValueError as e:
    print(f"Input: {input_value!r}")
    print(f"Actual error: {str(e)!r}")
    print(f"Expected: '{input_value!r} is not a valid double'")
```

## Why This Is A Bug

The function should accurately report which value failed validation. When passed a single-element tuple like `(42,)`, the error message incorrectly states `'42 is not a valid double'` instead of `'(42,) is not a valid double'`. This happens because the `%` formatting operator unpacks single-element tuples, causing the formatting to use the tuple's contents rather than the tuple itself.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -94,7 +94,7 @@ def double(x: Any) -> Union[SupportsFloat, SupportsIndex, str, bytes, bytearray
     try:
         float(x)
     except (ValueError, TypeError):
-        raise ValueError("%r is not a valid double" % x)
+        raise ValueError("%r is not a valid double" % (x,))
     else:
         return x
```