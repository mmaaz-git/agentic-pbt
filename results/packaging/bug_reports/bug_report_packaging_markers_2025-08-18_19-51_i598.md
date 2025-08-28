# Bug Report: packaging.markers InvalidVersion on Non-Version Field Comparisons

**Target**: `packaging.markers.Marker`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

Markers comparing non-version fields (like `os_name`, `sys_platform`) with version-like strings using comparison operators crash with `InvalidVersion` during evaluation, despite being accepted as valid by the parser.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import packaging.markers
import string

valid_variables = st.sampled_from(['os_name', 'sys_platform', 'platform_system'])
version_strings = st.from_regex(r'[0-9]+(\.[0-9]+)*', fullmatch=True)

@given(valid_variables, version_strings)
def test_non_version_field_comparison(var, version):
    marker_str = f'{var} < "{version}"'
    
    # Parser accepts this as valid
    marker = packaging.markers.Marker(marker_str)
    
    # But evaluation crashes
    result = marker.evaluate()  # Raises InvalidVersion
```

**Failing input**: `os_name < "0"`

## Reproducing the Bug

```python
import packaging.markers

# Parser accepts this marker as valid
marker = packaging.markers.Marker('os_name < "1.0"')

# But evaluation crashes with InvalidVersion
result = marker.evaluate()  # InvalidVersion: Invalid version: 'posix'
```

## Why This Is A Bug

The parser accepts markers that compare non-version fields with version-like strings, but these crash during evaluation when the library tries to parse the actual field value (e.g., "posix") as a version. This violates the principle that syntactically valid markers should be evaluable.

## Fix

The issue occurs because the library attempts version comparison when it detects version-like patterns in the comparison value, regardless of the field being compared. The fix should check if the field is actually a version field before attempting version comparison:

```diff
--- a/packaging/markers.py
+++ b/packaging/markers.py
@@ -185,7 +185,11 @@ def _eval_op(lhs: Any, op: Op, rhs: Any) -> bool:
         try:
             spec = SpecifierSet("".join([op.serialize(), rhs]))
         except InvalidSpecifier:
             pass
         else:
+            # Only use version comparison for version fields
+            if lhs_name not in {"python_version", "python_full_version", 
+                                "implementation_version"}:
+                # Fall back to string comparison for non-version fields
+                return _eval_op(lhs, op, rhs)
             return spec.contains(lhs, prereleases=True)
```