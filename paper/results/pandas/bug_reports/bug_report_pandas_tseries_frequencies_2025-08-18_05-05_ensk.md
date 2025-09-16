# Bug Report: pandas.tseries.frequencies Incorrect Self-Comparison in Period Functions

**Target**: `pandas.tseries.frequencies.is_subperiod` and `pandas.tseries.frequencies.is_superperiod`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `is_subperiod` and `is_superperiod` functions incorrectly return `True` when comparing certain frequencies with themselves, violating the logical property that a period cannot be both a subperiod and superperiod of itself.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pandas.tseries.frequencies as freq

VALID_FREQ_CODES = ["Y", "Q", "M", "W", "D", "B", "C", "h", "min", "s", "ms", "us", "ns"]
freq_strategy = st.sampled_from(VALID_FREQ_CODES)

@given(source=freq_strategy, target=freq_strategy)
def test_subperiod_superperiod_mutual_exclusion(source, target):
    is_sub = freq.is_subperiod(source, target)
    is_super = freq.is_superperiod(source, target)
    
    if source == target:
        # When frequencies are the same, both should be False
        assert not is_sub and not is_super
    else:
        # Both cannot be True at the same time
        assert not (is_sub and is_super)
```

**Failing input**: `source='Y', target='Y'` (and many others like 'D', 'ns', etc.)

## Reproducing the Bug

```python
import pandas.tseries.frequencies as freq

# Test various frequencies compared with themselves
test_cases = ["Y", "Y-JAN", "D", "h", "min", "s", "ms", "us", "ns"]

for frequency in test_cases:
    is_sub = freq.is_subperiod(frequency, frequency)
    is_super = freq.is_superperiod(frequency, frequency)
    
    if is_sub and is_super:
        print(f"BUG: {frequency} is both subperiod and superperiod of itself")
        print(f"  is_subperiod({frequency}, {frequency}) = {is_sub}")
        print(f"  is_superperiod({frequency}, {frequency}) = {is_super}")
```

## Why This Is A Bug

A frequency period cannot logically be both a subperiod (smaller/finer granularity) and a superperiod (larger/coarser granularity) of itself. The correct behavior when comparing a frequency with itself should be:
- `is_subperiod(X, X)` → `False` (X is not smaller than itself)
- `is_superperiod(X, X)` → `False` (X is not larger than itself)

This violates fundamental logical properties:
1. **Irreflexivity**: A period should not be considered a sub/super-period of itself
2. **Mutual exclusion**: If both functions return True for the same pair, it creates a logical contradiction

## Fix

```diff
--- a/pandas/tseries/frequencies.py
+++ b/pandas/tseries/frequencies.py
@@ -450,6 +450,9 @@ def is_subperiod(source, target) -> bool:
     if target is None or source is None:
         return False
+    # A frequency cannot be a subperiod of itself
+    if source == target:
+        return False
     source = _maybe_coerce_freq(source)
     target = _maybe_coerce_freq(target)
 
@@ -505,6 +508,9 @@ def is_superperiod(source, target) -> bool:
     if target is None or source is None:
         return False
+    # A frequency cannot be a superperiod of itself
+    if source == target:
+        return False
     source = _maybe_coerce_freq(source)
     target = _maybe_coerce_freq(target)
```