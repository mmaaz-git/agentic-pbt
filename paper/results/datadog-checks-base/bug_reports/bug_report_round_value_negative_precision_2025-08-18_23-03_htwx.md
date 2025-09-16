# Bug Report: round_value Incorrect Handling of Negative Precision

**Target**: `round_value` function from datadog_checks.utils.common
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `round_value` function fails to correctly round numbers when given negative precision values. It should round to multiples of 10^(-precision) but instead returns the original value unchanged.

## Property-Based Test

```python
@given(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    st.integers(min_value=-5, max_value=-1)
)
def test_round_value_negative_precision(value, precision):
    """Test round_value with negative precision (rounding to tens, hundreds, etc.)"""
    result = round_value(value, precision)
    scale = 10 ** (-precision)
    if value != 0:
        remainder = abs(result) % scale
        assert remainder < 1e-9 or abs(remainder - scale) < 1e-9, \
            f"Not properly rounded to scale {scale}: {result}"
```

**Failing input**: `value=1.0, precision=-1`

## Reproducing the Bug

```python
from decimal import ROUND_HALF_UP, Decimal

def round_value(value, precision=0, rounding_method=ROUND_HALF_UP):
    return float(Decimal(str(value)).quantize(Decimal(10) ** -precision, rounding=rounding_method))

result = round_value(1.0, -1)
print(f"Input: 1.0, precision: -1")
print(f"Expected: 0.0 (round to nearest 10)")
print(f"Got: {result}")

result = round_value(15.0, -1)
print(f"Input: 15.0, precision: -1")
print(f"Expected: 20.0 (round to nearest 10)")
print(f"Got: {result}")

result = round_value(149.0, -2)
print(f"Input: 149.0, precision: -2")
print(f"Expected: 100.0 (round to nearest 100)")
print(f"Got: {result}")
```

## Why This Is A Bug

The function's docstring states it rounds a numeric value to specified precision. Negative precision is a standard convention in many rounding functions (e.g., Python's built-in `round()`) where negative values round to tens, hundreds, etc. The current implementation uses `Decimal.quantize()` incorrectly for negative precision values, causing it to fail to round at all.

## Fix

```diff
def round_value(value, precision=0, rounding_method=ROUND_HALF_UP):
    """Round a numeric value to specified precision"""
-   return float(Decimal(str(value)).quantize(Decimal(10) ** -precision, rounding=rounding_method))
+   # For negative precision, use a different approach
+   if precision < 0:
+       scale = 10 ** (-precision)
+       return float(Decimal(str(value / scale)).quantize(Decimal('1'), rounding=rounding_method) * scale)
+   else:
+       return float(Decimal(str(value)).quantize(Decimal(10) ** -precision, rounding=rounding_method))
```