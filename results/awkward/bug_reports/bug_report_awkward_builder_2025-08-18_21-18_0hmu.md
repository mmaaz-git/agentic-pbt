# Bug Report: awkward.ArrayBuilder Integer Overflow on Large Python Integers

**Target**: `awkward.builder.ArrayBuilder`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

ArrayBuilder.integer() method crashes with TypeError when given Python integers that exceed the range of signed 64-bit integers (values >= 2^63 or <= -2^63 - 1).

## Property-Based Test

```python
from hypothesis import given, strategies as st
import awkward as ak

@given(values=st.lists(st.integers(), min_size=1, max_size=10))
def test_builder_state_after_snapshot(values):
    """Builder should handle arbitrary Python integers"""
    builder = ak.ArrayBuilder()
    
    for v in values[:len(values)//2]:
        builder.integer(v)
    
    snapshot1 = builder.snapshot()
    
    for v in values[len(values)//2:]:
        builder.integer(v)
    
    snapshot2 = builder.snapshot()
    
    assert snapshot2.to_list() == values
    assert len(snapshot2) == len(values)
```

**Failing input**: `[9223372036854775808]` (which is 2^63)

## Reproducing the Bug

```python
import awkward as ak

builder = ak.ArrayBuilder()

# This works (max int64)
builder.integer(2**63 - 1)

# This fails with TypeError
builder.integer(2**63)
```

## Why This Is A Bug

Python integers have arbitrary precision and the `integer()` method should either:
1. Handle large integers gracefully (convert to float, use BigInt, or similar)
2. Provide a clear error message about the limitation
3. Document the int64 limitation in the method's docstring

Instead, it raises an opaque TypeError about incompatible function arguments from the C++ binding layer, making it difficult for users to understand the limitation.

## Fix

The fix would require modifying the C++ implementation to either:
1. Check integer bounds in Python before passing to C++ and raise a more informative error
2. Support arbitrary precision integers (likely requires significant changes)
3. At minimum, document the limitation clearly

A simple Python-side workaround could be added to check bounds:

```diff
def integer(self, x):
    """
    Appends an integer `x` at the current position in the accumulated
-   array.
+   array. Note: integers must fit within int64 range (-2^63 to 2^63-1).
    """
+   if x > 2**63 - 1 or x < -2**63:
+       raise ValueError(f"Integer {x} exceeds int64 range. Consider using real() for large values.")
    self._layout.integer(x)
```