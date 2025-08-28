# Bug Report: fixit.ftypes.Tags.parse IndexError on Empty Tokens

**Target**: `fixit.ftypes.Tags.parse`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `Tags.parse()` method crashes with an IndexError when processing strings that contain empty tokens after splitting by comma, such as a single comma ",", multiple commas ",,", or whitespace-only strings.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from fixit.ftypes import Tags

@given(empty_input=st.sampled_from([None, "", "   ", ","]))
@settings(max_examples=50)
def test_tags_parse_empty_input(empty_input):
    """Test that Tags.parse handles empty/whitespace input correctly."""
    tags = Tags.parse(empty_input)
    
    # Should produce empty Tags object
    assert tags.include == ()
    assert tags.exclude == ()
    assert not tags  # __bool__ should return False
```

**Failing input**: `","` and `"   "`

## Reproducing the Bug

```python
from fixit.ftypes import Tags

# Bug: Single comma causes IndexError
Tags.parse(",")  # IndexError: string index out of range

# Bug: Whitespace string causes IndexError  
Tags.parse("   ")  # IndexError: string index out of range

# Bug: Multiple commas
Tags.parse(",,")  # IndexError: string index out of range
```

## Why This Is A Bug

The `Tags.parse()` method is designed to parse comma-separated tag strings but fails to handle edge cases where tokens become empty after splitting and stripping. This violates the expected behavior that the parser should gracefully handle malformed input strings that users might accidentally provide, such as extra commas or whitespace-only input.

## Fix

The issue occurs because the code doesn't check if a token is empty before accessing its first character. Here's the fix:

```diff
--- a/fixit/ftypes.py
+++ b/fixit/ftypes.py
@@ -140,6 +140,8 @@ class Tags(Container[str]):
         exclude = set()
         tokens = {value.strip() for value in value.lower().split(",")}
         for token in tokens:
+            if not token:  # Skip empty tokens
+                continue
             if token[0] in "!^-":
                 exclude.add(token[1:])
             else:
```