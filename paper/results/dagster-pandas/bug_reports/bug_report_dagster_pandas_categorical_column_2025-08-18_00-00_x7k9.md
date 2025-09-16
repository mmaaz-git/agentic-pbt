# Bug Report: dagster_pandas.validation.PandasColumn.categorical_column Type Mismatch

**Target**: `dagster_pandas.validation.PandasColumn.categorical_column`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `PandasColumn.categorical_column()` method documentation specifies it accepts a list for the `categories` parameter, but the implementation fails when a list is provided, requiring a set instead.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from dagster_pandas.validation import PandasColumn
import pandas as pd

@given(
    categories=st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=3, unique=True),
)
def test_categorical_column_accepts_list(categories):
    """Test that categorical_column accepts a list as documented."""
    df = pd.DataFrame({'test_col': categories})
    
    # According to docstring, categories should accept List[Any]
    cat_col = PandasColumn.categorical_column(
        name='test_col',
        categories=categories,  # Passing list as documented
        non_nullable=False
    )
    cat_col.validate(df)
```

**Failing input**: `categories=['0']`

## Reproducing the Bug

```python
import pandas as pd
from dagster_pandas.validation import PandasColumn

df = pd.DataFrame({'category_col': ['A', 'B', 'A', 'C']})

cat_col = PandasColumn.categorical_column(
    name='category_col',
    categories=['A', 'B', 'C'],  # List as per documentation
    non_nullable=False
)

cat_col.validate(df)
```

## Why This Is A Bug

The method's docstring at line 343 in validation.py clearly states:
```
categories (List[Any]): The valid set of buckets that all values in the column must match.
```

However, the implementation at line 364 passes the categories directly to `CategoricalColumnConstraint`, which expects a set parameter (constraints.py line 986), causing a `ParameterCheckError`.

## Fix

```diff
--- a/dagster_pandas/validation.py
+++ b/dagster_pandas/validation.py
@@ -361,7 +361,7 @@ class PandasColumn:
             name=check.str_param(name, "name"),
             constraints=[
                 ColumnDTypeInSetConstraint(of_types),
-                CategoricalColumnConstraint(categories, ignore_missing_vals=ignore_missing_vals),
+                CategoricalColumnConstraint(set(categories), ignore_missing_vals=ignore_missing_vals),
             ]
             + _construct_keyword_constraints(
                 non_nullable=non_nullable, unique=unique, ignore_missing_vals=ignore_missing_vals
```