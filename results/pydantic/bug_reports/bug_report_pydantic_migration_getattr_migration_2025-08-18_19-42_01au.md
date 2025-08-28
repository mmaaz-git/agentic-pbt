# Bug Report: pydantic._migration.getattr_migration KeyError on Non-existent Modules

**Target**: `pydantic._migration.getattr_migration`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `getattr_migration` function raises `KeyError` instead of `AttributeError` when accessing attributes of non-existent modules, violating Python's expected attribute access behavior.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
import string
from pydantic._migration import getattr_migration, MOVED_IN_V2, DEPRECATED_MOVED_IN_V2, REDIRECT_TO_V1, REMOVED_IN_V2

@given(
    st.text(
        alphabet=string.ascii_letters + string.digits + "_",
        min_size=1,
        max_size=50
    ).filter(lambda s: not s.startswith('_') and s.isidentifier())
)
def test_nonexistent_module_attribute_error(name):
    """Non-existent modules should raise AttributeError, not KeyError."""
    test_module = "pydantic.test_module_xyz"
    test_path = f"{test_module}:{name}"
    
    assume(test_path not in MOVED_IN_V2)
    assume(test_path not in DEPRECATED_MOVED_IN_V2)
    assume(test_path not in REDIRECT_TO_V1)
    assume(test_path not in REMOVED_IN_V2)
    assume(name != '__path__')
    
    wrapper = getattr_migration(test_module)
    
    try:
        wrapper(name)
        assert False, f"Expected AttributeError for non-existent {name}"
    except AttributeError:
        pass  # Expected
    except KeyError as e:
        assert False, f"Got KeyError instead of AttributeError: {e}"
```

**Failing input**: `name='A'` (or any valid identifier)

## Reproducing the Bug

```python
from pydantic._migration import getattr_migration

fake_module = 'pydantic.nonexistent_module'
wrapper = getattr_migration(fake_module)

try:
    wrapper('some_attr')
except KeyError as e:
    print(f"BUG: KeyError raised: {e}")
    print("Expected: AttributeError")
except AttributeError as e:
    print(f"Correct: AttributeError raised: {e}")
```

## Why This Is A Bug

Python's attribute access protocol expects `AttributeError` when an attribute doesn't exist. The current implementation violates this expectation by raising `KeyError` when the module itself doesn't exist in `sys.modules`. This breaks the expected behavior for `__getattr__` handlers and could cause issues in code that relies on proper exception types for attribute access failures.

## Fix

```diff
--- a/pydantic/_migration.py
+++ b/pydantic/_migration.py
@@ -300,7 +300,10 @@ def getattr_migration(module: str) -> Callable[[str], Any]:
             )
         if import_path in REMOVED_IN_V2:
             raise PydanticImportError(f'`{import_path}` has been removed in V2.')
-        globals: Dict[str, Any] = sys.modules[module].__dict__
+        if module in sys.modules:
+            globals: Dict[str, Any] = sys.modules[module].__dict__
+        else:
+            globals = {}
         if name in globals:
             return globals[name]
         raise AttributeError(f'module {module!r} has no attribute {name!r}')
```