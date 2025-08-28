# Bug Report: fire.test_components.BinaryCanvas Invalid Size Handling

**Target**: `fire.test_components.BinaryCanvas`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

BinaryCanvas constructor accepts invalid sizes (0 and negative values) but methods crash when called on these instances, causing ZeroDivisionError and IndexError exceptions.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import fire.test_components as tc

@given(st.integers(min_value=-10, max_value=10))
def test_binary_canvas_size_handling(size):
    """Test that BinaryCanvas handles all integer sizes gracefully."""
    canvas = tc.BinaryCanvas(size)
    
    try:
        canvas.move(5, 5)
        canvas.on()
        canvas.off()
        canvas.set(1)
        str(canvas)
        canvas.show()
    except (ZeroDivisionError, IndexError) as e:
        raise AssertionError(
            f"BinaryCanvas({size}) was created successfully but methods failed: {e}"
        )
```

**Failing input**: `size=0` and `size=-1`

## Reproducing the Bug

```python
import fire.test_components as tc

# Bug 1: ZeroDivisionError with size=0
canvas1 = tc.BinaryCanvas(0)
canvas1.move(5, 5)  # ZeroDivisionError: integer modulo by zero

# Bug 2: IndexError with negative size  
canvas2 = tc.BinaryCanvas(-1)
canvas2.move(1, 1)  # Succeeds but sets negative indices
canvas2.on()  # IndexError: list index out of range
```

## Why This Is A Bug

The BinaryCanvas constructor accepts any integer size without validation, but the implementation assumes size > 0. This violates the principle that if a constructor accepts a value, all methods should handle it gracefully. The modulo operation in move() crashes with size=0, and negative sizes create empty pixel arrays that cause IndexError when accessed.

## Fix

```diff
--- a/fire/test_components.py
+++ b/fire/test_components.py
@@ -474,6 +474,8 @@ class BinaryCanvas:
   """A canvas with which to make binary art, one bit at a time."""
 
   def __init__(self, size=10):
+    if size <= 0:
+      raise ValueError(f"Canvas size must be positive, got {size}")
     self.pixels = [[0] * size for _ in range(size)]
     self._size = size
     self._row = 0  # The row of the cursor.
```