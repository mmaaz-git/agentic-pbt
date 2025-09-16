# Bug Report: tabulate String 'True' and 'False' Parsing Error

**Target**: `tabulate.tabulate`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The tabulate library crashes with a ValueError when attempting to format data containing the strings 'True' or 'False' (with capital first letter) in mixed-type columns.

## Property-Based Test

```python
@given(table_data_strategy(), st.sampled_from(TABLE_FORMATS))
def test_consistent_column_alignment(data, fmt):
    """Property: Column alignment should be consistent across rows."""
    assume(len(data) >= 2)
    assume(all(len(row) == len(data[0]) for row in data))
    
    result = tabulate_func(data, tablefmt=fmt)
    # Test continues...
```

**Failing input**: `data=[[0.0], ['True']]`

## Reproducing the Bug

```python
import tabulate

data = [[0.0], ['True']]
result = tabulate.tabulate(data)
```

## Why This Is A Bug

This violates expected behavior because:
1. Mixed-type columns are common in tabular data and should be handled gracefully
2. The strings 'True' and 'False' are valid string values that should be displayed as-is
3. Inconsistent behavior: lowercase 'true'/'false' work fine, only capitalized versions fail
4. The error message "could not convert string to float" reveals an inappropriate type conversion attempt

## Fix

The issue appears to be in the number parsing logic that treats 'True' and 'False' as boolean literals before attempting float conversion. The fix would be to either:
1. Not treat 'True'/'False' strings as special boolean values in mixed-type columns
2. Handle the ValueError gracefully and treat them as strings when float conversion fails

Workaround: Use `disable_numparse=True` parameter to bypass the problematic parsing logic.