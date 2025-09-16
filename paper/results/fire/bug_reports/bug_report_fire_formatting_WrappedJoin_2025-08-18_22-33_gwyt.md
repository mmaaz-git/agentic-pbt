# Bug Report: fire.formatting.WrappedJoin Width Constraint Violation

**Target**: `fire.formatting.WrappedJoin`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `WrappedJoin` function fails to respect the width constraint when individual items are longer than the specified width, violating its documented purpose of wrapping lines at the given width.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from fire import formatting

@given(
    st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=10),
    st.text(min_size=1, max_size=5),
    st.integers(min_value=10, max_value=100)
)
def test_wrapped_join_respects_width(items, separator, width):
    """WrappedJoin should respect the width constraint for each line."""
    lines = formatting.WrappedJoin(items, separator, width)
    
    for line in lines:
        assert len(line) <= width, f"Line '{line}' ({len(line)}) exceeds width {width}"
```

**Failing input**: `items=['00000000000'], separator='0', width=10`

## Reproducing the Bug

```python
from fire import formatting

items = ['00000000000']
width = 10
lines = formatting.WrappedJoin(items, separator=' | ', width=width)

for line in lines:
    if len(line) > width:
        print(f"Line '{line}' has length {len(line)}, exceeds width {width}")
```

## Why This Is A Bug

The function's docstring states it "wraps lines at the given width", but when an individual item exceeds the width, it's included as-is on its own line without any wrapping or truncation. This violates the width constraint that callers expect to be enforced.

## Fix

The function should either:
1. Truncate items that exceed the width (with ellipsis)
2. Break long items across multiple lines
3. Document that items longer than width will not be wrapped

A simple fix for option 1:

```diff
--- a/fire/formatting.py
+++ b/fire/formatting.py
@@ -55,7 +55,10 @@ def WrappedJoin(items, separator=' | ', width=80):
     else:
       if len(current_line) + len(item) + len(separator) <= width:
         current_line += item + separator
       else:
         lines.append(current_line.rstrip())
-        current_line = item + separator
+        if len(item) > width:
+          current_line = EllipsisTruncate(item, width, width) + separator
+        else:
+          current_line = item + separator
```