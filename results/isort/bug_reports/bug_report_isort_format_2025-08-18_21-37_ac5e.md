# Bug Report: isort.format.remove_whitespace Doesn't Remove Tabs

**Target**: `isort.format.remove_whitespace`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `remove_whitespace` function fails to remove tab characters despite its name suggesting it removes all whitespace.

## Property-Based Test

```python
@given(st.lists(st.sampled_from([' ', '\n', '\t', '\r', '\x0c']), min_size=0, max_size=20))
def test_remove_whitespace_handles_all_whitespace_types(whitespace_list):
    """remove_whitespace should handle various whitespace characters"""
    content = ''.join(whitespace_list) + 'test' + ''.join(whitespace_list)
    result = fmt.remove_whitespace(content)
    assert result == 'test'
```

**Failing input**: `['\t']`

## Reproducing the Bug

```python
import isort.format as fmt

content = "\ttest\t"
result = fmt.remove_whitespace(content)

assert result == "\ttest\t"  # Bug: Tabs are not removed
```

## Why This Is A Bug

The function name `remove_whitespace` implies it should remove all whitespace characters. In Python, tabs (`\t`) are considered whitespace according to `str.isspace()`. However, the function only removes spaces, newlines (via the line_separator parameter), and form feed characters (`\x0c`), leaving tabs intact.

## Fix

```diff
--- a/isort/format.py
+++ b/isort/format.py
@@ -87,7 +87,7 @@ def ask_whether_to_apply_changes_to_file(file_path: str) -> bool:
 
 
 def remove_whitespace(content: str, line_separator: str = "\n") -> str:
-    content = content.replace(line_separator, "").replace(" ", "").replace("\x0c", "")
+    content = content.replace(line_separator, "").replace(" ", "").replace("\x0c", "").replace("\t", "").replace("\r", "")
     return content
```