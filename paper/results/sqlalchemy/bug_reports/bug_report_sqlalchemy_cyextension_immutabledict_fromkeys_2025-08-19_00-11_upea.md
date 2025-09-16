# Bug Report: sqlalchemy.cyextension.immutabledict fromkeys() Method Fails

**Target**: `sqlalchemy.cyextension.immutabledict.fromkeys()`
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `fromkeys()` class method of immutabledict raises TypeError instead of creating a new immutabledict with the specified keys and value.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import sqlalchemy.cyextension.immutabledict as cyi

@given(st.lists(st.text(), min_size=1), st.integers())
def test_immutabledict_fromkeys(keys, value):
    """fromkeys() should create new immutabledict."""
    result = cyi.immutabledict.fromkeys(keys, value)
    
    assert isinstance(result, cyi.immutabledict)
    for key in set(keys):
        assert key in result
        assert result[key] == value
```

**Failing input**: `keys=[''], value=0`

## Reproducing the Bug

```python
import sqlalchemy.cyextension.immutabledict as cyi

# fromkeys() should create a new immutabledict, but raises TypeError
try:
    result = cyi.immutabledict.fromkeys(['a', 'b', 'c'], 42)
    print(f"Success: {dict(result)}")
except TypeError as e:
    print(f"Failed: {e}")

# Compare with regular dict which works fine
regular_dict = dict.fromkeys(['a', 'b', 'c'], 42)
print(f"Regular dict works: {regular_dict}")
```

## Why This Is A Bug

The `fromkeys()` method is a standard dict class method that should be supported by immutabledict. Its failure means:
1. Missing standard dictionary functionality
2. Code expecting dict-like interface will break
3. No alternative way to create an immutabledict with multiple keys having the same value

## Fix

The fromkeys() implementation appears to be attempting to modify an immutable object internally. The method should be implemented to directly construct and return a new immutabledict with the specified keys and value, without attempting any mutation operations on an existing immutabledict instance.