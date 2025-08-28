# Bug Report: htmldate.extractors.correct_year Incorrectly Handles Negative Years

**Target**: `htmldate.extractors.correct_year`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `correct_year` function incorrectly converts negative year values to positive years in the 1900s or 2000s range, rather than leaving them unchanged or raising an error.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from htmldate.extractors import correct_year

@given(st.integers())
def test_correct_year_with_any_integer(year):
    """Test correct_year handles any integer input."""
    result = correct_year(year)
    
    # For negative or very large years, should return unchanged
    if year < 0 or year >= 100:
        assert result == year
```

**Failing input**: `year=-1`

## Reproducing the Bug

```python
from htmldate.extractors import correct_year

# Negative years are incorrectly converted to positive years
print(f"correct_year(-1) = {correct_year(-1)}")  # Returns 1999 instead of -1
print(f"correct_year(-50) = {correct_year(-50)}")  # Returns 1950 instead of -50
print(f"correct_year(-99) = {correct_year(-99)}")  # Returns 1901 instead of -99
```

## Why This Is A Bug

The function is designed to convert 2-digit years (0-99) to 4-digit years, but it doesn't validate that the input is non-negative. When given negative values, it applies the same conversion logic, resulting in incorrect positive years. This violates the expected behavior that values outside the 0-99 range should be returned unchanged.

## Fix

```diff
--- a/htmldate/extractors.py
+++ b/htmldate/extractors.py
@@ -247,7 +247,7 @@
 def correct_year(year: int) -> int:
     """Adapt year from YY to YYYY format"""
-    if year < 100:
+    if 0 <= year < 100:
         year += 1900 if year >= 90 else 2000
     return year
```