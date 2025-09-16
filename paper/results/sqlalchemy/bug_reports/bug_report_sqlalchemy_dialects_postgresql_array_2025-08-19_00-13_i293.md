# Bug Report: sqlalchemy.dialects.postgresql.ARRAY TypeError with FLOAT/NUMERIC Types

**Target**: `sqlalchemy.dialects.postgresql.ARRAY`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

Creating a result_processor for PostgreSQL ARRAY types with FLOAT, NUMERIC, REAL, or DOUBLE_PRECISION item types causes a TypeError when coltype is None.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import psycopg2 as pg_dialect

array_floats = st.lists(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
    min_size=0,
    max_size=100
)

@given(array_floats)
@settings(max_examples=500)
def test_postgresql_array_floats_round_trip(data):
    array_type = postgresql.ARRAY(postgresql.FLOAT)
    dialect = pg_dialect.dialect()
    
    bind_processor = array_type.bind_processor(dialect)
    result_processor = array_type.result_processor(dialect, None)  # Fails here
    
    bound_value = bind_processor(data)
    result_value = result_processor(bound_value)
    
    assert result_value == data
```

**Failing input**: `[]` (or any other value - the test fails during setup, not execution)

## Reproducing the Bug

```python
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import psycopg2

array_type = postgresql.ARRAY(postgresql.FLOAT)
dialect = psycopg2.dialect()

bind_processor = array_type.bind_processor(dialect)
result_processor = array_type.result_processor(dialect, None)
```

## Why This Is A Bug

The code attempts to format None with %d in a string formatting operation, which requires an integer. This happens in _psycopg_common.py when creating a result processor for numeric types within an array. The error occurs regardless of the actual data being processed - it fails during processor creation, preventing any use of FLOAT/NUMERIC/REAL/DOUBLE_PRECISION arrays when coltype is None.

This affects legitimate use cases where users need to process PostgreSQL arrays of floating-point numbers. The bind_processor works correctly, but the result_processor fails to initialize.

## Fix

The issue is in the error message formatting in _psycopg_common.py. When coltype is None, it should either handle this case explicitly or use string formatting that accepts None values:

```diff
- raise exc.InvalidRequestError("Unknown PG numeric type: %d" % coltype)
+ if coltype is None:
+     raise exc.InvalidRequestError("Unknown PG numeric type: None")
+ else:
+     raise exc.InvalidRequestError("Unknown PG numeric type: %d" % coltype)
```

Alternatively, the array processor should handle None coltype values more gracefully for numeric types.