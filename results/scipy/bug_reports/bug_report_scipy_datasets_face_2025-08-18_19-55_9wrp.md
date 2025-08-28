# Bug Report: scipy.datasets.face() Incorrect Gray Parameter Handling

**Target**: `scipy.datasets.face`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `face()` function only converts to grayscale when `gray=True` is passed, ignoring other truthy values like `gray=1`, violating Python's standard boolean semantics.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import scipy.datasets
import numpy as np

@given(st.integers())
def test_face_gray_parameter_integer_values(gray_value):
    """Test face() with arbitrary integer values for gray parameter."""
    result = scipy.datasets.face(gray=gray_value)
    
    if gray_value:  # Truthy
        assert result.shape == (768, 1024), \
            f"Unexpected shape for gray={gray_value}: {result.shape}"
    else:  # Falsy (0)
        assert result.shape == (768, 1024, 3), \
            f"Unexpected shape for gray={gray_value}: {result.shape}"
```

**Failing input**: `gray_value=1`

## Reproducing the Bug

```python
import scipy.datasets

# Expected: grayscale image (768, 1024)
# Actual: color image (768, 1024, 3)
img = scipy.datasets.face(gray=1)
print(f"gray=1 returns shape: {img.shape}")
print(f"Expected shape: (768, 1024)")

# Only gray=True works correctly
img_true = scipy.datasets.face(gray=True)
print(f"gray=True returns shape: {img_true.shape}")
```

## Why This Is A Bug

The function parameter `gray` is documented as a boolean, but Python convention expects any truthy value to be treated as True. The current implementation uses identity comparison (`is True`) instead of truthiness check, causing unexpected behavior for users passing integer 1, non-empty strings, or other truthy values.

## Fix

```diff
--- a/scipy/datasets/__init__.py
+++ b/scipy/datasets/__init__.py
@@ -156,7 +156,7 @@ def face(gray=False):
     face_data = bz2.decompress(rawdata)
     face = frombuffer(face_data, dtype='uint8')
     face.shape = (768, 1024, 3)
-    if gray is True:
+    if gray:
         face = (0.21 * face[:, :, 0] + 0.71 * face[:, :, 1] +
                 0.07 * face[:, :, 2]).astype('uint8')
     return face
```