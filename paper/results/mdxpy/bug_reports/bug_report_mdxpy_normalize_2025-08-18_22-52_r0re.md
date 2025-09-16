# Bug Report: mdxpy normalize() Function Not Idempotent

**Target**: `mdxpy.normalize`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `normalize()` function is not idempotent - applying it twice to strings containing ']' produces different results than applying it once, violating the expected property that f(f(x)) = f(x).

## Property-Based Test

```python
from hypothesis import given, strategies as st
from mdxpy import normalize

@given(st.text())
def test_normalize_idempotence(s):
    """normalize() should be idempotent - normalizing twice equals normalizing once"""
    normalized_once = normalize(s)
    normalized_twice = normalize(normalized_once)
    assert normalized_once == normalized_twice
```

**Failing input**: `']'`

## Reproducing the Bug

```python
from mdxpy import normalize

input_str = ']'
normalized_once = normalize(input_str)
normalized_twice = normalize(normalized_once)

print(f"Input: '{input_str}'")
print(f"Normalized once: '{normalized_once}'")
print(f"Normalized twice: '{normalized_twice}'")

assert normalized_once == normalized_twice, f"Not idempotent: '{normalized_once}' != '{normalized_twice}'"
```

## Why This Is A Bug

The normalize function replaces ']' with ']]' to escape brackets in MDX expressions. However, when the already-normalized string ']]' is passed through normalize again, it replaces each ']' with ']]', resulting in ']]]]'. This breaks idempotence, which is a fundamental property expected of normalization functions. This could lead to incorrect MDX queries when normalize is called multiple times in a processing pipeline.

## Fix

```diff
def normalize(name: str) -> str:
-    return name.lower().replace(" ", "").replace("]", "]]")
+    # First unescape any already escaped brackets to ensure idempotence
+    temp = name.lower().replace(" ", "")
+    # Replace only unescaped brackets
+    result = ""
+    i = 0
+    while i < len(temp):
+        if i < len(temp) - 1 and temp[i:i+2] == ']]':
+            result += ']]'
+            i += 2
+        elif temp[i] == ']':
+            result += ']]'
+            i += 1
+        else:
+            result += temp[i]
+            i += 1
+    return result
```