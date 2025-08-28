# Bug Report: click.style Adds ANSI Codes to Empty Strings

**Target**: `click.style`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `click.style()` function incorrectly adds ANSI escape codes when styling an empty string, producing non-empty output for empty input.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import click

@given(st.text())
def test_style_empty_string_with_params(text):
    if not text:
        styled = click.style(text, fg='red', bg='blue', bold=True)
        assert styled == ''
        
        unstyled = click.unstyle(styled)
        assert unstyled == text
```

**Failing input**: `text=''`

## Reproducing the Bug

```python
import click

text = ''
styled = click.style(text, fg='red', bg='blue', bold=True)

assert styled == '', f"Expected empty string, got {repr(styled)}"
```

## Why This Is A Bug

When styling an empty string, the function should return an empty string since there's no content to style. Instead, it returns ANSI escape codes without any actual content between them (`'\x1b[31m\x1b[44m\x1b[1m\x1b[0m'`). This violates the principle that styling empty content should produce empty output, and could cause issues in systems that check for empty strings.

## Fix

```diff
--- a/click/termui.py
+++ b/click/termui.py
@@ -540,6 +540,9 @@ def style(
     :param reset: if this is enabled a reset-all code is added at the
                   end of the string.
     """
+    if not text:
+        return ''
+        
     bits = []
 
     if fg:
```