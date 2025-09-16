# Bug Report: isort.parse Strips Whitespace from Comments

**Target**: `isort.comments.parse` (imported as `parse_comments` in isort.parse)
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `parse_comments` function incorrectly strips whitespace characters from comment content, causing information loss and preventing accurate round-trip parsing of import statements with comments.

## Property-Based Test

```python
from hypothesis import given, strategies as st

@given(
    st.text(alphabet=st.characters(blacklist_characters='#'), min_size=1),
    st.text(min_size=0)
)
def test_parse_comments_roundtrip(import_part, comment_part):
    """For simple cases, we should be able to reconstruct the line."""
    if comment_part:
        line = f"{import_part}#{comment_part}"
    else:
        line = import_part
    
    parsed_import, parsed_comment = isort.parse.parse_comments(line)
    
    if comment_part:
        # The comment should be extracted (without the #)
        assert parsed_comment == comment_part
        # The import part should match
        assert parsed_import == import_part
    else:
        assert parsed_comment == ""
        assert parsed_import == import_part
```

**Failing input**: `import_part='0', comment_part='\r'`

## Reproducing the Bug

```python
from isort.comments import parse as parse_comments

line = "import something#\r"
import_part, comment = parse_comments(line)

print(f"Input line: {repr(line)}")
print(f"Parsed import: {repr(import_part)}")
print(f"Parsed comment: {repr(comment)}")

assert comment == "\r", f"Expected '\\r' but got {repr(comment)}"
```

## Why This Is A Bug

The `parse_comments` function is designed to split import statements from their associated comments. However, it uses `.strip()` on the comment content (line 10 in comments.py), which removes all leading and trailing whitespace. This causes several issues:

1. **Information Loss**: Whitespace-only comments (like `\r`, `\n`, or spaces) are completely lost
2. **Round-trip Failure**: The original line cannot be reconstructed from the parsed components
3. **Formatting Preservation**: As a code formatter, isort should preserve comment content exactly as written

## Fix

```diff
--- a/isort/comments.py
+++ b/isort/comments.py
@@ -7,7 +7,7 @@ def parse(line: str) -> Tuple[str, str]:
     """
     comment_start = line.find("#")
     if comment_start != -1:
-        return (line[:comment_start], line[comment_start + 1 :].strip())
+        return (line[:comment_start], line[comment_start + 1 :])
 
     return (line, "")
```