# Bug Report: numpy.rec.format_parser Whitespace Field Name Stripping

**Target**: `numpy.rec.format_parser`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `format_parser` class strips whitespace from field names, causing different whitespace-only names to become duplicates and making fields inaccessible by their original names.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import numpy.rec as rec

@given(
    st.lists(st.sampled_from(['i4', 'f8', 'S5']), min_size=1, max_size=5),
    st.lists(st.text(min_size=1, max_size=10).filter(lambda x: ',' not in x), min_size=1, max_size=5)
)
def test_format_parser_name_preservation(formats, names):
    """Test that format_parser preserves field names exactly as given"""
    if len(names) > len(formats):
        names = names[:len(formats)]
    
    names = list(dict.fromkeys(names))  # Remove duplicates
    parser = rec.format_parser(formats, names=names, titles=None)
    
    # Property: User-provided names should be preserved (not stripped)
    for i, name in enumerate(names):
        if i < len(parser._names):
            assert parser._names[i] == name  # This fails when name is whitespace
```

**Failing input**: `formats=['i4'], names=[' ']`

## Reproducing the Bug

```python
import numpy.rec as rec

# Case 1: Single whitespace name gets converted to empty string
formats = ['i4']
names = [' ']
parser = rec.format_parser(formats, names=names, titles=None)
assert parser._names[0] == ''  # Should be ' '

# Case 2: Different whitespace names become duplicates
formats = ['i4', 'f8']
names = [' ', '\t']
try:
    parser = rec.format_parser(formats, names=names, titles=None)
except ValueError as e:
    print(f"Error: {e}")  # Duplicate field names: ['']

# Case 3: Field access fails with original name
import numpy as np
arr = np.array([1, 2, 3])
rec_arr = rec.fromarrays([arr], names=[' '])
try:
    value = rec_arr[' ']  # Fails with "ValueError: no field of name  "
except ValueError:
    value = rec_arr['']  # Works, but user didn't provide ''
```

## Why This Is A Bug

This violates the API contract in three ways:

1. **Data Loss**: Different valid field names (' ', '\t', '\n') all become the same empty string after stripping
2. **Unexpected Errors**: Valid, distinct field names raise "Duplicate field names" error after internal processing
3. **Broken Access Pattern**: Users cannot access fields using the names they provided; they must know the internal stripped version

The documentation doesn't specify that whitespace will be stripped from field names, so users reasonably expect their input to be preserved.

## Fix

```diff
--- a/numpy/_core/records.py
+++ b/numpy/_core/records.py
@@ -156,7 +156,10 @@ class format_parser:
             else:
                 raise NameError(f"illegal input names {repr(names)}")
 
-            self._names = [n.strip() for n in names[:self._nfields]]
+            # Only strip whitespace for comma-separated string input
+            if isinstance(names, str):
+                self._names = [n.strip() for n in names[:self._nfields]]
+            else:
+                self._names = list(names[:self._nfields])
         else:
             self._names = []
```

Alternatively, if stripping is intentional for all inputs, the duplicate check should happen before stripping to give a better error message, and the documentation should clearly state this behavior.