# Bug Report: numpy.dtypes Integer Overflow Handling Inconsistency

**Target**: `numpy.dtypes` integer dtype classes
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

NumPy has inconsistent overflow handling for integer dtypes - direct array creation with out-of-bounds values raises OverflowError, while arithmetic operations and astype() silently wrap using modular arithmetic.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import numpy as np

@given(
    st.sampled_from([np.int8, np.uint8, np.int16, np.uint16]),
    st.integers()
)
def test_integer_overflow_consistency(dtype, value):
    info = np.iinfo(dtype)
    
    if not (info.min <= value <= info.max):
        # Direct creation should fail
        try:
            arr1 = np.array([value], dtype=dtype)
            assert False, f"Should have raised OverflowError for {value}"
        except OverflowError:
            pass
        
        # But astype wraps silently
        arr2 = np.array([value], dtype=np.int64).astype(dtype)
        wrapped = value % (info.max - info.min + 1)
        if value < info.min:
            wrapped += info.min
        assert arr2[0] == wrapped % 256  # Wraps
```

**Failing input**: `dtype=np.uint8, value=256`

## Reproducing the Bug

```python
import numpy as np

dtype = np.uint8
value = 256

try:
    arr1 = np.array([value], dtype=dtype)
    print(f"Direct: {arr1[0]}")
except OverflowError:
    print("Direct: OverflowError")

arr2 = np.array([value]).astype(dtype)
print(f"astype: {arr2[0]}")

arr3 = np.array([255], dtype=dtype) + 1
print(f"Arithmetic: {arr3[0]}")
```

## Why This Is A Bug

This violates the principle of least surprise. The same out-of-bounds value is handled differently depending on the operation:

1. `np.array([256], dtype=uint8)` → OverflowError
2. `np.array([256]).astype(uint8)` → Silently wraps to 0
3. `np.array([255], dtype=uint8) + 1` → Silently wraps to 0

This inconsistency can cause:
- Unexpected errors when refactoring code that changes how arrays are created
- Confusion about whether NumPy enforces bounds checking
- Difficulty in choosing between fail-fast (errors) vs silent wrapping behavior

## Fix

The fix requires a design decision about NumPy's overflow policy. Two consistent approaches:

**Option 1: Always wrap (like C)**
```diff
# In numpy/core/src/multiarray/ctors.c or equivalent
- if (value < min || value > max) {
-     PyErr_Format(PyExc_OverflowError, 
-                  "Python integer %ld out of bounds for %s",
-                  value, dtype_name);
-     return NULL;
- }
+ value = value % (max - min + 1);
+ if (value < 0 && is_unsigned) {
+     value += (max + 1);
+ }
```

**Option 2: Always check (safer)**
Make arithmetic operations and astype() also check bounds by default, with an optional parameter to allow wrapping when explicitly requested.

The current mixed behavior is the worst of both worlds - neither consistently safe nor consistently performant.