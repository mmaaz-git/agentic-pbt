# Bug Report: fire.test_components.VarArgs.cumsums Mutable Reference Bug

**Target**: `fire.test_components.VarArgs.cumsums`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `cumsums` method incorrectly shares the same mutable object across all cumulative results when processing mutable types like lists, causing all elements in the result to be identical references to the final accumulated value.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import fire.test_components as tc

@given(
    lists=st.lists(
        st.lists(st.integers(min_value=-10, max_value=10), min_size=1, max_size=3),
        min_size=2,
        max_size=5
    )
)
def test_varargs_cumsums_list_concatenation(lists):
    """Test that cumsums concatenates lists correctly."""
    va = tc.VarArgs()
    result = va.cumsums(*lists)
    
    expected = []
    accumulated = None
    for lst in lists:
        if accumulated is None:
            accumulated = lst
        else:
            accumulated = accumulated + lst
        expected.append(accumulated)
    
    assert result == expected
```

**Failing input**: `[[0], [0]]`

## Reproducing the Bug

```python
import fire.test_components as tc

va = tc.VarArgs()
result = va.cumsums([1], [2], [3])

print(f"Result: {result}")
print(f"Expected: [[1], [1, 2], [1, 2, 3]]")
print(f"All same object? {result[0] is result[1] is result[2]}")
```

## Why This Is A Bug

The `cumsums` method is supposed to return a list of cumulative sums/accumulations. For mutable types like lists, each element should be a separate object representing the cumulative state at that point. However, the implementation reuses the same mutable object (`total`) and appends it multiple times to the result list. This causes all elements to reference the same object, which gets modified in-place, resulting in all elements having the final accumulated value.

## Fix

```diff
--- a/fire/test_components.py
+++ b/fire/test_components.py
@@ -183,7 +183,10 @@ class VarArgs:
       if total is None:
         total = item
       else:
         total += item
-      sums.append(total)
+      # Create a copy for mutable types to avoid reference sharing
+      import copy
+      sums.append(copy.copy(total))
     return sums
```