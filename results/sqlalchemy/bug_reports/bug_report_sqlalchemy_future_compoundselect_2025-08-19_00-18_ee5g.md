# Bug Report: sqlalchemy.future CompoundSelect Cannot Chain Set Operations

**Target**: `sqlalchemy.future.select` 
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `CompoundSelect` object returned by set operations (union, intersect, except_) lacks the methods needed to chain additional set operations, breaking the expected fluent interface pattern.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from sqlalchemy.future import select
from sqlalchemy import column

@given(st.lists(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10), 
                min_size=3, max_size=3, unique=True))
def test_multiple_set_operations_chaining(col_names):
    """Test chaining multiple set operations."""
    c1, c2, c3 = col_names
    
    s1 = select(column(c1))
    s2 = select(column(c2))
    s3 = select(column(c3))
    
    # This should work but fails
    result = s1.union(s2).union(s3)
    assert result is not None
```

**Failing input**: `col_names=['a', 'b', 'c']`

## Reproducing the Bug

```python
from sqlalchemy.future import select
from sqlalchemy import column

s1 = select(column('a'))
s2 = select(column('b'))
s3 = select(column('c'))

union_result = s1.union(s2)
print(f"First union type: {type(union_result).__name__}")

try:
    chained_union = union_result.union(s3)
except AttributeError as e:
    print(f"Error: {e}")
```

## Why This Is A Bug

SQLAlchemy's Select class provides a fluent interface where methods return new objects that can be further chained. Users reasonably expect set operations to follow this pattern: `s1.union(s2).union(s3)`. However, `union()` returns a `CompoundSelect` object that lacks `union()`, `intersect()`, and `except_()` methods, breaking the chain. This violates the principle of least surprise and the established chaining pattern used throughout SQLAlchemy's query builder API.

## Fix

The `CompoundSelect` class should implement the same set operation methods as `Select` to enable chaining. Here's a high-level approach:

1. Add `union()`, `union_all()`, `intersect()`, `intersect_all()`, `except_()`, and `except_all()` methods to `CompoundSelect`
2. These methods should create a new `CompoundSelect` that combines the current compound operation with the new one
3. Ensure proper SQL generation for nested set operations

Workaround: Users can currently pass multiple arguments to a single `union()` call: `s1.union(s2, s3, s4)` or use subqueries for complex cases.