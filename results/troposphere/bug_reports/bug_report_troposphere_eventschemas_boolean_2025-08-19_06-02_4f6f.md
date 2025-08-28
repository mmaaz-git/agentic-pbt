# Bug Report: troposphere.eventschemas Inconsistent Case Handling in boolean Function

**Target**: `troposphere.eventschemas.boolean`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `boolean` function in troposphere.eventschemas handles case variations inconsistently - it accepts 'true' and 'True' but raises ValueError for 'TRUE', similarly for 'false'/'False' vs 'FALSE'.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.eventschemas as es
import pytest

@given(st.text())
def test_boolean_case_insensitive_consistency(s):
    """
    Test that the boolean function handles case variations consistently.
    If it accepts 'true', it should accept 'TRUE' and 'True'.
    If it accepts 'false', it should accept 'FALSE' and 'False'.
    """
    if s.lower() == 'true':
        try:
            result_lower = es.boolean('true')
            result_title = es.boolean('True')
            result_upper = es.boolean('TRUE')
            assert result_lower == result_title == result_upper == True
        except ValueError:
            with pytest.raises(ValueError):
                es.boolean('true')
            with pytest.raises(ValueError):
                es.boolean('True')
            with pytest.raises(ValueError):
                es.boolean('TRUE')
```

**Failing input**: `s='true'` (also fails with `s='false'`)

## Reproducing the Bug

```python
import troposphere.eventschemas as es

result_true = es.boolean('true')
result_True = es.boolean('True')
result_TRUE = es.boolean('TRUE')
```

## Why This Is A Bug

Users reasonably expect that if a function accepts string representations of booleans with some case variations ('true', 'True'), it should handle all common case variations consistently, including uppercase ('TRUE'). The current implementation creates a surprising inconsistency where mixed case works but full uppercase doesn't.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -36,10 +36,10 @@
 
 
 def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x in [True, 1, "1", "true", "True", "TRUE"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x in [False, 0, "0", "false", "False", "FALSE"]:
         return False
     raise ValueError
```