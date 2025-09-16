# Bug Report: fire.docstrings API Inconsistency in Empty Sections

**Target**: `fire.docstrings._join_lines` and `fire.docstrings.parse`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `_join_lines` function returns an empty string `''` for lists containing only blank lines, but returns `None` for empty lists, causing API inconsistency where empty docstring sections return `''` instead of `None`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import fire.docstrings as docstrings

@given(st.lists(st.text(alphabet=' \t\n'), min_size=1))
def test_join_lines_blank_only_consistency(lines):
    """Lists with only blank content should return None like empty lists."""
    result = docstrings._join_lines(lines)
    if all(not line.strip() for line in lines):
        assert result is None, f"Expected None for blank-only list, got {result!r}"
```

**Failing input**: `['']`

## Reproducing the Bug

```python
import fire.docstrings as docstrings

docstring_no_section = "Just a summary."
docstring_empty_section = "Summary.\n\nReturns:\n   "

result_no = docstrings.parse(docstring_no_section)
result_empty = docstrings.parse(docstring_empty_section)

print(f"No Returns section: returns = {result_no.returns!r}")     # None
print(f"Empty Returns section: returns = {result_empty.returns!r}") # ''

assert result_no.returns is None
assert result_empty.returns == ''  # Should be None for consistency!
```

## Why This Is A Bug

This violates the API contract where docstring fields should be `None` when they contain no meaningful content. Users checking `if info.returns:` will get different behavior for missing sections vs. empty sections, leading to subtle bugs in code that processes docstrings.

## Fix

```diff
--- a/fire/docstrings.py
+++ b/fire/docstrings.py
@@ -267,7 +267,10 @@ def _join_lines(lines):
   if group_lines:  # Process the final group.
     group_text = ' '.join(group_lines)
     group_texts.append(group_text)
-
-  return '\n\n'.join(group_texts)
+  
+  result = '\n\n'.join(group_texts)
+  if not result:
+    return None
+  return result
```