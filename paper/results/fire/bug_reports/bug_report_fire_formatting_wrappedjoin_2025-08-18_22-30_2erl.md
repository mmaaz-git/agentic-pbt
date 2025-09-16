# Bug Report: fire.formatting.WrappedJoin Exceeds Width Limit

**Target**: `fire.formatting.WrappedJoin`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

WrappedJoin produces lines that exceed the specified width limit when an individual item is longer than the width.

## Property-Based Test

```python
@given(st.lists(st.text(min_size=1, max_size=20), min_size=1),
       st.text(min_size=1, max_size=5),
       st.integers(min_value=10, max_value=100))
def test_wrapped_join_respects_width(items, separator, width):
    """No line should exceed the specified width."""
    lines = formatting.WrappedJoin(items, separator, width)
    for line in lines:
        assert len(line) <= width
```

**Failing input**: `items=['00000000000', '0'], separator='0', width=10`

## Reproducing the Bug

```python
import fire.formatting as fmt

items = ['00000000000', '0']
separator = '0'
width = 10
lines = fmt.WrappedJoin(items, separator, width)

for i, line in enumerate(lines):
    print(f'Line {i}: "{line}" (len={len(line)})')

assert all(len(line) <= width for line in lines), "Lines exceed width limit"
```

## Why This Is A Bug

The function's docstring states it "wraps lines at the given width", but when an item doesn't fit on the current line, it creates a new line with `item + separator` without checking if this exceeds the width limit. Line 1 outputs "000000000000" which is 12 characters, exceeding the width of 10.

## Fix

```diff
--- a/fire/formatting.py
+++ b/fire/formatting.py
@@ -55,10 +55,14 @@ def WrappedJoin(items, separator=' | ', width=80):
     else:
       if len(current_line) + len(item) + len(separator) <= width:
         current_line += item + separator
       else:
         lines.append(current_line.rstrip())
-        current_line = item + separator
+        # Don't add separator if item alone exceeds width
+        if len(item) >= width:
+          current_line = item
+        else:
+          current_line = item + separator
 
   lines.append(current_line)
   return lines
```