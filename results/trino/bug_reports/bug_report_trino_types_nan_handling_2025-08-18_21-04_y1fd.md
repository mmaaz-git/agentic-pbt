# Bug Report: trino.types TemporalType.round_to() Crashes on NaN

**Target**: `trino.types.TemporalType.round_to()`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The round_to() method in TemporalType crashes with TypeError when given NaN fractional seconds, as it doesn't handle special Decimal values properly.

## Property-Based Test

```python
def test_time_with_nan_fraction():
    from datetime import time
    from decimal import Decimal
    from trino.types import Time
    
    whole_time = time(12, 0, 0)
    nan_fraction = Decimal('NaN')
    
    time_obj = Time(whole_time, nan_fraction)
    rounded = time_obj.round_to(3)  # Crashes here
```

**Failing input**: `Decimal('NaN')` as fractional seconds

## Reproducing the Bug

```python
from datetime import time
from decimal import Decimal
from trino.types import Time

time_obj = Time(time(12, 0, 0), Decimal('NaN'))
time_obj.round_to(3)  # TypeError: bad operand type for abs(): 'str'
```

## Why This Is A Bug

The code assumes `as_tuple().exponent` returns an integer, but for NaN values it returns the string 'n'. The abs() function then fails on this string value. While NaN fractional seconds may not be meaningful, the code should handle this gracefully rather than crashing.

## Fix

```diff
--- a/trino/types.py
+++ b/trino/types.py
@@ -43,7 +43,11 @@ class TemporalType(Generic[PythonTemporalType], metaclass=abc.ABCMeta):
         precision = min(precision, MAX_PYTHON_TEMPORAL_PRECISION_POWER)
         remaining_fractional_seconds = self._remaining_fractional_seconds
         # exponent can return `n`, `N`, `F` too if the value is a NaN for example
-        digits = abs(remaining_fractional_seconds.as_tuple().exponent)  # type: ignore
+        exponent = remaining_fractional_seconds.as_tuple().exponent
+        if isinstance(exponent, str):
+            # Handle special values like NaN, Infinity
+            return self
+        digits = abs(exponent)
         if digits > precision:
             rounding_factor = POWERS_OF_TEN[precision]
             rounded = remaining_fractional_seconds.quantize(Decimal(1 / rounding_factor))
```