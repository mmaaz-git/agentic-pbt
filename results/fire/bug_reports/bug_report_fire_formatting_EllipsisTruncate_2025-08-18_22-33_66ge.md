# Bug Report: fire.formatting.EllipsisTruncate Line Length Violation

**Target**: `fire.formatting.EllipsisTruncate`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `EllipsisTruncate` function violates its contract by returning text longer than the `line_length` parameter when `line_length` is smaller than the ellipsis string ("...").

## Property-Based Test

```python
from hypothesis import given, strategies as st
from fire import formatting

@given(
    st.text(min_size=0, max_size=200),
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=1, max_value=200)
)
def test_ellipsis_truncate_respects_available_space(text, available_space, line_length):
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    
    ellipsis_len = len('...')
    effective_space = available_space if available_space >= ellipsis_len else line_length
    
    assert len(result) <= effective_space
```

**Failing input**: `text='00', available_space=0, line_length=1`

## Reproducing the Bug

```python
from fire import formatting

text = '00'
available_space = 0
line_length = 1
result = formatting.EllipsisTruncate(text, available_space, line_length)

print(f"Result: '{result}' (length: {len(result)})")
print(f"Expected max length: {line_length}")
print(f"Violation: {len(result)} > {line_length}")
```

## Why This Is A Bug

When `available_space < len(ELLIPSIS)`, the function falls back to using `line_length`. However, if `line_length` is also smaller than the ellipsis length (3 characters), the function still returns the full ellipsis "...", violating the constraint that the result should not exceed `line_length`.

## Fix

```diff
--- a/fire/formatting.py
+++ b/fire/formatting.py
@@ -70,8 +70,11 @@ def EllipsisTruncate(text, available_space, line_length):
 def EllipsisTruncate(text, available_space, line_length):
   """Truncate text from the end with ellipsis."""
   if available_space < len(ELLIPSIS):
     available_space = line_length
+  # Handle case where line_length is also too small
+  if available_space < len(ELLIPSIS):
+    return text[:available_space]
   # No need to truncate
   if len(text) <= available_space:
     return text
   return text[:available_space - len(ELLIPSIS)] + ELLIPSIS
```