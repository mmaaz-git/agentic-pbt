# Bug Report: awkward.prettyprint Formatter Ignores Precision for Python Floats

**Target**: `awkward.prettyprint.Formatter`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `Formatter` class in `awkward.prettyprint` ignores the `precision` parameter when formatting Python's built-in `float` type, while correctly applying it to NumPy float types.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import awkward.prettyprint as pp
import numpy as np

@given(
    st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    st.integers(min_value=1, max_value=5)
)
def test_formatter_respects_precision_for_python_floats(value, precision):
    formatter = pp.Formatter(precision=precision)
    
    python_float_result = formatter(value)
    numpy_float_result = formatter(np.float64(value))
    
    max_expected_len = precision + 10
    
    assert len(python_float_result) <= max_expected_len, \
        f"Python float ignores precision setting! Got: {python_float_result}"
```

**Failing input**: `value=0.3333333333333333, precision=1`

## Reproducing the Bug

```python
import awkward.prettyprint as pp
import numpy as np

formatter = pp.Formatter(precision=2)
value = 1/3

python_float = value
numpy_float = np.float64(value)

print(f"Python float: {formatter(python_float)}")
print(f"NumPy float64: {formatter(numpy_float)}")
```

## Why This Is A Bug

The Formatter class accepts a `precision` parameter that should control the number of significant digits in formatted output. The documentation and implementation clearly intend for this to work with all float types. However, Python's built-in `float` type falls through to the default `str` formatter instead of using the precision-aware `_format_real` method, resulting in inconsistent behavior between Python floats and NumPy floats.

## Fix

```diff
--- a/awkward/prettyprint.py
+++ b/awkward/prettyprint.py
@@ -311,7 +311,7 @@ class Formatter:
                 return self._formatters["int"]
             except KeyError:
                 return self._formatters.get("int_kind", str)
-        elif issubclass(cls, (np.float64, np.float32)):
+        elif issubclass(cls, (np.float64, np.float32, float)):
             try:
                 return self._formatters["float"]
             except KeyError:
```