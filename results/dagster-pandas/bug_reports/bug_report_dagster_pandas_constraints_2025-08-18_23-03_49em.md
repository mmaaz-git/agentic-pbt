# Bug Report: StrictColumnsConstraint Fails to Detect Missing Columns

**Target**: `dagster_pandas.constraints.StrictColumnsConstraint`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

StrictColumnsConstraint with `enforce_ordering=False` fails to detect when required columns are missing from a DataFrame, only checking that present columns are in the allowed list.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pandas as pd
from dagster_pandas.constraints import StrictColumnsConstraint

@given(
    required_cols=st.lists(st.text(min_size=1, max_size=5), min_size=3, max_size=5, unique=True),
    subset_size=st.integers(min_value=1, max_value=2)
)
def test_strict_columns_missing_detection(required_cols, subset_size):
    """Test that StrictColumnsConstraint detects missing columns."""
    subset_size = min(subset_size, len(required_cols) - 1)
    present_cols = required_cols[:subset_size]
    
    constraint = StrictColumnsConstraint(required_cols, enforce_ordering=False)
    df = pd.DataFrame(columns=present_cols)
    
    # Should raise exception for missing columns
    try:
        constraint.validate(df)
        assert False, f"Should detect missing columns: {set(required_cols) - set(present_cols)}"
    except DataFrameConstraintViolationException:
        pass  # Expected
```

**Failing input**: `required_cols=['a', 'b', 'c']`, `df.columns=['a', 'b']`

## Reproducing the Bug

```python
import pandas as pd
from dagster_pandas.constraints import StrictColumnsConstraint

constraint = StrictColumnsConstraint(['a', 'b', 'c'], enforce_ordering=False)
df = pd.DataFrame(columns=['a', 'b'])

constraint.validate(df)
print("Bug: validation passed despite missing column 'c'")
```

## Why This Is A Bug

The StrictColumnsConstraint class is designed to enforce that a DataFrame has exactly the specified columns. The docstring states "No columns outside of {strict_column_list} allowed", implying the DataFrame should have exactly those columns, not a subset. When `enforce_ordering=False`, the constraint should still verify all required columns are present, just not their order. Currently, it only validates that present columns are in the allowed list, missing the check for completeness.

## Fix

```diff
--- a/dagster_pandas/constraints.py
+++ b/dagster_pandas/constraints.py
@@ -326,11 +326,18 @@ class StrictColumnsConstraint(DataFrameConstraint):
                         f" {columns_received}"
                     ),
                 )
-        for column in columns_received:
-            if column not in self.strict_column_list:
-                raise DataFrameConstraintViolationException(
-                    constraint_name=self.name,
-                    constraint_description=f"Expected {self.strict_column_list}. Recevied {columns_received}.",
-                )
+        else:
+            # Check no extra columns
+            for column in columns_received:
+                if column not in self.strict_column_list:
+                    raise DataFrameConstraintViolationException(
+                        constraint_name=self.name,
+                        constraint_description=f"Expected {self.strict_column_list}. Recevied {columns_received}.",
+                    )
+            # Check no missing columns
+            if set(self.strict_column_list) != set(columns_received):
+                raise DataFrameConstraintViolationException(
+                    constraint_name=self.name,
+                    constraint_description=f"Expected {self.strict_column_list}. Recevied {columns_received}.",
+                )
```