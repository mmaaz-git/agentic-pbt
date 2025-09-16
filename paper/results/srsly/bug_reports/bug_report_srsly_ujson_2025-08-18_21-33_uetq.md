# Bug Report: srsly.ujson Integer Overflow on Large Negative Integers

**Target**: `srsly.ujson.dumps`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

ujson.dumps() crashes with OverflowError when encoding integers smaller than -(2^63), while the standard json module handles these values correctly.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import srsly.ujson as ujson

@given(st.integers())
@settings(max_examples=500)
def test_integer_encoding(i):
    """All Python integers should be encodable"""
    encoded = ujson.dumps(i)
    decoded = ujson.loads(encoded)
    assert decoded == i
```

**Failing input**: `-9223372036854775809` (which is -(2^63) - 1)

## Reproducing the Bug

```python
import srsly.ujson as ujson
import json

test_int = -9223372036854775809  # -(2^63) - 1

# ujson fails
try:
    encoded = ujson.dumps(test_int)
except OverflowError as e:
    print(f"ujson ERROR: {e}")

# Standard json works
json_encoded = json.dumps(test_int)
json_decoded = json.loads(json_encoded)
print(f"Standard json handles it: {json_decoded == test_int}")
```

## Why This Is A Bug

The ujson module should be able to handle all valid Python integers that the standard json module can encode. The crash violates the expected behavior of a JSON encoder, which should either encode the value correctly or provide a meaningful way to handle large integers. The error message "can't convert negative int to unsigned" suggests an internal implementation issue with signed/unsigned integer handling.

## Fix

The bug appears to be in the C extension's integer handling logic. The fix would involve:
- Properly handling signed integers beyond the 64-bit signed range
- Either encoding them as strings (like some JSON libraries do) or as floating point numbers
- Ensuring consistency with how positive integers beyond 2^63 are handled