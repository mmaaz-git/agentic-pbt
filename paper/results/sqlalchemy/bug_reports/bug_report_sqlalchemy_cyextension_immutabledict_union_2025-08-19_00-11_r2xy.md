# Bug Report: sqlalchemy.cyextension.immutabledict Union Returns Same Object

**Target**: `sqlalchemy.cyextension.immutabledict.union()`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `union()` and `merge_with()` methods of immutabledict return the same object instance instead of creating a new one when the result would be identical to one of the inputs.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import sqlalchemy.cyextension.immutabledict as cyi

@given(
    st.dictionaries(st.text(), st.integers()),
    st.dictionaries(st.text(), st.integers())
)
def test_immutabledict_union_creates_new(d1, d2):
    """union() should create a new immutabledict with merged contents."""
    imd1 = cyi.immutabledict(d1)
    imd2 = cyi.immutabledict(d2)
    
    result = imd1.union(imd2)
    
    # Result should be a new immutabledict
    assert isinstance(result, cyi.immutabledict)
    assert result is not imd1
    assert result is not imd2
```

**Failing input**: `d1={}, d2={}`

## Reproducing the Bug

```python
import sqlalchemy.cyextension.immutabledict as cyi

# Create two empty immutabledicts
imd1 = cyi.immutabledict({})
imd2 = cyi.immutabledict({})

# Union should create a new object, but returns the same one
result = imd1.union(imd2)
assert result is imd1  # Should be False, but is True

# Also happens when first dict is non-empty and second is empty
imd3 = cyi.immutabledict({'a': 1})
imd4 = cyi.immutabledict({})
result2 = imd3.union(imd4)
assert result2 is imd3  # Should be False, but is True

# Same issue with merge_with()
result3 = imd1.merge_with(imd2)
assert result3 is imd1  # Should be False, but is True
```

## Why This Is A Bug

Immutable data structures should create new instances for operations like union, even when the result is identical to one of the inputs. This is important for:
1. Consistency - all union operations should behave the same way
2. Identity checks - code may rely on getting a new object
3. Reference tracking - systems that track object references expect new objects from operations

## Fix

The union() and merge_with() methods should always return a new immutabledict instance, even when the contents would be identical to one of the inputs. The optimization of returning the same object breaks the expected contract of immutable data structure operations.