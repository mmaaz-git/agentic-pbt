# Bug Report: aiogram.utils.markdown Double-Escaping in Nested Functions

**Target**: `aiogram.utils.markdown`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Nesting markdown formatting functions causes double-escaping of special characters, resulting in invalid markdown output.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from aiogram.utils import markdown

@given(st.text(alphabet='[]()*._{}`', min_size=1, max_size=10))
@settings(max_examples=100)
def test_nested_markdown_double_escaping(text):
    """Test that nesting markdown functions doesn't cause double-escaping."""
    bold_text = markdown.bold(text)
    italic_bold_text = markdown.italic(bold_text)
    
    # Check if there's double-escaping (backslash before backslash)
    if '\\\\' in italic_bold_text:
        assert False, f"Double-escaping occurred: {italic_bold_text}"
```

**Failing input**: `'['`

## Reproducing the Bug

```python
from aiogram.utils import markdown

text = "["
bold_text = markdown.bold(text)
italic_bold_text = markdown.italic(bold_text)

print(f"Original: '{text}'")
print(f"After bold(): '{bold_text}'")
print(f"After italic(bold()): '{italic_bold_text}'")

assert italic_bold_text == '_\*\\\[\*_'
```

## Why This Is A Bug

When composing markdown formatting functions, the escaping logic is applied multiple times. The `bold()` function escapes special characters like `[` to `\[`. When `italic()` is applied to this already-escaped text, it escapes the backslash itself, turning `\[` into `\\[`. This produces invalid markdown that won't render correctly.

The expected behavior would be for `italic(bold(text))` to produce `_*\[*_`, but instead it produces `_\*\\\[\*_` with double-escaped characters.

## Fix

The issue is that each markdown function calls `quote()` on its input, including input that has already been quoted. The fix would be to either:

1. Track whether text has already been escaped to avoid double-escaping
2. Only escape at the final formatting stage
3. Provide separate internal functions that don't escape for composition

A potential fix approach:

```diff
def italic(*content: Any, sep: str = " ") -> str:
    """Make italic text (Markdown)"""
-    return markdown_decoration.italic(value=markdown_decoration.quote(_join(*content, sep=sep)))
+    # Check if content is already markdown-formatted to avoid double-escaping
+    joined = _join(*content, sep=sep)
+    # Only quote if not already formatted
+    if not _is_already_formatted(joined):
+        joined = markdown_decoration.quote(joined)
+    return markdown_decoration.italic(value=joined)
```