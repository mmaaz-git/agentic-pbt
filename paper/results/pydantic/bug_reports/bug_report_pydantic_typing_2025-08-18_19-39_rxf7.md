# Bug Report: pydantic.typing KeyError on Non-Existent Module Access

**Target**: `pydantic.typing.getattr_migration`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `getattr_migration` function crashes with `KeyError` when accessing attributes from non-existent modules, instead of raising the expected `AttributeError`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pydantic.typing

@given(st.text(min_size=1, max_size=100).filter(lambda x: ':' not in x and '.' not in x))
def test_wrapper_handles_nonexistent_modules(attr_name):
    wrapper = pydantic.typing.getattr_migration('nonexistent.module')
    try:
        wrapper(attr_name)
    except AttributeError:
        pass  # Expected
    except KeyError:
        raise AssertionError("Should raise AttributeError, not KeyError")
```

**Failing input**: `'0'` (or any attribute name)

## Reproducing the Bug

```python
import pydantic.typing

wrapper = pydantic.typing.getattr_migration('nonexistent.module')
wrapper('any_attribute')  # Raises KeyError instead of AttributeError
```

## Why This Is A Bug

The function is designed to handle attribute access and should raise `AttributeError` when an attribute cannot be found, as shown by the last line of the function: `raise AttributeError(f'module {module!r} has no attribute {name!r}')`. However, when the module itself doesn't exist in `sys.modules`, it crashes with `KeyError` instead. This violates the expected behavior and API contract where attribute access errors should be `AttributeError`.

## Fix

```diff
--- a/pydantic/_migration.py
+++ b/pydantic/_migration.py
@@ -300,7 +300,10 @@ def getattr_migration(module: str) -> Callable[[str], Any]:
             )
         if import_path in REMOVED_IN_V2:
             raise PydanticImportError(f'`{import_path}` has been removed in V2.')
-        globals: Dict[str, Any] = sys.modules[module].__dict__
+        if module not in sys.modules:
+            raise AttributeError(f'module {module!r} has no attribute {name!r}')
+        globals: Dict[str, Any] = sys.modules[module].__dict__
         if name in globals:
             return globals[name]
         raise AttributeError(f'module {module!r} has no attribute {name!r}')
```