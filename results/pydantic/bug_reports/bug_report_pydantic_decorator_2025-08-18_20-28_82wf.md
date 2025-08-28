# Bug Report: pydantic.decorator Module Descriptor Attributes Access Failure

**Target**: `pydantic.decorator.getattr_migration`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `getattr_migration` function fails to handle module descriptor attributes like `__dict__`, `__class__`, causing AttributeError when these valid module attributes are accessed through the migration wrapper.

## Property-Based Test

```python
@settings(max_examples=500)
@given(
    attr_name=st.sampled_from(['__dict__', '__class__', '__module__', '__name__', '__doc__', '__annotations__'])
)
def test_dunder_attributes(attr_name):
    """Test behavior with various dunder attributes."""
    fake_module = 'test_dunder_module'
    module = type(sys)(fake_module)
    sys.modules[fake_module] = module
    
    try:
        wrapper = getattr_migration(fake_module)
        result = wrapper(attr_name)
        assert result is not None or result is None
    finally:
        del sys.modules[fake_module]
```

**Failing input**: `attr_name='__dict__'`

## Reproducing the Bug

```python
import sys
from pydantic.decorator import getattr_migration

module_name = 'test_module'
module = type(sys)(module_name)
sys.modules[module_name] = module

print(f"Module has __dict__: {hasattr(module, '__dict__')}")

wrapper = getattr_migration(module_name)

result = wrapper('__dict__')
```

## Why This Is A Bug

Module objects have descriptor attributes like `__dict__` and `__class__` that are valid attributes but not stored in the module's `__dict__`. The `getattr_migration` function only checks `if name in sys.modules[module].__dict__`, missing these descriptor attributes. This violates the expected behavior that the wrapper should handle all valid module attributes that aren't explicitly in the migration dictionaries.

## Fix

```diff
--- a/pydantic/_migration.py
+++ b/pydantic/_migration.py
@@ -302,8 +302,11 @@ def getattr_migration(module: str) -> Callable[[str], Any]:
             )
         if import_path in REMOVED_IN_V2:
             raise PydanticImportError(f'`{import_path}` has been removed in V2.')
-        globals: Dict[str, Any] = sys.modules[module].__dict__
-        if name in globals:
-            return globals[name]
+        module_obj = sys.modules[module]
+        if hasattr(module_obj, name):
+            return getattr(module_obj, name)
         raise AttributeError(f'module {module!r} has no attribute {name!r}')
```