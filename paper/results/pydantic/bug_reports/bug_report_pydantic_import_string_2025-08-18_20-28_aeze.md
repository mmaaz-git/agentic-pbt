# Bug Report: pydantic._internal._validators.import_string Inconsistent Error Handling

**Target**: `pydantic._internal._validators.import_string`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `import_string` function fails to consistently wrap import errors in `PydanticCustomError`, allowing `TypeError` to leak through for relative import paths.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from pydantic._internal._validators import import_string

@given(st.sampled_from(['.', '..', '../', './']))
def test_import_string_error_consistency(import_path):
    """All import errors should be wrapped in PydanticCustomError."""
    try:
        import_string(import_path)
    except Exception as e:
        assert type(e).__name__ == 'PydanticCustomError', \
            f"Expected PydanticCustomError but got {type(e).__name__}"
```

**Failing input**: `'.'`

## Reproducing the Bug

```python
from pydantic._internal._validators import import_string

try:
    import_string('.')
except TypeError as e:
    print(f"Bug: TypeError leaked through instead of PydanticCustomError")
    print(f"Error: {e}")
```

## Why This Is A Bug

The `import_string` function explicitly catches `ImportError` and wraps it in `PydanticCustomError`, but `import_module` can also raise `TypeError` for relative imports without a package context. This violates the function's contract of consistent error handling.

## Fix

```diff
def import_string(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return _import_string_logic(value)
-        except ImportError as e:
+        except (ImportError, TypeError) as e:
            raise PydanticCustomError('import_error', 'Invalid python path: {error}', {'error': str(e)}) from e
    else:
        # otherwise we just return the value and let the next validator do the rest of the work
        return value
```