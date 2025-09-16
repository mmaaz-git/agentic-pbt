# Bug Report: Cython.Utils normalise_float_repr Produces Malformed Float Strings

**Target**: `Cython.Utils.normalise_float_repr`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The function `normalise_float_repr` produces malformed string representations for negative numbers in scientific notation, creating strings that cannot be parsed back as valid floats.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import Cython.Utils
import math

@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_normalise_float_repr_preserves_value(f):
    """Test that normalise_float_repr preserves the numeric value."""
    float_str = str(f)
    normalized = Cython.Utils.normalise_float_repr(float_str)
    
    # The normalized string should still represent the same float value
    # (within floating point precision)
    denormalized = float(normalized)
    assert math.isclose(f, denormalized, rel_tol=1e-9)
```

**Failing input**: `-5.590134040310381e-170`

## Reproducing the Bug

```python
import Cython.Utils

test_value = -5.590134040310381e-170
float_str = str(test_value)
normalized = Cython.Utils.normalise_float_repr(float_str)
print(normalized)

parsed_back = float(normalized)
```

## Why This Is A Bug

The function is meant to generate a normalized, simple digits string representation of a float value. However, for negative numbers in scientific notation with very small exponents, it produces a malformed string like `.000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000-5590134040310381` which places the negative sign in the middle of the string rather than at the beginning. This violates the fundamental property that a normalized float representation should still be parseable as a valid float.

## Fix

The issue appears to be in how the function handles the negative sign when converting from scientific notation to decimal notation. The negative sign should be placed at the beginning of the entire normalized string, not embedded within it. A proper implementation would handle the sign separately from the mantissa conversion.