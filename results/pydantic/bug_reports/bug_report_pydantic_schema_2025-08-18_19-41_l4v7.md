# Bug Report: pydantic.schema KeyError on Nonexistent Module Access

**Target**: `pydantic.schema.getattr_migration`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `getattr_migration` function crashes with `KeyError` when accessing attributes on a module that doesn't exist in `sys.modules`, instead of raising the expected `AttributeError`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import sys
import pytest
from pydantic.schema import getattr_migration

@given(
    module_name=st.text(min_size=1, max_size=100).filter(lambda x: x not in sys.modules)
)
def test_nonexistent_module_behavior(module_name):
    """Test behavior when module doesn't exist in sys.modules."""
    assume(':' not in module_name)
    
    wrapper = getattr_migration(module_name)
    
    # Should raise AttributeError for non-special attributes
    with pytest.raises(AttributeError) as exc_info:
        wrapper('some_random_attr')
    
    error_msg = str(exc_info.value)
    assert 'some_random_attr' in error_msg or repr('some_random_attr') in error_msg
```

**Failing input**: `module_name='0'` (or any module name not in `sys.modules`)

## Reproducing the Bug

```python
from pydantic.schema import getattr_migration

# Create wrapper for a module that doesn't exist
wrapper = getattr_migration('nonexistent_module')

# This raises KeyError instead of AttributeError
wrapper('some_attribute')  # KeyError: 'nonexistent_module'
```

## Why This Is A Bug

The function should gracefully handle the case where a module doesn't exist in `sys.modules` by raising an `AttributeError` with a descriptive message, as it does for other error cases. Instead, it crashes with an unhandled `KeyError`, which violates the expected behavior documented in the function that it should "raise an error if the object is not found" - specifically an `AttributeError` as shown by other code paths.

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