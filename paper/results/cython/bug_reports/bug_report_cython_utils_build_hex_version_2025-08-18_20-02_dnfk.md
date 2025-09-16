# Bug Report: Cython.Utils.build_hex_version Returns String Instead of Integer

**Target**: `Cython.Utils.build_hex_version`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

build_hex_version returns a string representation of hex values instead of an integer, contradicting its documentation which compares it to PY_VERSION_HEX (an integer).

## Property-Based Test

```python
from hypothesis import given, strategies as st
import Cython.Utils as Utils

@given(
    major=st.integers(min_value=0, max_value=99),
    minor=st.integers(min_value=0, max_value=99),
    patch=st.integers(min_value=0, max_value=99)
)
def test_build_hex_version_returns_integer(major, minor, patch):
    version = f"{major}.{minor}.{patch}"
    result = Utils.build_hex_version(version)
    
    # Should return an integer like PY_VERSION_HEX
    assert isinstance(result, int), f"Expected int, got {type(result).__name__}"
```

**Failing input**: Any valid version string, e.g., `"1.2.3"`

## Reproducing the Bug

```python
import Cython.Utils as Utils
import sys

version = "1.2.3"
result = Utils.build_hex_version(version)

print(f"build_hex_version('{version}'):")
print(f"  Result: {result}")
print(f"  Type: {type(result).__name__}")
print(f"  Expected type: int (like sys.hexversion)")
print(f"\nsys.hexversion (PY_VERSION_HEX):")
print(f"  Value: {hex(sys.hexversion)}")
print(f"  Type: {type(sys.hexversion).__name__}")

try:
    comparison = result > 0x010000F0
    print(f"\nCan compare with int: Yes")
except TypeError as e:
    print(f"\nCan compare with int: No - {e}")
```

## Why This Is A Bug

The function's docstring states it returns a value "like PY_VERSION_HEX", which is an integer. However, it actually returns a string. This breaks:

1. Integer comparisons: `result > 0x010000F0` raises TypeError
2. Bitwise operations: `result & 0xFF` raises TypeError  
3. Arithmetic: `result + 1` raises TypeError
4. Any code expecting integer behavior based on the PY_VERSION_HEX comparison

## Fix

The function should return an integer instead of a string representation:

```diff
- return "0x010203F0"  # string
+ return 0x010203F0    # integer
```

Alternatively, if returning a string is intentional, the documentation should be clarified to not compare it with PY_VERSION_HEX.