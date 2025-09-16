# Bug Report: troposphere.validators positive_integer Accepts Zero

**Target**: `troposphere.validators.positive_integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-01-18

## Summary

The `positive_integer` validator incorrectly accepts 0 as a valid positive integer, violating the mathematical definition where positive integers are > 0.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import positive_integer

@given(st.integers(min_value=-10, max_value=10))
def test_positive_integer_validation(value):
    if value > 0:
        result = positive_integer(value)
        assert result == value
    else:
        with pytest.raises(ValueError):
            positive_integer(value)
```

**Failing input**: `0`

## Reproducing the Bug

```python
from troposphere.validators import positive_integer

result = positive_integer(0)
print(f"positive_integer(0) returned: {result}")
```

## Why This Is A Bug

In mathematics, positive integers are defined as integers greater than zero (1, 2, 3, ...). Zero is neither positive nor negative. The function name `positive_integer` implies it should only accept integers > 0, but the implementation incorrectly allows 0 to pass validation. This could lead to configuration errors in AWS CloudFormation templates where truly positive values are expected.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -55,7 +55,7 @@ def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
 
 def positive_integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     p = integer(x)
-    if int(p) < 0:
+    if int(p) <= 0:
         raise ValueError("%r is not a positive integer" % x)
     return x
```