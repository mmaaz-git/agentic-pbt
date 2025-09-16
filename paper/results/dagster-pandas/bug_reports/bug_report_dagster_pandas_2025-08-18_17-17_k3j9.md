# Bug Report: dagster_pandas Range Validation Off-by-One Error with System Minimum

**Target**: `dagster_pandas.constraints.column_range_validation_factory`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `column_range_validation_factory` function incorrectly rejects `-sys.maxsize` when no minimum value is specified, due to an off-by-one error in the default minimum calculation.

## Property-Based Test

```python
import sys as sys_module
from dagster_pandas.constraints import column_range_validation_factory

def test_extreme_numeric_ranges():
    """Test range validation with system max/min values."""
    # Test with no min specified (should use system min)
    validator_no_min = column_range_validation_factory(None, 0)
    result, _ = validator_no_min(-sys_module.maxsize)
    assert result == True, "System min value should pass when no min specified"
```

**Failing input**: `-sys.maxsize` (e.g., `-9223372036854775807`)

## Reproducing the Bug

```python
import sys
from dagster_pandas.constraints import column_range_validation_factory

# Create validator with no minimum specified
validator = column_range_validation_factory(None, 0)

# Test with the actual minimum representable integer
result, _ = validator(-sys.maxsize)
print(f"Validating -sys.maxsize ({-sys.maxsize}): {result}")

# Test with one value higher  
result2, _ = validator(-sys.maxsize + 1)
print(f"Validating -sys.maxsize + 1 ({-sys.maxsize + 1}): {result2}")
```

## Why This Is A Bug

The function sets the default minimum to `-(sys.maxsize - 1)` when no minimum is specified. However, `-sys.maxsize` is a valid integer value that is less than this default minimum. This means the validator incorrectly rejects `-sys.maxsize` even though it should accept all valid integer values when no explicit minimum is provided.

The issue stems from the code at line 719 in constraints.py:
```python
minim = -1 * (sys.maxsize - 1)
```

This evaluates to `-9223372036854775806`, but `-sys.maxsize` is `-9223372036854775807`, which is smaller and thus fails the range check.

## Fix

```diff
--- a/dagster_pandas/constraints.py
+++ b/dagster_pandas/constraints.py
@@ -716,7 +716,7 @@ def column_range_validation_factory(minim=None, maxim=None, ignore_missing_vals
         if isinstance(maxim, datetime):
             minim = datetime.min
         else:
-            minim = -1 * (sys.maxsize - 1)
+            minim = -sys.maxsize - 1
     if maxim is None:
         if isinstance(minim, datetime):
             maxim = datetime.max
```