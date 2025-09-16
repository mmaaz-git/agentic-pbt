# Bug Report: numpy.char Silent Truncation in Case Transformations

**Target**: `numpy.char.upper`, `numpy.char.swapcase`, `numpy.char.capitalize`, `numpy.char.title`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

NumPy char module functions silently truncate results when case transformations produce strings longer than the input array's dtype can hold, leading to data loss without warning.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import numpy as np
import numpy.char as nc

@given(st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=20))
def test_swapcase_involution(texts):
    """swapcase(swapcase(x)) should equal x"""
    arr = np.array(texts, dtype=str)
    swapped_once = nc.swapcase(arr)
    swapped_twice = nc.swapcase(swapped_once)
    assert np.array_equal(arr, swapped_twice)
```

**Failing input**: `['ß']`

## Reproducing the Bug

```python
import numpy as np
import numpy.char as nc

# Demonstrate silent truncation with German eszett
arr = np.array(['ß'])  # Creates dtype '<U1'
upper_result = nc.upper(arr)
print(f"Input: '{arr[0]}' (dtype: {arr.dtype})")
print(f"Expected: 'SS'")
print(f"Actual: '{upper_result[0]}' (dtype: {upper_result.dtype})")

# Demonstrate with ligatures
ligatures = np.array(['ﬀ', 'ﬁ', 'ﬂ'])
upper_ligatures = nc.upper(ligatures)
for i, (orig, result) in enumerate(zip(ligatures, upper_ligatures)):
    expected = orig.upper()
    print(f"'{orig}' -> Expected: '{expected}', Got: '{result}'")

# The bug affects multiple functions
test = np.array(['ß'])
print(f"\nAll affected functions:")
print(f"upper('ß'): '{nc.upper(test)[0]}' (should be 'SS')")
print(f"swapcase('ß'): '{nc.swapcase(test)[0]}' (should be 'SS')")
print(f"capitalize('ß'): '{nc.capitalize(test)[0]}' (should be 'Ss')")
print(f"title('ß'): '{nc.title(test)[0]}' (should be 'Ss')")
```

## Why This Is A Bug

This violates the principle of data integrity. When performing case transformations, the functions should either:
1. Automatically resize the output array dtype to accommodate expanded strings
2. Raise an exception warning about potential truncation
3. Document this limitation clearly

Silent data loss is particularly dangerous as it can corrupt text processing pipelines without any indication of error. The truncation breaks Unicode correctness and the mathematical property that `swapcase(swapcase(x)) = x` for certain characters.

## Fix

The functions should detect when output requires more space and allocate appropriate dtype:

```diff
# Conceptual fix in numpy char case transformation functions
def upper(arr):
    # Current behavior (simplified)
-   result = np.empty_like(arr)
-   for i, s in enumerate(arr):
-       result[i] = s.upper()  # Truncates if too long
    
    # Fixed behavior
+   # First pass: determine maximum output length
+   max_len = 0
+   for s in arr:
+       max_len = max(max_len, len(s.upper()))
+   
+   # Create output array with appropriate dtype
+   result = np.empty(arr.shape, dtype=f'<U{max_len}')
+   for i, s in enumerate(arr):
+       result[i] = s.upper()
    
    return result
```

Alternatively, add a parameter to control truncation behavior:
```python
nc.upper(arr, truncate='error')  # Raise on truncation
nc.upper(arr, truncate='warn')   # Warn on truncation  
nc.upper(arr, truncate='silent')  # Current behavior (default for compatibility)
nc.upper(arr, truncate='resize')  # Auto-resize output dtype
```