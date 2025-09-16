# Bug Report: awkward.mask Fails on Empty Arrays from Python Lists

**Target**: `awkward.mask`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `ak.mask` function raises a ValueError when both the array and mask are empty arrays created from Python lists, even though this is a logically valid operation.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import awkward as ak

@given(st.lists(st.integers(-1000, 1000), min_size=0, max_size=50),
       st.lists(st.booleans(), min_size=0, max_size=50))
@settings(max_examples=100)
def test_mask_is_none_consistency(arr_data, mask_data):
    """Elements that are masked should be detected as None by is_none."""
    arr = ak.Array(arr_data)
    
    # Make mask same length as array
    if len(mask_data) < len(arr):
        mask_data = mask_data + [False] * (len(arr) - len(mask_data))
    elif len(mask_data) > len(arr):
        mask_data = mask_data[:len(arr)]
    
    mask = ak.Array(mask_data)
    
    # Apply mask (valid_when=False means True in mask creates None)
    masked = ak.mask(arr, mask, valid_when=False)
    
    # Check with is_none
    none_mask = ak.is_none(masked, axis=0)
    
    # The none_mask should match our original mask
    assert ak.all(none_mask == mask), "is_none doesn't match the mask applied"
```

**Failing input**: `arr_data=[], mask_data=[]`

## Reproducing the Bug

```python
import awkward as ak

# Create empty arrays from Python lists
empty_data = ak.Array([])
empty_mask = ak.Array([])

# This fails with ValueError
result = ak.mask(empty_data, empty_mask, valid_when=False)
```

## Why This Is A Bug

The `ak.mask` function should accept any boolean array as a mask that has the same length as the data array. When both arrays are empty (length 0), this condition is satisfied. However, the function fails because:

1. Empty arrays created from Python lists get type `0 * unknown`
2. This unknown type is internally interpreted as `dtype('float64')`
3. The mask function strictly requires boolean dtype, rejecting the empty array
4. This is overly strict type checking for a logically valid edge case

## Fix

```diff
--- a/awkward/operations/ak_mask.py
+++ b/awkward/operations/ak_mask.py
@@ -109,6 +109,10 @@ def _impl(array, mask, valid_when, highlevel, behavior, attrs):
     def action(inputs, backend, **kwargs):
         layoutarray, layoutmask = inputs
         if layoutmask.is_numpy:
+            # Handle empty arrays gracefully
+            if len(layoutmask) == 0 and len(layoutarray) == 0:
+                # Both empty, type doesn't matter
+                m = backend.nplike.asarray([], dtype=np.bool_)
             m = backend.nplike.asarray(layoutmask.data)
             if not issubclass(m.dtype.type, (bool, np.bool_)):
                 raise ValueError(f"mask must have boolean type, not {m.dtype!r}")
```