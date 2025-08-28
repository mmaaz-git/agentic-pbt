# Bug Report: click.formatting.HelpFormatter.write_usage Loses Program Name

**Target**: `click.formatting.HelpFormatter.write_usage`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `write_usage` method fails to include the program name in its output when the `args` parameter is an empty string, resulting in malformed usage text.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import click.formatting

@given(st.text(min_size=1, max_size=20).filter(lambda x: '\x00' not in x and '\n' not in x))
def test_write_usage_with_empty_args_loses_prog(prog):
    formatter = click.formatting.HelpFormatter(width=80)
    formatter.write_usage(prog, '')
    output = formatter.getvalue()
    assert prog in output
```

**Failing input**: `prog='0'`

## Reproducing the Bug

```python
import click.formatting

formatter = click.formatting.HelpFormatter()
prog = 'mycommand'
args = ''

formatter.write_usage(prog, args)
output = formatter.getvalue()

print(f"Expected: 'Usage: mycommand\\n'")
print(f"Actual: {repr(output)}")
print(f"Bug: Program name '{prog}' is missing!")
```

## Why This Is A Bug

The `write_usage` method is responsible for formatting usage lines like "Usage: mycommand [OPTIONS]". When a command has no arguments (empty string), the method should still output "Usage: mycommand\n". However, due to the way `wrap_text` handles empty strings, the entire usage prefix (including the program name) is discarded, resulting in just a newline character. This affects all Click commands without arguments, producing malformed help text.

## Fix

```diff
--- a/click/formatting.py
+++ b/click/formatting.py
@@ -161,11 +161,15 @@ class HelpFormatter:
         if text_width >= (term_len(usage_prefix) + 20):
             # The arguments will fit to the right of the prefix.
             indent = " " * term_len(usage_prefix)
-            self.write(
-                wrap_text(
-                    args,
-                    text_width,
-                    initial_indent=usage_prefix,
-                    subsequent_indent=indent,
+            if args:
+                self.write(
+                    wrap_text(
+                        args,
+                        text_width,
+                        initial_indent=usage_prefix,
+                        subsequent_indent=indent,
+                    )
                 )
-            )
+            else:
+                # When args is empty, still write the usage prefix
+                self.write(usage_prefix.rstrip())
         else:
```