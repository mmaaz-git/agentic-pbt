# Bug Report: pydantic.utils.getattr_migration KeyError on Non-Existent Modules

**Target**: `pydantic.utils.getattr_migration`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `getattr_migration` function raises `KeyError` instead of `AttributeError` when the module name doesn't exist in `sys.modules`.

## Property-Based Test

```python
@given(st.text(min_size=1, max_size=100).filter(lambda x: '\\x00' not in x), 
       st.text(min_size=1, max_size=100).filter(lambda x: '\\x00' not in x and x != '__path__'))
def test_error_message_format(module_name, attr_name):
    """Error messages should have consistent format with proper quoting."""
    import_path = f"{module_name}:{attr_name}"
    
    assume(import_path not in MOVED_IN_V2)
    assume(import_path not in DEPRECATED_MOVED_IN_V2)
    assume(import_path not in REDIRECT_TO_V1)
    assume(import_path not in REMOVED_IN_V2)
    assume(import_path != 'pydantic:BaseSettings')
    
    wrapper = pydantic.utils.getattr_migration(module_name)
    
    if module_name in sys.modules:
        old_module = sys.modules[module_name]
        del sys.modules[module_name]
    else:
        old_module = None
    
    try:
        wrapper(attr_name)
        assert False, "Should have raised AttributeError"
    except AttributeError as e:
        # Expected behavior
        pass
```

**Failing input**: `module_name='0', attr_name='0'`

## Reproducing the Bug

```python
import pydantic.utils

wrapper = pydantic.utils.getattr_migration('0')
try:
    result = wrapper('test_attr')
except KeyError as e:
    print(f"Bug: Got KeyError({e!r}) instead of AttributeError")
```

## Why This Is A Bug

The function is designed to handle attribute access migration for pydantic modules. When a module doesn't exist in `sys.modules`, the expected behavior is to raise `AttributeError` (consistent with Python's normal attribute access behavior), not `KeyError`. The function correctly raises `AttributeError` for other cases (like `__path__` or when the module exists but the attribute doesn't), so this inconsistency breaks the expected error handling contract.

## Fix

```diff
--- a/pydantic/_migration.py
+++ b/pydantic/_migration.py
@@ -300,9 +300,12 @@ def getattr_migration(module: str) -> Callable[[str], Any]:
         if import_path in REMOVED_IN_V2:
             raise PydanticImportError(f'`{import_path}` has been removed in V2.')
-        globals: Dict[str, Any] = sys.modules[module].__dict__
-        if name in globals:
-            return globals[name]
+        if module in sys.modules:
+            globals: Dict[str, Any] = sys.modules[module].__dict__
+            if name in globals:
+                return globals[name]
         raise AttributeError(f'module {module!r} has no attribute {name!r}')
 
     return wrapper
```