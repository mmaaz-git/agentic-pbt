# Bug Report: simple_history.template_utils ObjDiffDisplay Assertion Error with Small max_length Values

**Target**: `simple_history.template_utils.ObjDiffDisplay`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

ObjDiffDisplay.__init__ raises AssertionError when max_length < 39 with default parameters, preventing users from setting small display limits for historical change diffs.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from simple_history.template_utils import ObjDiffDisplay

@given(st.integers(min_value=10, max_value=200))
def test_objdiffdisplay_accepts_any_positive_max_length(max_length):
    """ObjDiffDisplay should accept any reasonable positive max_length"""
    display = ObjDiffDisplay(max_length=max_length)
    assert display.max_length == max_length
```

**Failing input**: `max_length=10` (or any value < 39)

## Reproducing the Bug

```python
from simple_history.template_utils import ObjDiffDisplay

# This raises AssertionError
display = ObjDiffDisplay(max_length=30)

# The assertion fails because:
# min_diff_len = 30 - (5 + 12 + 5 + 12 + 5) = -9
# assert self.min_diff_len >= 0  # Fails!
```

## Why This Is A Bug

The ObjDiffDisplay class should either:
1. Accept small max_length values and handle them gracefully, or
2. Validate max_length and raise a meaningful ValueError with a clear message

Instead, it crashes with an undocumented AssertionError that provides no guidance to users about the minimum acceptable value.

## Fix

```diff
--- a/simple_history/template_utils.py
+++ b/simple_history/template_utils.py
@@ -183,6 +183,13 @@ class ObjDiffDisplay:
         min_end_len=5,
         min_common_len=5,
     ):
+        min_required_length = (
+            min_begin_len + placeholder_len + min_common_len + 
+            placeholder_len + min_end_len
+        )
+        if max_length < min_required_length:
+            raise ValueError(
+                f"max_length must be at least {min_required_length} with current parameters"
+            )
         self.max_length = max_length
         self.placeholder_len = placeholder_len
         self.min_begin_len = min_begin_len
@@ -194,7 +201,6 @@ class ObjDiffDisplay:
             + placeholder_len
             + min_end_len
         )
-        assert self.min_diff_len >= 0  # nosec
```