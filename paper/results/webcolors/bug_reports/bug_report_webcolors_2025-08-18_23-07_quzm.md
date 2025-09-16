# Bug Report: webcolors Scientific Notation in Percent Values

**Target**: `webcolors.rgb_percent_to_rgb`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `rgb_percent_to_rgb` function crashes when processing percentage values in scientific notation without a decimal point (e.g., '5e-324%'), even though CSS supports scientific notation in numeric values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import webcolors

def percent_string(value):
    if value == int(value):
        return f"{int(value)}%"
    return f"{value}%"

valid_rgb_percents = st.tuples(
    st.floats(min_value=0, max_value=100, allow_nan=False).map(percent_string),
    st.floats(min_value=0, max_value=100, allow_nan=False).map(percent_string),
    st.floats(min_value=0, max_value=100, allow_nan=False).map(percent_string)
)

@given(valid_rgb_percents)
def test_percent_to_integer_to_percent_precision(rgb_percent):
    integer_rgb = webcolors.rgb_percent_to_rgb(rgb_percent)
    percent_back = webcolors.rgb_to_rgb_percent(integer_rgb)
```

**Failing input**: `('0%', '0%', '5e-324%')`

## Reproducing the Bug

```python
import webcolors

result = webcolors.rgb_percent_to_rgb(('0%', '0%', '5e-324%'))
```

## Why This Is A Bug

CSS supports scientific notation in numeric values, including percentages. The function fails because the `_normalize_percent_rgb` function in `webcolors/_normalization.py` incorrectly assumes that numeric values without a decimal point are integers. When it encounters '5e-324' (valid scientific notation), it tries to parse it with `int()` which fails, even though this is a valid CSS percentage value that should be treated as a float.

## Fix

```diff
--- a/webcolors/_normalization.py
+++ b/webcolors/_normalization.py
@@ -92,7 +92,11 @@ def _normalize_percent_rgb(value: str) -> str:
 
     """
     value = value.split("%")[0]
-    percent = float(value) if "." in value else int(value)
+    try:
+        percent = int(value)
+    except ValueError:
+        # Handle scientific notation and decimal values
+        percent = float(value)
 
     return "0%" if percent < 0 else "100%" if percent > 100 else f"{percent}%"
```