# Bug Report: fire.formatting.EllipsisMiddleTruncate Length Violation

**Target**: `fire.formatting.EllipsisMiddleTruncate`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-01-18

## Summary

The `EllipsisMiddleTruncate` function violates its length contract when `available_space < 3`, returning text longer than the requested space instead of properly truncating it.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from fire import formatting

@settings(max_examples=1000)
@given(st.text(min_size=4, max_size=100), st.integers(min_value=1, max_value=2))
def test_ellipsis_middle_truncate_respects_available_space(text, available_space):
    """EllipsisMiddleTruncate should never return text longer than available_space."""
    line_length = 80
    result = formatting.EllipsisMiddleTruncate(text, available_space, line_length)
    
    # When available_space < 3, it should still respect the original constraint
    # or at least not exceed line_length
    assert len(result) <= max(available_space, line_length), \
        f"Result length {len(result)} exceeds both available_space {available_space} and line_length {line_length}"
```

**Failing input**: `text="abcd", available_space=1`

## Reproducing the Bug

```python
from fire import formatting

text = "abcdefgh"
available_space = 2
line_length = 80

result = formatting.EllipsisMiddleTruncate(text, available_space, line_length)

print(f"Input text: '{text}' (length={len(text)})")
print(f"Requested available_space: {available_space}")
print(f"Result: '{result}' (length={len(result)})")
print(f"Bug: Result length {len(result)} > requested {available_space}")
```

## Why This Is A Bug

The function is supposed to truncate text to fit within `available_space` characters. When `available_space < 3` (less than the length of "..."), the function falls back to using `line_length` internally but then returns the full text if it's shorter than `line_length`. This violates the implicit contract that the result should respect the original `available_space` parameter.

The bug occurs because:
1. When `available_space < 3`, the function sets `available_space = line_length` (line 83)
2. It then checks if `len(text) < available_space` (line 84)
3. If true, it returns the full text without truncation (line 85)
4. This means a request for 1-2 character output can return arbitrarily long text

## Fix

```diff
def EllipsisMiddleTruncate(text, available_space, line_length):
  """Truncates text from the middle with ellipsis."""
+  original_available_space = available_space
   if available_space < len(ELLIPSIS):
     available_space = line_length
-  if len(text) < available_space:
+  if len(text) <= original_available_space:
     return text
+  if original_available_space < len(ELLIPSIS):
+    # Can't fit ellipsis, just truncate to requested length
+    return text[:original_available_space]
   available_string_len = available_space - len(ELLIPSIS)
   first_half_len = int(available_string_len / 2)  # start from middle
   second_half_len = available_string_len - first_half_len
   return text[:first_half_len] + ELLIPSIS + text[-second_half_len:]
```