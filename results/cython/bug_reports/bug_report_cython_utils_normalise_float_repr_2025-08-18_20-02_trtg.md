# Bug Report: Cython.Utils.normalise_float_repr Malformed Output for Small Negative Scientific Notation

**Target**: `Cython.Utils.normalise_float_repr`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

normalise_float_repr produces malformed output for very small negative numbers in scientific notation, placing the minus sign incorrectly in the middle of the decimal representation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import Cython.Utils as Utils

@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_normalise_float_repr_consistent(f):
    repr1 = str(f)
    result1 = Utils.normalise_float_repr(repr1)
    
    # Result should be convertible back to float
    try:
        float(result1.rstrip('.'))
    except ValueError:
        raise AssertionError(f"Invalid float representation: {repr(result1)} from {repr1}")
```

**Failing input**: `-2.2571763014288194e-71`

## Reproducing the Bug

```python
import Cython.Utils as Utils

f = -2.2571763014288194e-71
result = Utils.normalise_float_repr(str(f))
print(f"Input:  {str(f)}")
print(f"Output: {result}")

try:
    float(result.rstrip('.'))
    print("Valid float representation: Yes")
except ValueError:
    print("Valid float representation: No - malformed output")
```

## Why This Is A Bug

The function produces `.000000000000000000000000000000000000000000000000000000000000000000000-22571763014288194` which is not a valid float representation. The minus sign appears in the middle of the number instead of at the beginning. This makes the output unparseable and breaks any code that expects valid float representations.

## Fix

The bug appears to be in the handling of negative numbers in scientific notation when converting to decimal form. The minus sign should be placed at the beginning of the entire number, not embedded within it.

```diff
- .000000000000000000000000000000000000000000000000000000000000000000000-22571763014288194
+ -.000000000000000000000000000000000000000000000000000000000000000000000022571763014288194
```