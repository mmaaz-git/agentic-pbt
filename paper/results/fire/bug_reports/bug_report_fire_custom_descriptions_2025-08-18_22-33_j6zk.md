# Bug Report: fire.custom_descriptions Content Loss in String Truncation

**Target**: `fire.custom_descriptions` and `fire.formatting.EllipsisTruncate`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `EllipsisTruncate` function loses all string content when `available_space=3`, returning just "..." instead of preserving at least some characters from the original string.

## Property-Based Test

```python
from hypothesis import given, strategies as st, example
import fire.formatting as formatting

@example(text='hello', available_space=3, line_length=80)
@given(st.text(min_size=4, max_size=100), st.integers(min_value=3, max_value=3), st.integers(min_value=80, max_value=100))
def test_ellipsis_truncate_preserves_content(text, available_space, line_length):
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    
    # Bug: When available_space=3 and text is longer than 3 chars,
    # the function returns just '...' with no content preserved
    if len(text) > available_space:
        assert result != '...', f"Should preserve some content, not just ellipsis"
```

**Failing input**: `EllipsisTruncate('hello', 3, 80)` returns `'...'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
import fire.formatting as formatting

result = formatting.EllipsisTruncate('hello', 3, 80)
print(f"Result: '{result}'")
assert result == '...', "Bug confirmed: all content lost"

result2 = formatting.EllipsisTruncate('important data', 3, 80)
print(f"Result: '{result2}'")
assert result2 == '...', "Bug confirmed: all content lost"
```

## Why This Is A Bug

When `available_space=3` (equal to `len('...')`), the function incorrectly truncates text to `text[:0] + '...'`, resulting in complete content loss. The ellipsis becomes meaningless as it doesn't indicate what was truncated. Users expect at least one character to be preserved or the function to fall back to `line_length`.

## Fix

```diff
--- a/fire/formatting.py
+++ b/fire/formatting.py
@@ -69,7 +69,7 @@ def Error(text):
 
 def EllipsisTruncate(text, available_space, line_length):
   """Truncate text from the end with ellipsis."""
-  if available_space < len(ELLIPSIS):
+  if available_space <= len(ELLIPSIS):
     available_space = line_length
   # No need to truncate
   if len(text) <= available_space:
```