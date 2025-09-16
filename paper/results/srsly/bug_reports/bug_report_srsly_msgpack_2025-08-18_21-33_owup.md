# Bug Report: srsly.msgpack Integer Overflow on Large Values

**Target**: `srsly.msgpack` / `srsly._msgpack_api.msgpack_dumps`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The msgpack serialization functions in srsly raise OverflowError when attempting to serialize integers outside the range [-2^63, 2^64-1], which are valid Python integers commonly used in cryptographic, scientific, and timestamp applications.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from srsly._msgpack_api import msgpack_dumps, msgpack_loads

@given(st.lists(st.integers(), min_size=1, max_size=10))
@settings(max_examples=500)  
def test_integer_serialization(data):
    """Test that integers in lists survive msgpack serialization."""
    original = {"data": data}
    packed = msgpack_dumps(original)
    unpacked = msgpack_loads(packed, use_list=True)
    assert unpacked["data"] == data
```

**Failing input**: `[18446744073709551616]` (2^64) and `[-9223372036854775809]` (-(2^63)-1)

## Reproducing the Bug

```python
from srsly._msgpack_api import msgpack_dumps

# Case 1: Unsigned overflow
large_unsigned = 2**64  # 18446744073709551616
data1 = {"value": large_unsigned}
msgpack_dumps(data1)  # Raises: OverflowError: Integer value out of range

# Case 2: Negative overflow
large_negative = -(2**63) - 1  # -9223372036854775809
data2 = {"value": large_negative}
msgpack_dumps(data2)  # Raises: OverflowError: Integer value out of range

# Case 3: Common use case - factorial
import math
factorial_25 = math.factorial(25)  # 15511210043330985984000000
data3 = {"factorial": factorial_25}
msgpack_dumps(data3)  # Raises: OverflowError: Integer value out of range
```

## Why This Is A Bug

While the msgpack format specification has inherent integer size limits, the srsly library doesn't handle this limitation gracefully. Python's arbitrary precision integers are commonly used in:
- Cryptographic applications (256-bit hashes as integers)
- Scientific computing (large factorials, combinatorics)  
- High-precision timestamps

The library should either document this limitation prominently, provide automatic fallback to string/bytes encoding for large integers, or raise a more informative error message suggesting workarounds.

## Fix

```diff
--- a/srsly/_msgpack_api.py
+++ b/srsly/_msgpack_api.py
@@ -5,12 +5,29 @@
 from .util import force_path, FilePath, JSONInputBin, JSONOutputBin
 
 
+def _handle_large_int(obj, chain=None):
+    """Handle integers outside msgpack's range by encoding as string."""
+    if isinstance(obj, int):
+        if obj > 2**63-1 or obj < -(2**63):
+            return {"__bigint__": str(obj)}
+    return obj if chain is None else chain(obj)
+
+
 def msgpack_dumps(data: JSONInputBin) -> bytes:
     """Serialize an object to a msgpack byte string.
 
     data: The data to serialize.
     RETURNS (bytes): The serialized bytes.
+    
+    Note: Integers outside the range [-2^63, 2^64-1] will be encoded 
+    as special dictionaries with '__bigint__' key.
     """
-    return msgpack.dumps(data, use_bin_type=True)
+    try:
+        return msgpack.dumps(data, use_bin_type=True)
+    except OverflowError as e:
+        if "Integer value out of range" in str(e):
+            # Retry with large integer handler
+            return msgpack.dumps(data, use_bin_type=True, default=_handle_large_int)
+        raise
```