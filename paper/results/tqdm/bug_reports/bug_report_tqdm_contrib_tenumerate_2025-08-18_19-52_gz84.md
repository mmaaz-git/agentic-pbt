# Bug Report: tqdm.contrib.tenumerate Silently Ignores start Parameter for NumPy Arrays

**Target**: `tqdm.contrib.tenumerate`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `start` parameter in `tqdm.contrib.tenumerate` is silently ignored when used with NumPy arrays, causing inconsistent behavior compared to regular iterables.

## Property-Based Test

```python
import numpy as np
from tqdm.contrib import tenumerate
from hypothesis import given, strategies as st

@given(st.integers(min_value=1, max_value=5), 
       st.integers(min_value=1, max_value=5),
       st.integers(min_value=1, max_value=100))
def test_tenumerate_numpy_start_consistency(rows, cols, start):
    """tenumerate should respect start parameter for all input types"""
    # Create numpy array
    arr = np.zeros((rows, cols), dtype=int)
    
    # The start parameter is silently ignored for numpy arrays
    result_with_start = list(tenumerate(arr, start=start))
    
    # Bug: First index should incorporate start value but doesn't
    first_index = result_with_start[0][0]
    assert first_index == (0, 0)  # Always starts at 0, ignoring start parameter
```

**Failing input**: Any numpy array with non-zero start value

## Reproducing the Bug

```python
import numpy as np
from tqdm.contrib import tenumerate

# Regular list - start parameter works
regular_list = [10, 20, 30]
result_list = list(tenumerate(regular_list, start=100))
print(f"List with start=100: {result_list}")
# Output: [(100, 10), (101, 20), (102, 30)]

# NumPy array - start parameter is ignored
numpy_array = np.array([10, 20, 30])
result_array = list(tenumerate(numpy_array, start=100))
print(f"Array with start=100: {result_array}")
# Output: [((0,), 10), ((1,), 20), ((2,), 30)]
# Bug: Indices start at 0, not 100
```

## Why This Is A Bug

The function accepts a `start` parameter that works correctly for regular iterables but is silently ignored for NumPy arrays. This violates the API contract and principle of least surprise. Users expect consistent behavior or an explicit error if the parameter is not supported.

## Fix

The issue occurs because `tenumerate` delegates to `np.ndenumerate` for NumPy arrays, which doesn't support a start parameter. Two possible fixes:

```diff
def tenumerate(iterable, start=0, total=None, tqdm_class=tqdm_auto, **tqdm_kwargs):
    try:
        import numpy as np
    except ImportError:
        pass
    else:
        if isinstance(iterable, np.ndarray):
+           if start != 0:
+               raise ValueError("start parameter is not supported for numpy arrays")
            return tqdm_class(np.ndenumerate(iterable), total=total or iterable.size,
                              **tqdm_kwargs)
    return enumerate(tqdm_class(iterable, total=total, **tqdm_kwargs), start)
```

Or alternatively, implement start offset for numpy arrays:

```diff
def tenumerate(iterable, start=0, total=None, tqdm_class=tqdm_auto, **tqdm_kwargs):
    try:
        import numpy as np
    except ImportError:
        pass
    else:
        if isinstance(iterable, np.ndarray):
+           if start != 0:
+               # Apply start offset to numpy enumeration
+               for idx, val in tqdm_class(np.ndenumerate(iterable), 
+                                          total=total or iterable.size, **tqdm_kwargs):
+                   yield (tuple(i + start for i in idx), val)
+               return
            return tqdm_class(np.ndenumerate(iterable), total=total or iterable.size,
                              **tqdm_kwargs)
    return enumerate(tqdm_class(iterable, total=total, **tqdm_kwargs), start)
```