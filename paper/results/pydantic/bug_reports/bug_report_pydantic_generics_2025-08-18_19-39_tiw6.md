# Bug Report: pydantic._migration.getattr_migration KeyError on Non-Existent Modules

**Target**: `pydantic._migration.getattr_migration`
**Severity**: Medium  
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `getattr_migration` function crashes with a `KeyError` when the wrapper it returns is called for a module name that doesn't exist in `sys.modules`, instead of raising the expected `AttributeError`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pydantic._migration import getattr_migration
import sys

@given(
    module_name=st.text(min_size=0, max_size=100),
    attr_name=st.text(min_size=1, max_size=100)
)
def test_getattr_migration_handles_nonexistent_modules(module_name, attr_name):
    """Test that getattr_migration handles non-existent modules gracefully."""
    if module_name in sys.modules or attr_name == '__path__':
        return  # Skip existing modules and special case
    
    wrapper = getattr_migration(module_name)
    
    try:
        wrapper(attr_name)
    except AttributeError:
        pass  # Expected behavior
    except KeyError:
        raise AssertionError(f"Got KeyError for module '{module_name}' - should be AttributeError")
```

**Failing input**: `module_name=""`, `attr_name="test"`

## Reproducing the Bug

```python
from pydantic._migration import getattr_migration

wrapper = getattr_migration("")
wrapper("test_attribute")
```

## Why This Is A Bug

The function is expected to raise `AttributeError` for missing attributes, as documented in its behavior and as shown by the error messages it constructs. Instead, it crashes with `KeyError` when trying to access `sys.modules[module].__dict__` for a module that doesn't exist. This violates the principle of consistent error handling and could cause unexpected crashes in code that uses this migration helper.

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