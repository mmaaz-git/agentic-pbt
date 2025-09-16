# Bug Report: fire.inspectutils Duplicate code in Py3GetFullArgSpec

**Target**: `fire.inspectutils.Py3GetFullArgSpec`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `Py3GetFullArgSpec()` function contains a duplicate line of code that assigns `defaults = ()` twice, which is redundant and potentially confusing.

## Property-Based Test

```python
import fire.inspectutils as inspectutils

def test_duplicate_defaults_assignment():
    """This test verifies the function works despite the duplicate code."""
    def sample_func(a, b=10):
        return a + b
    
    spec = inspectutils.Py3GetFullArgSpec(sample_func)
    # Function works correctly despite duplicate assignment
    assert spec.defaults == (10,)
```

**Failing input**: N/A - This is a code quality issue, not a functional bug

## Reproducing the Bug

```python
# View lines 119-121 of fire/inspectutils.py:
# Line 119: defaults = ()
# Line 120: annotations = {}  
# Line 121: defaults = ()  # <-- Duplicate assignment
```

## Why This Is A Bug

While not causing functional issues, the duplicate assignment of `defaults = ()` on lines 119 and 121 is redundant code that reduces code clarity and maintainability. This appears to be a copy-paste error or merge artifact.

## Fix

```diff
--- a/fire/inspectutils.py
+++ b/fire/inspectutils.py
@@ -118,7 +118,6 @@ def Py3GetFullArgSpec(fn):
   kwonlyargs = []
   defaults = ()
   annotations = {}
-  defaults = ()
   kwdefaults = {}
 
   if sig.return_annotation is not sig.empty:
```