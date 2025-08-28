# Bug Report: numpy.ma.compress Incorrectly Handles Masked Conditions

**Target**: `numpy.ma.compress`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `ma.compress` function incorrectly includes masked elements in its output when the condition array is a masked array with masked values. These masked condition values should be treated as False and excluded from the result.

## Property-Based Test

```python
import numpy.ma as ma
import numpy as np
from hypothesis import given, strategies as st

@given(st.lists(st.integers(), min_size=1, max_size=10),
       st.lists(st.booleans(), min_size=1, max_size=10))
def test_compress_with_masked_condition(data, mask):
    min_len = min(len(data), len(mask))
    data = data[:min_len]
    mask = mask[:min_len]
    
    arr = ma.array(data, mask=mask)
    condition = arr > np.median(data)  # Creates masked condition
    
    result = ma.compress(condition, arr)
    
    # Result should only include elements where condition is True AND not masked
    for val in result:
        assert not ma.is_masked(val), "Result should not contain masked values from masked conditions"
```

**Failing input**: `arr = ma.array([1, 2, 3, 4, 5], mask=[0, 0, 1, 0, 0])`, `condition = arr > 2`

## Reproducing the Bug

```python
import numpy.ma as ma

arr = ma.array([1, 2, 3, 4, 5], mask=[0, 0, 1, 0, 0])
condition = arr > 2  # Results in [False, False, --, True, True]

result = ma.compress(condition, arr)

print(f"Array: {arr}")
print(f"Condition: {condition}")
print(f"Result: {result}")
print(f"Result list: {list(result)}")

# Expected: [4, 5] (only unmasked True conditions)
# Actual: [masked, 4, 5] (incorrectly includes masked condition position)
```

## Why This Is A Bug

When using `ma.compress` with a masked condition array, masked values in the condition should be treated as False and excluded from the result. The current implementation incorrectly includes elements at positions where the condition is masked, adding them as masked values to the output. This violates the principle that uncertain/unknown conditions (masked values) should not select elements.

The correct behavior is demonstrated when using a regular numpy array as the condition:
- `ma.compress(np.array([False, False, False, True, True]), arr)` correctly returns `[4, 5]`
- `ma.compress(ma.array([False, False, ma.masked, True, True]), arr)` incorrectly returns `[masked, 4, 5]`

## Fix

The issue appears to be in how `ma.compress` handles masked values in the condition array. The fix would involve treating masked condition values as False:

```diff
# In numpy/ma/core.py, in the compress function
def compress(condition, a, axis=None, out=None):
    # ... existing code ...
    
+   # If condition is a masked array, treat masked values as False
+   if isinstance(condition, MaskedArray):
+       condition = condition.filled(False)
    
    # ... rest of the function ...
```