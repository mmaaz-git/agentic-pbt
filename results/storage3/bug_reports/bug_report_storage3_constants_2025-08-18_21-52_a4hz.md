# Bug Report: storage3.constants Mutable Constants Vulnerability

**Target**: `storage3.constants`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The DEFAULT_SEARCH_OPTIONS and DEFAULT_FILE_OPTIONS in storage3.constants are mutable dictionaries that can be modified at runtime, affecting all code using these "constants" and breaking encapsulation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from storage3.constants import DEFAULT_SEARCH_OPTIONS, DEFAULT_FILE_OPTIONS

@given(
    new_limit=st.integers(),
    new_offset=st.integers()
)
def test_search_options_mutability_bug(new_limit, new_offset):
    """DEFAULT_SEARCH_OPTIONS can be mutated, affecting all code using it."""
    original = dict(DEFAULT_SEARCH_OPTIONS)
    
    DEFAULT_SEARCH_OPTIONS["limit"] = new_limit
    DEFAULT_SEARCH_OPTIONS["offset"] = new_offset
    
    assert DEFAULT_SEARCH_OPTIONS["limit"] == new_limit
    assert DEFAULT_SEARCH_OPTIONS["offset"] == new_offset
    
    from storage3.constants import DEFAULT_SEARCH_OPTIONS as reimported
    assert reimported["limit"] == new_limit
    
    DEFAULT_SEARCH_OPTIONS.clear()
    DEFAULT_SEARCH_OPTIONS.update(original)
```

**Failing input**: Any modification to the dictionary mutates the global constant

## Reproducing the Bug

```python
from storage3.constants import DEFAULT_SEARCH_OPTIONS

admin_options = DEFAULT_SEARCH_OPTIONS
admin_options["limit"] = 10000

from storage3.constants import DEFAULT_SEARCH_OPTIONS as user_defaults
print(f"Expected: 100, Actual: {user_defaults['limit']}")
assert user_defaults["limit"] == 10000
```

## Why This Is A Bug

Constants should be immutable. When code modifies what appears to be a local reference to DEFAULT_SEARCH_OPTIONS or DEFAULT_FILE_OPTIONS, it actually modifies the global constant, affecting all other code using these values. This violates the principle of least surprise and can cause hard-to-debug issues where modifications in one part of an application affect unrelated parts.

## Fix

```diff
--- a/storage3/constants.py
+++ b/storage3/constants.py
@@ -1,14 +1,20 @@
-DEFAULT_SEARCH_OPTIONS = {
-    "limit": 100,
-    "offset": 0,
-    "sortBy": {
-        "column": "name",
-        "order": "asc",
-    },
-}
-DEFAULT_FILE_OPTIONS = {
-    "cache-control": "3600",
-    "content-type": "text/plain;charset=UTF-8",
-    "x-upsert": "false",
-}
+from typing import Dict, Any
+
+def _get_default_search_options() -> Dict[str, Any]:
+    return {
+        "limit": 100,
+        "offset": 0,
+        "sortBy": {
+            "column": "name",
+            "order": "asc",
+        },
+    }
+
+def _get_default_file_options() -> Dict[str, str]:
+    return {
+        "cache-control": "3600",
+        "content-type": "text/plain;charset=UTF-8",
+        "x-upsert": "false",
+    }
+
+DEFAULT_SEARCH_OPTIONS = property(lambda self: _get_default_search_options())
+DEFAULT_FILE_OPTIONS = property(lambda self: _get_default_file_options())
 
 DEFAULT_TIMEOUT = 20
```

Alternative fix using types.MappingProxyType for read-only dictionaries:

```diff
--- a/storage3/constants.py
+++ b/storage3/constants.py
@@ -1,4 +1,6 @@
-DEFAULT_SEARCH_OPTIONS = {
+from types import MappingProxyType
+
+DEFAULT_SEARCH_OPTIONS = MappingProxyType({
     "limit": 100,
     "offset": 0,
     "sortBy": {
@@ -6,11 +8,11 @@
         "order": "asc",
     },
-}
-DEFAULT_FILE_OPTIONS = {
+})
+DEFAULT_FILE_OPTIONS = MappingProxyType({
     "cache-control": "3600",
     "content-type": "text/plain;charset=UTF-8",
     "x-upsert": "false",
-}
+})
 
 DEFAULT_TIMEOUT = 20
```