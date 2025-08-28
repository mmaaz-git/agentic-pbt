# Bug Report: coremltools.models.datatypes.Array Accepts Invalid Non-Positive Dimensions

**Target**: `coremltools.models.datatypes.Array`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `Array` class in coremltools incorrectly accepts zero and negative dimensions, resulting in arrays with nonsensical properties like negative `num_elements`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from coremltools.models import datatypes

@given(st.lists(st.integers(max_value=0), min_size=1, max_size=5))
def test_array_rejects_non_positive_dimensions(dimensions):
    """Test that Array rejects non-positive dimensions."""
    if any(d <= 0 for d in dimensions):
        with pytest.raises(AssertionError):
            datatypes.Array(*dimensions)
```

**Failing input**: `dimensions=[0]` or `dimensions=[-5]`

## Reproducing the Bug

```python
from coremltools.models import datatypes

# Arrays with invalid dimensions are incorrectly accepted
arr1 = datatypes.Array(0)
print(f"Array(0) has num_elements={arr1.num_elements}")  # 0

arr2 = datatypes.Array(-5)
print(f"Array(-5) has num_elements={arr2.num_elements}")  # -5

arr3 = datatypes.Array(3, 0, 5)
print(f"Array(3,0,5) has num_elements={arr3.num_elements}")  # 0

arr4 = datatypes.Array(-2, -3)
print(f"Array(-2,-3) has num_elements={arr4.num_elements}")  # 6
```

## Why This Is A Bug

Arrays with zero or negative dimensions are mathematically nonsensical. The current implementation only validates that dimensions are integers but fails to check if they are positive. This violates the fundamental property that array dimensions must be positive integers, and leads to arrays with invalid `num_elements` values (zero or negative).

## Fix

```diff
--- a/coremltools/models/datatypes.py
+++ b/coremltools/models/datatypes.py
@@ -79,6 +79,8 @@ class Array(_DatatypeBase):
         """
         assert len(dimensions) >= 1
         assert all(
             isinstance(d, (int, _np.int64, _np.int32)) for d in dimensions
         ), "Dimensions must be ints, not {}".format(str(dimensions))
+        assert all(d > 0 for d in dimensions), \
+            "All dimensions must be positive, got {}".format(dimensions)
         self.dimensions = dimensions
```