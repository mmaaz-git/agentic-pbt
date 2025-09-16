# Bug Report: fire.formatting Ellipsis Functions Incorrectly Handle Small available_space

**Target**: `fire.formatting.EllipsisTruncate` and `fire.formatting.EllipsisMiddleTruncate`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

EllipsisTruncate and EllipsisMiddleTruncate incorrectly truncate text when available_space is less than the ellipsis length, even after resetting available_space to line_length.

## Property-Based Test

```python
@given(st.integers(min_value=0, max_value=2), st.integers(min_value=10, max_value=100))
def test_ellipsis_truncate_small_available_space(available_space, line_length):
    """When available_space < len(ELLIPSIS), should handle gracefully."""
    text = "This is a very long string that needs truncation"
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    # When available_space is too small, function resets it to line_length
    # But if text is still longer than line_length, it still truncates
    if available_space < len(formatting.ELLIPSIS):
        if len(text) <= line_length:
            assert result == text
        else:
            assert len(result) == line_length
```

**Failing input**: `available_space=0, line_length=10`

## Reproducing the Bug

```python
import fire.formatting as fmt

text = 'This is a very long string that needs truncation'

result1 = fmt.EllipsisTruncate(text, available_space=0, line_length=10)
print(f'EllipsisTruncate: "{result1}" (len={len(result1)})')

result2 = fmt.EllipsisMiddleTruncate(text, available_space=0, line_length=10)  
print(f'EllipsisMiddleTruncate: "{result2}" (len={len(result2)})')

# Both truncate to line_length even when available_space was too small
assert len(result1) == 10
assert len(result2) == 10
```

## Why This Is A Bug

When `available_space < len(ELLIPSIS)` (3 characters), both functions reset `available_space = line_length` to avoid truncating to less than the ellipsis size. However, they then proceed to truncate the text to this new `available_space` value, even if `line_length` is also small. This defeats the purpose of the reset, which appears intended to prevent overly aggressive truncation.

## Fix

```diff
--- a/fire/formatting.py
+++ b/fire/formatting.py
@@ -70,6 +70,8 @@
 def EllipsisTruncate(text, available_space, line_length):
   """Truncate text from the end with ellipsis."""
   if available_space < len(ELLIPSIS):
+    if len(text) <= line_length:
+      return text
     available_space = line_length
   # No need to truncate
   if len(text) <= available_space:
@@ -80,6 +82,8 @@
 def EllipsisMiddleTruncate(text, available_space, line_length):
   """Truncates text from the middle with ellipsis."""
   if available_space < len(ELLIPSIS):
+    if len(text) <= line_length:
+      return text
     available_space = line_length
   if len(text) < available_space:
     return text
```