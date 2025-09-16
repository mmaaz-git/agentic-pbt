# Bug Report: flask.sansio.scaffold.get_root_path Contract Violation

**Target**: `flask.sansio.scaffold.get_root_path`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `get_root_path` function raises a RuntimeError for built-in modules instead of returning the current working directory as documented.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import flask.sansio.scaffold

existing_modules = st.sampled_from(['os', 'sys', 'json', 'math', 'collections', 'itertools', 'functools'])

@given(existing_modules)
@settings(max_examples=50)
def test_get_root_path_consistency_for_imported_modules(module_name):
    """get_root_path should return the same path consistently for already imported modules."""
    __import__(module_name)
    
    result1 = flask.sansio.scaffold.get_root_path(module_name)
    result2 = flask.sansio.scaffold.get_root_path(module_name)
    
    assert result1 == result2, f"Inconsistent results: {result1} != {result2}"
    assert os.path.exists(result1), f"Path does not exist: {result1}"
```

**Failing input**: `'sys'`

## Reproducing the Bug

```python
import flask.sansio.scaffold

result = flask.sansio.scaffold.get_root_path('sys')
```

## Why This Is A Bug

The function's docstring states: "Find the root path of a package, or the path that contains a module. If it cannot be found, returns the current working directory." However, when given built-in modules like 'sys', 'builtins', 'marshal', or 'gc', the function raises a RuntimeError instead of returning `os.getcwd()` as documented.

## Fix

```diff
--- a/flask/sansio/scaffold.py
+++ b/flask/sansio/scaffold.py
@@ -610,14 +610,7 @@ def get_root_path(import_name: str) -> str:
         # namespace package. In this case pick the root path from the
         # first module that is contained in the package.
         if filepath is None:
-            raise RuntimeError(
-                "No root path can be found for the provided module"
-                f" {import_name!r}. This can happen because the module"
-                " came from an import hook that does not provide file"
-                " name information or because it's a namespace package."
-                " In this case the root path needs to be explicitly"
-                " provided."
-            )
+            return os.getcwd()
 
     # filepath is import_name.py for a module, or __init__.py for a package.
     return os.path.dirname(os.path.abspath(filepath))  # type: ignore[no-any-return]
```