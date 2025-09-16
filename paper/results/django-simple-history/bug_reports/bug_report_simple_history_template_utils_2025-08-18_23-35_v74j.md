# Bug Report: simple_history.template_utils ObjDiffDisplay AssertionError with Small max_length

**Target**: `simple_history.template_utils.ObjDiffDisplay`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

ObjDiffDisplay raises an AssertionError when initialized with max_length < 39 using default parameters, instead of handling small values gracefully or providing a descriptive error.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from simple_history.template_utils import ObjDiffDisplay

@given(st.integers(min_value=10, max_value=1000))
def test_objdiffdisplay_accepts_valid_max_lengths(max_length):
    """ObjDiffDisplay should be constructible with any reasonable max_length."""
    display = ObjDiffDisplay(max_length=max_length)
    assert display.max_length == max_length
```

**Failing input**: `max_length=10` (or any value < 39)

## Reproducing the Bug

```python
from simple_history.template_utils import ObjDiffDisplay

display = ObjDiffDisplay(max_length=30)
```

## Why This Is A Bug

The class uses an assertion to validate internal constraints without considering that users might provide smaller max_length values. With default parameters (min_begin_len=5, placeholder_len=12, min_common_len=5, min_end_len=5), the minimum viable max_length is 39. Values below this trigger an undocumented AssertionError instead of either:
1. Handling small values gracefully by adjusting internal parameters
2. Raising a descriptive ValueError explaining the constraint
3. Documenting the minimum max_length requirement

## Fix

```diff
--- a/simple_history/template_utils.py
+++ b/simple_history/template_utils.py
@@ -194,7 +194,11 @@ class ObjDiffDisplay:
             + placeholder_len
             + min_end_len
         )
-        assert self.min_diff_len >= 0  # nosec
+        if self.min_diff_len < 0:
+            min_required = (min_begin_len + placeholder_len * 2 + 
+                          min_common_len + min_end_len)
+            raise ValueError(f"max_length must be at least {min_required} "
+                           f"with the given parameters (got {max_length})")
 
     def common_shorten_repr(self, *args: Any) -> tuple[str, ...]:
         """
```