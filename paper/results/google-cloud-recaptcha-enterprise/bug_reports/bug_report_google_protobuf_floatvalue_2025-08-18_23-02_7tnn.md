# Bug Report: google.protobuf.wrappers_pb2.FloatValue JSON Round-trip Failure at Float32 Maximum

**Target**: `google.protobuf.json_format` with `wrappers_pb2.FloatValue`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

FloatValue messages containing the maximum float32 value fail to round-trip through JSON serialization, violating the expected property that `Parse(MessageToJson(msg))` should reconstruct the original message.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from google.protobuf import json_format, wrappers_pb2
import math

@given(st.floats(min_value=3.4e38, max_value=3.5e38, allow_nan=False, allow_infinity=False))
def test_json_roundtrip_float_boundary(value):
    msg = wrappers_pb2.FloatValue()
    msg.value = value
    
    if math.isinf(msg.value):
        return
    
    json_str = json_format.MessageToJson(msg)
    parsed_msg = wrappers_pb2.FloatValue()
    json_format.Parse(json_str, parsed_msg)
    
    assert math.isclose(msg.value, parsed_msg.value, rel_tol=1e-6, abs_tol=1e-9)
```

**Failing input**: `value=3.402823364973241e+38`

## Reproducing the Bug

```python
from google.protobuf import json_format, wrappers_pb2

value = 3.402823364973241e+38

msg = wrappers_pb2.FloatValue()
msg.value = value

json_str = json_format.MessageToJson(msg)
print(f"Stored value: {msg.value}")  
print(f"JSON: {json_str}")

parsed_msg = wrappers_pb2.FloatValue()
json_format.Parse(json_str, parsed_msg)
```

## Why This Is A Bug

The FloatValue message type uses 32-bit floats internally. When the maximum float32 value (3.4028234663852886e+38) is serialized to JSON, it gets rounded to "3.4028235e+38" due to formatting precision. However, when parsing this rounded value back, the JSON parser rejects it with "Float value too large" because 3.4028235e+38 exceeds the maximum representable float32 value.

This violates the round-trip property that messages should be reconstructable from their JSON representation. The serializer produces JSON that the parser cannot consume.

## Fix

The issue lies in the float serialization precision and parsing validation. The serializer should either:
1. Use sufficient precision to ensure the rounded value remains within float32 bounds
2. Or the parser should be more lenient and clamp values at the float32 maximum rather than rejecting them

A potential fix would be to adjust the JSON serialization to use higher precision for float32 values near the boundaries, or to modify the parser to accept and clamp values that are marginally over the limit due to rounding:

```diff
# In json_format.py _ConvertFloat function
def _ConvertFloat(value, field):
  if field.cpp_type == descriptor.FieldDescriptor.CPPTYPE_FLOAT:
    if value > 3.4028235e+38:
-     raise ParseError('Float value too large')
+     # Clamp to max float32 if marginally over due to rounding
+     if value < 3.4028236e+38:
+       return 3.4028234663852886e+38
+     else:
+       raise ParseError('Float value too large')
```