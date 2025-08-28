# Bug Report: fire.formatting.WrappedJoin Strips Trailing Whitespace from Separator

**Target**: `fire.formatting.WrappedJoin`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `WrappedJoin` function incorrectly strips trailing whitespace from separators when wrapping text across multiple lines, changing separators like `' | '` to `' |'`.

## Property-Based Test

```python
@given(st.lists(st.text(min_size=1, max_size=10), min_size=2, max_size=10),
       st.text(min_size=1, max_size=5),
       st.integers(min_value=20, max_value=100))
def test_wrapped_join_separator_preservation(items, separator, width):
    """Separator should be preserved exactly as given."""
    lines = formatting.WrappedJoin(items, separator, width)
    joined = ''.join(lines)
    
    # Count separators in output - should match expected count
    expected_separator_count = len(items) - 1
    
    # For separators with trailing whitespace, check they're preserved
    if separator and separator != separator.rstrip():
        for line in lines[:-1]:  # All but last line
            if line.endswith(separator.rstrip()) and not line.endswith(separator):
                assert False, f"Separator {repr(separator)} was stripped to {repr(separator.rstrip())}"
```

**Failing input**: `items=['foo', 'bar'], separator=' | ', width=8`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
import fire.formatting as fmt

items = ['foo', 'bar', 'baz']
separator = ' | '
width = 10

result = fmt.WrappedJoin(items, separator, width)
print(f"Result: {result}")
print(f"First line: {repr(result[0])}")

assert result[0] == 'foo | ', f"Expected 'foo | ' but got {repr(result[0])}"
```

## Why This Is A Bug

The function is supposed to join items with the exact separator provided. When a separator ends with whitespace (e.g., `' | '`), that whitespace is semantically significant for formatting. Stripping it changes the visual appearance and breaks the contract that the separator should appear unchanged between items.

## Fix

```diff
--- a/formatting.py
+++ b/formatting.py
@@ -50,7 +50,7 @@ def WrappedJoin(items, separator=' | ', width=80):
       if len(current_line) + len(item) <= width:
         current_line += item
       else:
-        lines.append(current_line.rstrip())
+        lines.append(current_line)
         current_line = item
     else:
       if len(current_line) + len(item) + len(separator) <= width:
@@ -56,7 +56,10 @@ def WrappedJoin(items, separator=' | ', width=80):
         current_line += item + separator
       else:
-        lines.append(current_line.rstrip())
+        # Only strip if the line doesn't end with the separator
+        if current_line.endswith(separator):
+          lines.append(current_line[:-len(separator)].rstrip() + separator)
+        else:
+          lines.append(current_line.rstrip())
         current_line = item + separator
 
   lines.append(current_line)
```