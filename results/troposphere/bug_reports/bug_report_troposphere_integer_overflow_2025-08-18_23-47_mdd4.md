# Bug Report: troposphere.validators Integer Validator Overflow

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The integer validator crashes with OverflowError when given float infinity values instead of handling them gracefully.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import appsync

@given(st.just(float('inf')))
def test_graphql_api_infinity_query_limit(query_limit):
    try:
        api = appsync.GraphQLApi(
            "TestAPI",
            Name="TestAPI",
            AuthenticationType="API_KEY",
            QueryDepthLimit=query_limit
        )
    except OverflowError:
        assert False, "Should handle infinity gracefully, not crash"
    except (TypeError, ValueError):
        pass  # Expected graceful handling
```

**Failing input**: `float('inf')`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import appsync

api = appsync.GraphQLApi(
    "TestAPI",
    Name="TestAPI",
    AuthenticationType="API_KEY",
    QueryDepthLimit=float('inf')
)
```

## Why This Is A Bug

The integer validator is meant to validate integer values and reject invalid ones with a ValueError. However, when passed float infinity, it crashes with an unhandled OverflowError instead of gracefully rejecting the value. This violates the expected contract of validators to handle invalid input gracefully.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -46,7 +46,7 @@ def boolean(x):
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
         int(x)
-    except (ValueError, TypeError):
+    except (ValueError, TypeError, OverflowError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```