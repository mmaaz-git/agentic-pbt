# Bug Report: troposphere.workspacesthinclient Integer Validator Accepts Fractional Floats

**Target**: `troposphere.workspacesthinclient.integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer()` validation function incorrectly accepts fractional float values (e.g., 0.5, 1.9) when it should only accept whole numbers.

## Property-Based Test

```python
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_float_handling(x):
    """Test integer() correctly handles floats - accepts whole numbers, rejects fractions."""
    is_whole = x == int(x)
    
    if is_whole:
        result = integer(x)
        assert result is x
    else:
        # Should reject fractional floats
        with pytest.raises(ValueError, match="is not a valid integer"):
            integer(x)
```

**Failing input**: `0.5`

## Reproducing the Bug

```python
from troposphere.workspacesthinclient import integer, MaintenanceWindow

# Bug: Fractional floats are accepted as valid integers
print(integer(0.5))   # Returns 0.5 (should raise ValueError)
print(integer(1.9))   # Returns 1.9 (should raise ValueError)
print(integer(-2.7))  # Returns -2.7 (should raise ValueError)

# This leads to accepting invalid time values
mw = MaintenanceWindow(
    Type='CUSTOM',
    StartTimeHour=10.5,   # Accepts fractional hour!
    EndTimeMinute=30.7    # Accepts fractional minute!
)
print(f"StartTimeHour: {mw.StartTimeHour}")  # 10.5
print(f"EndTimeMinute: {mw.EndTimeMinute}")  # 30.7
```

## Why This Is A Bug

The `integer()` function is used to validate that values represent whole numbers (integers), particularly for time fields in MaintenanceWindow (hours and minutes). The current implementation uses `int(x)` to check validity, but `int()` doesn't raise an error for floats - it silently truncates them. This allows fractional values like 10.5 hours or 30.7 minutes to pass validation, which violates the expected integer constraint.

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    try:
        int(x)
+       # Also check that floats are whole numbers
+       if isinstance(x, float) and x != int(x):
+           raise ValueError
    except (ValueError, TypeError):
        raise ValueError("%r is not a valid integer" % x)
    else:
        return x
```