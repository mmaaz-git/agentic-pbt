# Bug Report: fire.formatting.WrappedJoin produces empty first line when items exceed width

**Target**: `fire.formatting.WrappedJoin`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

WrappedJoin produces an empty first line when the first item exceeds the specified width, causing incorrect formatting in help text output.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
import fire.formatting as formatting

@given(
    long_item=st.text(min_size=100, max_size=200),
    width=st.integers(min_value=10, max_value=50)
)
def test_wrapped_join_long_item(long_item, width):
    items = [long_item]
    result_lines = formatting.WrappedJoin(items, ' | ', width)
    
    joined = ''.join(result_lines)
    assert long_item in joined, "Long item should still appear in result"
    
    assert long_item in result_lines[0] or result_lines[0] != ''
```

**Failing input**: `long_item='0'*100, width=10`

## Reproducing the Bug

```python
import fire.formatting as formatting

items = ['x' * 100]
width = 10
result_lines = formatting.WrappedJoin(items, ' | ', width)

print(f"Result: {result_lines}")
print(f"First line is empty: {result_lines[0] == ''}")

assert result_lines[0] != '', "First line should not be empty"
```

## Why This Is A Bug

The function incorrectly produces an empty first line when items are longer than the specified width. When processing the final item that exceeds width, it appends the current (empty) line to the results before setting current_line to the item. This creates unwanted empty lines in formatted help text.

## Fix

```diff
--- a/fire/formatting.py
+++ b/fire/formatting.py
@@ -48,7 +48,8 @@ def WrappedJoin(items, separator=' | ', width=80):
     is_final_item = index == len(items) - 1
     if is_final_item:
       if len(current_line) + len(item) <= width:
         current_line += item
       else:
-        lines.append(current_line.rstrip())
+        if current_line:  # Only append non-empty lines
+          lines.append(current_line.rstrip())
         current_line = item
     else:
       if len(current_line) + len(item) + len(separator) <= width:
         current_line += item + separator
       else:
-        lines.append(current_line.rstrip())
+        if current_line:  # Only append non-empty lines
+          lines.append(current_line.rstrip())
         current_line = item + separator
 
   lines.append(current_line)
   return lines
```