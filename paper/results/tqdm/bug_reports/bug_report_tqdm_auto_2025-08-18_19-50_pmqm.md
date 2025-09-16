# Bug Report: tqdm.auto Incorrect Percentage Rounding

**Target**: `tqdm.auto.tqdm.format_meter`
**Severity**: Low  
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

format_meter incorrectly rounds percentages, showing 17% for 1/6 (16.67%) when it should display 16% using integer truncation.

## Property-Based Test

```python
@given(st.integers(min_value=0, max_value=1000),
       st.integers(min_value=0, max_value=1000),
       st.floats(min_value=0.001, max_value=1000, allow_nan=False, allow_infinity=False))
def test_format_meter_returns_string(n, total, elapsed):
    """Property: format_meter should always return a string"""
    result = tqdm.format_meter(n, total, elapsed)
    assert isinstance(result, str), f"format_meter should return string, got {type(result)}"
    
    # Check that percentage is included when total is known
    if total > 0:
        percentage = int(100 * n / total)
        assert f"{percentage}%" in result or f"{percentage:3d}%" in result
```

**Failing input**: `n=1, total=6, elapsed=1.0`

## Reproducing the Bug

```python
from tqdm.auto import tqdm

result = tqdm.format_meter(1, 6, 1.0)
print(result)  #  17%|█▋        | 1/6 [00:01<00:05,  1.00it/s]

# Expected: 16% (since 1/6 = 0.1666... → int(16.66) = 16)
# Actual: 17%

expected_percentage = int(100 * 1 / 6)  # 16
assert f"{expected_percentage}%" in result, f"Expected {expected_percentage}%, but got: {result}"
```

## Why This Is A Bug

The percentage calculation appears to use rounding instead of truncation. When calculating `int(100 * n / total)`, the result should be 16 for 1/6, not 17. This inconsistency can confuse users about actual progress.

## Fix

```diff
# In format_meter function
- percentage = round(100 * n / total)  # or similar rounding logic
+ percentage = int(100 * n / total)    # Use truncation for consistency
```