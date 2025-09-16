# Bug Report: flask.helpers.get_root_path Raises RuntimeError Instead of Returning CWD

**Target**: `flask.helpers.get_root_path`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `get_root_path` function raises a RuntimeError for built-in modules like 'sys' and 'builtins' instead of returning the current working directory as documented.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import flask.helpers

@given(st.sampled_from(['os', 'sys', 'json', 'math', 'collections', 'itertools']))
def test_get_root_path_existing_modules(module_name):
    """For existing standard library modules, get_root_path should return a valid directory."""
    result = flask.helpers.get_root_path(module_name)
    assert isinstance(result, str)
    assert os.path.isdir(result)
```

**Failing input**: `'sys'`

## Reproducing the Bug

```python
import flask.helpers

result = flask.helpers.get_root_path('sys')
```

Output:
```
RuntimeError: No root path can be found for the provided module 'sys'. This can happen because the module came from an import hook that does not provide file name information or because it's a namespace package. In this case the root path needs to be explicitly provided.
```

## Why This Is A Bug

The function's docstring explicitly states: "Find the root path of a package, or the path that contains a module. **If it cannot be found, returns the current working directory.**"

However, when the function cannot find a root path for built-in modules like 'sys' (which have no `__file__` attribute), it raises a RuntimeError instead of returning `os.getcwd()` as documented.

## Fix

```diff
--- a/flask/helpers.py
+++ b/flask/helpers.py
@@ -607,14 +607,8 @@ def get_root_path(import_name: str) -> str:
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
+            # As documented, return current working directory if path cannot be found
+            return os.getcwd()
 
     # filepath is import_name.py for a module, or __init__.py for a package.
     return os.path.dirname(os.path.abspath(filepath))  # type: ignore[no-any-return]
```