# Bug Report: sqlalchemy.schema.sort_tables_and_constraints Returns Sets Instead of Lists

**Target**: `sqlalchemy.schema.sort_tables_and_constraints`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `sort_tables_and_constraints` function returns sets instead of lists for the constraints part of its tuple return values, violating its documented interface.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from sqlalchemy import MetaData, Table, Column, Integer
from sqlalchemy.schema import sort_tables_and_constraints

@st.composite
def tables_with_dependencies(draw):
    num_tables = draw(st.integers(min_value=2, max_value=10))
    names = draw(st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10),
        min_size=num_tables,
        max_size=num_tables,
        unique=True
    ))
    
    metadata = MetaData()
    tables = []
    for name in names:
        table = Table(name, metadata,
            Column('id', Integer, primary_key=True)
        )
        tables.append(table)
    return tables

@given(tables_with_dependencies())
def test_sort_tables_and_constraints_returns_lists(tables):
    result = sort_tables_and_constraints(tables)
    
    for table, constraints in result:
        assert isinstance(constraints, list), \
            f"Expected list but got {type(constraints).__name__}"
```

**Failing input**: Any non-empty list of tables, e.g., `[Table('a'), Table('b')]`

## Reproducing the Bug

```python
from sqlalchemy import MetaData, Table, Column, Integer
from sqlalchemy.schema import sort_tables_and_constraints

metadata = MetaData()
table_a = Table('a', metadata, Column('id', Integer, primary_key=True))
table_b = Table('b', metadata, Column('id', Integer, primary_key=True))

result = sort_tables_and_constraints([table_a, table_b])

for table, constraints in result:
    if table is not None:
        print(f"Table {table.name}: constraints type = {type(constraints).__name__}")
        assert isinstance(constraints, list), f"Expected list, got {type(constraints).__name__}"
```

## Why This Is A Bug

The function's docstring explicitly states it returns tuples of `(Table, [ForeignKeyConstraint, ...])` where the square bracket notation indicates a list. However, the function actually returns sets for non-None table entries, violating the documented contract. This inconsistency can break code that expects list-specific operations like indexing or ordering.

## Fix

The issue is in the internal implementation where sets are used for constraint tracking. The fix would be to convert sets to lists before returning:

```diff
def sort_tables_and_constraints(...):
    # ... existing implementation ...
    
    # When building the return value
    for table in tables:
-       yield (table, table_constraints)  # where table_constraints is a set
+       yield (table, list(table_constraints))  # convert set to list
```