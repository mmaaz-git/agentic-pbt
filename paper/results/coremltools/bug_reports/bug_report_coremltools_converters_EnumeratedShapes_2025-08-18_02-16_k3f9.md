# Bug Report: coremltools.converters EnumeratedShapes IndexError with Different Length Shapes

**Target**: `coremltools.converters.mil.input_types.EnumeratedShapes`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

EnumeratedShapes crashes with IndexError when provided shapes of different lengths, preventing common ML use cases like supporting both 1D and 2D inputs.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from coremltools.converters.mil.input_types import EnumeratedShapes

@given(
    shapes_data=st.lists(
        st.lists(st.integers(min_value=1, max_value=100), min_size=2, max_size=3),
        min_size=2, max_size=4
    )
)  
def test_enumerated_shapes_different_lengths(shapes_data):
    """EnumeratedShapes should handle shapes with different lengths"""
    enum_shapes = EnumeratedShapes(shapes_data)
    assert len(enum_shapes.shapes) == len(shapes_data)
```

**Failing input**: `shapes_data=[[1, 1], [1, 1, 1]]`

## Reproducing the Bug

```python
from coremltools.converters.mil.input_types import EnumeratedShapes

# Minimal reproduction - crashes with IndexError
shapes = [[1], [1, 1]]
enum_shapes = EnumeratedShapes(shapes)

# Real-world example - also crashes
shapes = [(224, 224), (224, 224, 3)]  # Grayscale vs RGB
enum_shapes = EnumeratedShapes(shapes)
```

## Why This Is A Bug

The EnumeratedShapes class is designed to support multiple valid input shapes for ML models. Different length shapes are common (e.g., batch vs single sample, grayscale vs RGB images, 1D vs 2D features). The code crashes because it assumes all shapes have the same number of dimensions, accessing indices beyond the first shape's length when processing longer shapes. This violates the documented purpose of supporting "multiple valid shapes" without any stated restriction on shape lengths.

## Fix

```diff
--- a/coremltools/converters/mil/input_types.py
+++ b/coremltools/converters/mil/input_types.py
@@ -553,11 +553,14 @@ class EnumeratedShapes:
             else:
                 self.shapes.append(Shape(s))
 
-        self.symbolic_shape = self.shapes[0].symbolic_shape
+        # Find the maximum number of dimensions across all shapes
+        max_rank = max(len(shape.symbolic_shape) for shape in self.shapes)
+        # Initialize symbolic_shape with new symbols for all dimensions  
+        self.symbolic_shape = [get_new_symbol() for _ in range(max_rank)]
+        
         for shape in self.shapes:
             for idx, s in enumerate(shape.symbolic_shape):
-                if is_symbolic(self.symbolic_shape[idx]):
-                    continue
+                # idx will never be out of bounds now
                 elif is_symbolic(s):
                     self.symbolic_shape[idx] = s
                 elif s != self.symbolic_shape[idx]:
```