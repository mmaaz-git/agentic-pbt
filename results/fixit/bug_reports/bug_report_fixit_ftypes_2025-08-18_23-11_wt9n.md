# Bug Report: fixit.ftypes Tags.parse() crashes on whitespace-only input

**Target**: `fixit.ftypes.Tags.parse`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `Tags.parse()` method raises an `IndexError` when given a string containing only whitespace or comma-separated whitespace, failing to handle edge cases that produce empty tokens after splitting and stripping.

## Property-Based Test

```python
from hypothesis import given, strategies as st, example
import fixit.ftypes as ftypes

@given(st.text())
@example(" ")
@example(", ")
def test_tags_parse_handles_any_input(tag_str):
    """Tags.parse should handle any string input without crashing"""
    result = ftypes.Tags.parse(tag_str)
    assert isinstance(result, ftypes.Tags)
```

**Failing input**: `" "` (single space)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')
import fixit.ftypes as ftypes

ftypes.Tags.parse(" ")
```

## Why This Is A Bug

The `Tags.parse()` method is meant to parse tag strings from configuration or user input. It already handles `None` and empty strings gracefully by returning an empty `Tags()` object. However, it crashes on whitespace-only input because:

1. The input `" "` is truthy (not caught by the `if not value:` check on line 136)
2. After splitting by comma and stripping, it produces an empty string token `""`
3. The code attempts to access `token[0]` on line 143 without checking if the token is empty
4. This causes an `IndexError: string index out of range`

This violates the expected behavior that the parser should handle malformed or edge-case inputs gracefully, especially since whitespace-only strings are a common edge case in user input.

## Fix

```diff
@@ -139,10 +139,12 @@ class Tags(Container[str]):
         include = set()
         exclude = set()
         tokens = {value.strip() for value in value.lower().split(",")}
         for token in tokens:
+            if not token:  # Skip empty tokens
+                continue
             if token[0] in "!^-":
                 exclude.add(token[1:])
             else:
                 include.add(token)
 
         return Tags(
```