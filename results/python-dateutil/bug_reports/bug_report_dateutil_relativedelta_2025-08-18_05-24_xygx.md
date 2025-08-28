# Bug Report: dateutil.relativedelta Addition Not Associative Due to Normalization

**Target**: `dateutil.relativedelta`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Addition of relativedelta objects is not associative when microseconds overflow due to premature normalization in the _fix() method, causing `(a + b) + c ≠ a + (b + c)`.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from dateutil.relativedelta import relativedelta

@given(
    st.integers(min_value=-999999999, max_value=999999999),
    st.integers(min_value=-999999999, max_value=999999999),
    st.integers(min_value=-999999999, max_value=999999999)
)
@settings(max_examples=500)
def test_addition_associative_microseconds(ms1, ms2, ms3):
    rd1 = relativedelta(microseconds=ms1)
    rd2 = relativedelta(microseconds=ms2)
    rd3 = relativedelta(microseconds=ms3)
    
    left_assoc = (rd1 + rd2) + rd3
    right_assoc = rd1 + (rd2 + rd3)
    
    assert left_assoc == right_assoc
```

**Failing input**: `microseconds=(1, -441891, -558109)` which creates `seconds=(-18, -41)` after partial additions

## Reproducing the Bug

```python
from dateutil.relativedelta import relativedelta

rd1 = relativedelta(microseconds=1)
rd2 = relativedelta(seconds=-18, microseconds=-441891)
rd3 = relativedelta(seconds=-41, microseconds=-558109)

left_assoc = (rd1 + rd2) + rd3
right_assoc = rd1 + (rd2 + rd3)

print(f"(rd1 + rd2) + rd3 = {left_assoc}")
print(f"rd1 + (rd2 + rd3) = {right_assoc}")
print(f"Are they equal? {left_assoc == right_assoc}")
```

## Why This Is A Bug

Mathematical addition should be associative: `(a + b) + c = a + (b + c)`. The bug occurs because:
1. When `rd2 + rd3` is computed first, their microseconds sum to -1000000
2. The _fix() method normalizes this to -1 second and 0 microseconds  
3. When later adding rd1's +1 microsecond, we get -1 minute and +1 microsecond
4. But computing `(rd1 + rd2) + rd3` yields -59 seconds and -999999 microseconds

This violates the fundamental associative property of addition.

## Fix

The issue is that _fix() is called after every addition, causing intermediate normalization. The fix would be to either:
1. Make normalization consistent across different groupings
2. Store raw values and only normalize when needed (e.g., when applying to dates)
3. Use a different representation that maintains associativity

```diff
--- a/dateutil/relativedelta.py
+++ b/dateutil/relativedelta.py
@@ -317,6 +317,8 @@ class relativedelta(object):
     def __add__(self, other):
         if isinstance(other, relativedelta):
+            # Consider accumulating raw values without intermediate normalization
+            # to preserve associativity
             return self.__class__(years=other.years + self.years,
                                  months=other.months + self.months,
                                  days=other.days + self.days,
```