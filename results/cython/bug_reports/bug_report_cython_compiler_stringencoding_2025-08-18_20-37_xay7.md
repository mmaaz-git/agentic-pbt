# Bug Report: Cython.Compiler.StringEncoding Infinite Loop in split_string_literal

**Target**: `Cython.Compiler.StringEncoding.split_string_literal`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `split_string_literal` function enters an infinite loop when called with a limit parameter less than or equal to 0, causing the program to hang indefinitely.

## Property-Based Test

```python
from hypothesis import given, strategies as st, example
import Cython.Compiler.StringEncoding as SE

@given(st.text(min_size=1, max_size=100), 
       st.integers(min_value=-10, max_value=0))
@example("test", 0)
@example("test", -1)
def test_split_string_literal_nonpositive_limits(s, limit):
    """Test that split_string_literal handles non-positive limits safely."""
    result = SE.split_string_literal(s, limit)
    # This test will hang indefinitely with limit <= 0
```

**Failing input**: `("test", 0)`

## Reproducing the Bug

```python
import Cython.Compiler.StringEncoding as SE

# This will hang indefinitely
result = SE.split_string_literal("test", 0)
```

## Why This Is A Bug

The function's while loop at line 310 (`while start < len(s)`) never terminates when `limit <= 0`:

1. With `limit = 0`: The variable `end = start + 0 = start`, so `start` never advances
2. With `limit < 0`: The variable `end = start + limit < start`, causing backwards progression or other undefined behavior
3. The loop continues infinitely as `start` never reaches or exceeds `len(s)`

While the function documentation mentions it's for handling MSVC's limitation with long string literals (defaulting to 2000), there's no input validation to prevent invalid limit values. This could cause production code to hang if the limit is misconfigured or calculated dynamically.

## Fix

```diff
--- a/Cython/Compiler/StringEncoding.py
+++ b/Cython/Compiler/StringEncoding.py
@@ -302,6 +302,8 @@
 
 def split_string_literal(s, limit=2000):
     # MSVC can't handle long string literals.
+    if limit <= 0:
+        raise ValueError(f"limit must be positive, got {limit}")
     if len(s) < limit:
         return s
     else:
```