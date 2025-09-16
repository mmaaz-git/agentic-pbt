# Bug Report: dagster_pandas.constraints Type Checking Failure with Unbounded Ranges

**Target**: `dagster_pandas.constraints.column_range_validation_factory`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `column_range_validation_factory` function incorrectly rejects non-integer values (floats, datetimes) when both min and max bounds are None, due to a type checking bug that defaults to integer type validation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from datetime import datetime, timedelta
from dagster_pandas.constraints import column_range_validation_factory

@given(
    use_min=st.booleans(),
    use_max=st.booleans(),
    days_offset=st.integers(min_value=-365, max_value=365)
)
def test_column_range_validation_datetime(use_min, use_max, days_offset):
    base_date = datetime(2023, 1, 1)
    min_date = base_date if use_min else None
    max_date = base_date + timedelta(days=30) if use_max else None
    test_date = base_date + timedelta(days=days_offset)
    
    validator = column_range_validation_factory(minim=min_date, maxim=max_date)
    result, metadata = validator(test_date)
    
    effective_min = min_date if min_date else datetime.min
    effective_max = max_date if max_date else datetime.max
    
    if effective_min <= test_date <= effective_max:
        assert result == True
    else:
        assert result == False
```

**Failing input**: `use_min=False, use_max=False, days_offset=0`

## Reproducing the Bug

```python
from datetime import datetime
from dagster_pandas.constraints import column_range_validation_factory

validator = column_range_validation_factory(minim=None, maxim=None)
test_datetime = datetime(2023, 1, 1)
result, _ = validator(test_datetime)
print(f"Result: {result}")  # Prints: False (should be True)

test_float = 3.14
result, _ = validator(test_float)
print(f"Result: {result}")  # Prints: False (should be True)
```

## Why This Is A Bug

When both `minim` and `maxim` are None, the function should accept all values of the input type. However, it defaults to integer bounds (`sys.maxsize`) and then performs a type check requiring the value to be of type `int`. This causes valid datetime and float values to be rejected even though they should pass when no bounds are specified.

The validation function checks `isinstance(x, (type(minim), type(maxim)))`, which becomes `isinstance(x, (int, int))` when both bounds default to integer values, causing non-integer types to fail validation.

## Fix

```diff
def column_range_validation_factory(minim=None, maxim=None, ignore_missing_vals=False):
+    # Store original None values to handle type checking correctly
+    original_minim = minim
+    original_maxim = maxim
+    
     if minim is None:
         if isinstance(maxim, datetime):
             minim = datetime.min
         else:
             minim = -1 * (sys.maxsize - 1)
     if maxim is None:
         if isinstance(minim, datetime):
             maxim = datetime.max
         else:
             maxim = sys.maxsize

     def in_range_validation_fn(x):
         if ignore_missing_vals and pd.isnull(x):
             return True, {}
-        return (isinstance(x, (type(minim), type(maxim)))) and (x <= maxim) and (x >= minim), {}
+        # If both bounds were None, skip type checking as we accept all types
+        if original_minim is None and original_maxim is None:
+            # Try to compare with the default bounds, handle type mismatches gracefully
+            try:
+                return (x <= maxim) and (x >= minim), {}
+            except TypeError:
+                # Can't compare, so accept the value
+                return True, {}
+        else:
+            return (isinstance(x, (type(minim), type(maxim)))) and (x <= maxim) and (x >= minim), {}

     in_range_validation_fn.__doc__ = f"checks whether values are between {minim} and {maxim}"
     if ignore_missing_vals:
         in_range_validation_fn.__doc__ += ", ignoring nulls"

     return in_range_validation_fn
```