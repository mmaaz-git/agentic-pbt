# Bug Report: lml.utils.PythonObjectEncoder Incorrectly Handles Basic Types

**Target**: `lml.utils.PythonObjectEncoder.default`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

PythonObjectEncoder.default() method incorrectly delegates basic types to parent's default() which always raises TypeError, instead of properly handling them.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from lml.utils import PythonObjectEncoder

@given(st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False),
    st.text(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_pythonobjectencoder_basic_types(obj):
    encoder = PythonObjectEncoder()
    result = encoder.default(obj)
    # Should not raise TypeError for basic types
```

**Failing input**: `None`

## Reproducing the Bug

```python
from lml.utils import PythonObjectEncoder

encoder = PythonObjectEncoder()
result = encoder.default(None)
```

## Why This Is A Bug

The PythonObjectEncoder.default() method checks if an object is a basic type (lines 23-24) and then incorrectly calls `JSONEncoder.default(self, obj)` (line 25). However, JSONEncoder.default() is designed to always raise TypeError for any input, as its purpose is to be overridden. This makes the check for basic types pointless since it will always raise an error.

While this doesn't affect normal json_dumps() usage (since JSON handles basic types before calling default()), it's still incorrect logic that could cause issues when:
- The default() method is called directly
- The encoder is subclassed or extended
- During testing or debugging

## Fix

```diff
--- a/lml/utils.py
+++ b/lml/utils.py
@@ -22,7 +22,7 @@ class PythonObjectEncoder(JSONEncoder):
     def default(self, obj):
         a_list_of_types = (list, dict, str, int, float, bool, type(None))
         if isinstance(obj, a_list_of_types):
-            return JSONEncoder.default(self, obj)
+            return obj
         return {"_python_object": str(obj)}
```