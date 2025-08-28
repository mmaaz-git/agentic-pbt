# Bug Report: mdxpy normalize() Violates Idempotence

**Target**: `mdxpy.normalize`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `normalize()` function is not idempotent - applying it twice produces different results than applying it once, specifically when the input contains ']' characters.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from mdxpy import normalize

@given(st.text())
def test_normalize_idempotence(s):
    """The normalize function should be idempotent: f(f(x)) = f(x)"""
    normalized_once = normalize(s)
    normalized_twice = normalize(normalize(s))
    assert normalized_once == normalized_twice
```

**Failing input**: `']'`

## Reproducing the Bug

```python
from mdxpy import normalize

input_str = ']'
normalized_once = normalize(input_str)
normalized_twice = normalize(normalized_once)

print(f"Original: '{input_str}'")
print(f"Normalized once: '{normalized_once}'")  
print(f"Normalized twice: '{normalized_twice}'")

assert normalized_once == normalized_twice
```

## Why This Is A Bug

The normalize function is meant to prepare strings for MDX query generation by lowercasing, removing spaces, and escaping ']' characters. However, it should be idempotent - applying the normalization multiple times should produce the same result as applying it once. This property is violated because the function blindly replaces ']' with ']]' without checking if the bracket is already escaped, causing ']]' to become ']]]]' on subsequent applications.

## Fix

```diff
--- a/mdxpy/mdx.py
+++ b/mdxpy/mdx.py
@@ -66,7 +66,11 @@ class ElementType(Enum):
 
 
 def normalize(name: str) -> str:
-    return name.lower().replace(" ", "").replace("]", "]]")
+    # First lowercase and remove spaces
+    result = name.lower().replace(" ", "")
+    # Then escape ']' characters, but not those that are already escaped
+    result = result.replace("]]", "\x00").replace("]", "]]").replace("\x00", "]]")
+    return result
```