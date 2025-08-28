# Bug Report: trino.types TemporalType.round_to() KeyError on Negative Precision

**Target**: `trino.types.TemporalType.round_to()`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The round_to() method raises KeyError when given negative precision values, as it tries to access non-existent negative indices in the POWERS_OF_TEN dictionary.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from datetime import time
from decimal import Decimal
from trino.types import Time

@given(
    whole_time=st.times(),
    fraction=st.decimals(min_value=Decimal('0'), max_value=Decimal('0.999999'), places=6),
    negative_precision=st.integers(min_value=-10, max_value=-1)
)
def test_time_round_to_negative_precision(whole_time, fraction, negative_precision):
    time_obj = Time(whole_time, fraction)
    rounded = time_obj.round_to(negative_precision)  # Raises KeyError
```

**Failing input**: Any negative integer for precision parameter

## Reproducing the Bug

```python
from datetime import time
from decimal import Decimal
from trino.types import Time

time_obj = Time(time(12, 0, 0), Decimal('0.123456'))
time_obj.round_to(-1)  # KeyError: -1
```

## Why This Is A Bug

The method doesn't validate the precision parameter before using it as a dictionary key. When precision is negative and less than MAX_PYTHON_TEMPORAL_PRECISION_POWER, it remains negative after the min() operation and causes KeyError when accessing POWERS_OF_TEN[precision].

## Fix

```diff
--- a/trino/types.py
+++ b/trino/types.py
@@ -41,7 +41,7 @@ class TemporalType(Generic[PythonTemporalType], metaclass=abc.ABCMeta):
             In case the supplied value exceeds the specified precision,
             the value needs to be rounded.
         """
-        precision = min(precision, MAX_PYTHON_TEMPORAL_PRECISION_POWER)
+        precision = max(0, min(precision, MAX_PYTHON_TEMPORAL_PRECISION_POWER))
         remaining_fractional_seconds = self._remaining_fractional_seconds
         # exponent can return `n`, `N`, `F` too if the value is a NaN for example
         digits = abs(remaining_fractional_seconds.as_tuple().exponent)  # type: ignore
```