# Bug Report: packaging.markers InvalidVersion on Extra Field Comparisons

**Target**: `packaging.markers.Marker`
**Severity**: Medium  
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

Markers comparing the `extra` field with numeric or version-like strings crash with `InvalidVersion` when the extra field is empty (default environment), despite being accepted as valid by the parser.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import packaging.markers
import string

# Strategy for numeric/version-like strings
numeric_strings = st.from_regex(r'[0-9]+(\.[0-9]+)*', fullmatch=True)

@given(numeric_strings)
def test_extra_marker_with_numeric_string(value):
    marker_str = f'extra == "{value}"'
    
    # Parser accepts this as valid
    marker = packaging.markers.Marker(marker_str)
    
    # But evaluation with default environment crashes
    result = marker.evaluate()  # Raises InvalidVersion: Invalid version: ''
```

**Failing input**: `extra == "0"`

## Reproducing the Bug

```python
import packaging.markers

# Parser accepts this marker as valid
marker = packaging.markers.Marker('extra == "0"')

# But evaluation crashes when extra is empty (default)
result = marker.evaluate()  # InvalidVersion: Invalid version: ''
```

## Why This Is A Bug

When the `extra` field is compared with a numeric or version-like string, the library attempts version comparison. In the default environment, `extra` is an empty string, which fails to parse as a version, causing a crash. This is inconsistent behavior - the marker is accepted as valid but fails at evaluation time.

## Fix

The library should handle empty strings gracefully when attempting version comparisons, or avoid version comparison for the `extra` field entirely:

```diff
--- a/packaging/markers.py
+++ b/packaging/markers.py
@@ -185,6 +185,10 @@ def _eval_op(lhs: Any, op: Op, rhs: Any) -> bool:
         try:
             spec = SpecifierSet("".join([op.serialize(), rhs]))
         except InvalidSpecifier:
             pass
         else:
+            # Handle empty strings that can't be parsed as versions
+            if lhs == "":
+                # Treat empty string as incomparable in version context
+                return False
             return spec.contains(lhs, prereleases=True)
```