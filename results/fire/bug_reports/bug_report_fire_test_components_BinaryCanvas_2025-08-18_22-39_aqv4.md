# Bug Report: fire.test_components.BinaryCanvas Accepts Invalid Sizes

**Target**: `fire.test_components.BinaryCanvas`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

BinaryCanvas constructor accepts negative and zero size values without validation, creating an invalid canvas state that causes crashes when using canvas methods.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import fire.test_components as target

@given(size=st.integers(max_value=0))
def test_binary_canvas_invalid_size_handling(size):
    """Test that BinaryCanvas properly handles invalid sizes."""
    canvas = target.BinaryCanvas(size=size)
    # Canvas accepts invalid size but creates broken state
    if size == 0:
        canvas.move(0, 0)  # Raises ZeroDivisionError
    else:
        canvas.move(0, 0).on()  # Raises IndexError
```

**Failing input**: `size=-1` or `size=0`

## Reproducing the Bug

```python
import fire.test_components as target

# Case 1: Negative size
canvas = target.BinaryCanvas(size=-1)
print(f"Canvas created with size=-1")
print(f"Pixels: {canvas.pixels}")  # Empty list []
canvas.move(0, 0).on()  # IndexError: list index out of range

# Case 2: Zero size  
canvas = target.BinaryCanvas(size=0)
print(f"Canvas created with size=0")
print(f"Pixels: {canvas.pixels}")  # Empty list []
canvas.move(1, 1)  # ZeroDivisionError: integer modulo by zero
```

## Why This Is A Bug

The BinaryCanvas class is described as "A canvas with which to make binary art, one bit at a time." A canvas with negative or zero dimensions is meaningless and violates the expected contract. The constructor should validate that size > 0 to prevent creating an unusable canvas that crashes on basic operations.

## Fix

```diff
class BinaryCanvas:
  """A canvas with which to make binary art, one bit at a time."""

  def __init__(self, size=10):
+   if size <= 0:
+     raise ValueError(f"Canvas size must be positive, got {size}")
    self.pixels = [[0] * size for _ in range(size)]
    self._size = size
    self._row = 0  # The row of the cursor.
    self._col = 0  # The column of the cursor.
```