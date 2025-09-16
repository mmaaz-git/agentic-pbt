# Bug Report: click.formatting.iter_rows Fails to Truncate Rows

**Target**: `click.formatting.iter_rows`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `iter_rows` function fails to truncate rows when `col_count` is less than the actual number of columns in a row, violating the expected contract that all returned rows should have exactly `col_count` columns.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import click.formatting

@given(
    st.lists(
        st.tuples(st.text(), st.text(), st.text()),
        min_size=1
    )
)
def test_iter_rows_should_truncate_to_col_count(rows):
    col_count = 2  # Request 2 columns but rows have 3
    result = list(click.formatting.iter_rows(rows, col_count))
    
    for row in result:
        assert len(row) == col_count
```

**Failing input**: `rows=[('0', '', '')]`

## Reproducing the Bug

```python
import click.formatting

rows = [('col1', 'col2', 'col3')]
col_count = 2

result = list(click.formatting.iter_rows(rows, col_count))

print(f"Input: rows with 3 columns")
print(f"Requested: col_count={col_count}")
print(f"Expected: [('col1', 'col2')]")
print(f"Actual: {result}")
assert len(result[0]) == col_count, f"Row has {len(result[0])} columns instead of {col_count}"
```

## Why This Is A Bug

The function name and parameter `col_count` imply that all returned rows should have exactly that many columns. The current implementation only pads rows with empty strings when they have fewer columns than `col_count`, but fails to truncate rows that have more columns. This asymmetric behavior violates the principle of least surprise and could lead to unexpected results when the function is used with inconsistent data.

## Fix

```diff
--- a/click/formatting.py
+++ b/click/formatting.py
@@ -26,4 +26,4 @@ def iter_rows(
     rows: cabc.Iterable[tuple[str, str]], col_count: int
 ) -> cabc.Iterator[tuple[str, ...]]:
     for row in rows:
-        yield row + ("",) * (col_count - len(row))
+        yield row[:col_count] + ("",) * max(0, col_count - len(row))
```