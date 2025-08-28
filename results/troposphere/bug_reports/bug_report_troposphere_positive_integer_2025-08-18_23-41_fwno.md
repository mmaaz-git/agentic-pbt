# Bug Report: troposphere.validators positive_integer accepts zero

**Target**: `troposphere.validators.positive_integer`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `positive_integer` validator incorrectly accepts 0 as a valid positive integer, when mathematically 0 is not positive.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators.apigatewayv2 import validate_authorizer_ttl

@given(st.integers())
def test_authorizer_ttl_boundary(ttl):
    try:
        result = validate_authorizer_ttl(ttl)
        assert 0 < result <= 3600
        assert result == ttl
    except (ValueError, TypeError):
        assert ttl <= 0 or ttl > 3600
```

**Failing input**: `0`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import positive_integer
from troposphere.validators.apigatewayv2 import validate_authorizer_ttl

result1 = positive_integer(0)
print(f"positive_integer(0) = {result1}")

result2 = validate_authorizer_ttl(0)
print(f"validate_authorizer_ttl(0) = {result2}")
```

## Why This Is A Bug

The function `positive_integer` is meant to validate positive integers. By mathematical definition, positive integers are greater than zero (1, 2, 3, ...). Zero is neither positive nor negative. This bug propagates to other validators like `validate_authorizer_ttl`, allowing invalid TTL values of 0 seconds.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -54,7 +54,7 @@ def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
 
 def positive_integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     p = integer(x)
-    if int(p) < 0:
+    if int(p) <= 0:
         raise ValueError("%r is not a positive integer" % x)
     return x
```