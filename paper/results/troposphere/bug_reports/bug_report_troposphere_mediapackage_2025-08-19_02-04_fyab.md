# Bug Report: troposphere.mediapackage Integer Validator Accepts Floats

**Target**: `troposphere.validators.integer` and all properties using it in `troposphere.mediapackage`
**Severity**: High
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer` validator function in troposphere accepts float values without converting them to integers, causing CloudFormation templates to contain float values for properties that AWS CloudFormation strictly requires to be integers.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from troposphere.mediapackage import StreamSelection

@given(
    float_value=st.floats(
        allow_nan=False, 
        allow_infinity=False,
        min_value=-1e10,
        max_value=1e10
    ).filter(lambda x: x != int(x))  # Only non-integer floats
)
@settings(max_examples=20)
def test_integer_properties_accept_floats(float_value):
    """Test that integer properties incorrectly accept and preserve float values."""
    stream = StreamSelection()
    stream.MaxVideoBitsPerSecond = float_value
    assert stream.MaxVideoBitsPerSecond == float_value
    assert isinstance(stream.MaxVideoBitsPerSecond, float)
    
    dict_repr = stream.to_dict()
    assert dict_repr["MaxVideoBitsPerSecond"] == float_value
```

**Failing input**: Any float value, e.g., `1666666.6666666667`

## Reproducing the Bug

```python
import json
from troposphere.mediapackage import StreamSelection, OriginEndpoint
from troposphere import Template

# Example 1: Direct float assignment
stream = StreamSelection()
stream.MaxVideoBitsPerSecond = 1000000.5
print(json.dumps(stream.to_dict()))
# Output: {"MaxVideoBitsPerSecond": 1000000.5}

# Example 2: Common calculation scenario
total_bitrate = 5000000
num_streams = 3
per_stream_bitrate = total_bitrate / num_streams

stream2 = StreamSelection()
stream2.MaxVideoBitsPerSecond = per_stream_bitrate
print(json.dumps(stream2.to_dict()))
# Output: {"MaxVideoBitsPerSecond": 1666666.6666666667}

# Example 3: Full template generation
template = Template()
endpoint = OriginEndpoint("TestEndpoint", ChannelId="test", Id="endpoint1")
endpoint.StartoverWindowSeconds = 86400.5
template.add_resource(endpoint)
print(template.to_json())
# Contains: "StartoverWindowSeconds": 86400.5
```

## Why This Is A Bug

AWS CloudFormation strictly requires integer types for properties documented as "Type: Integer". When troposphere generates templates with float values for these properties, CloudFormation will reject the template with a validation error. The `integer` validator should either:
1. Convert float inputs to integers (preferred), or
2. Reject float inputs with a clear error message

Currently, it accepts floats and passes them through unchanged, leading to invalid CloudFormation templates.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -46,10 +46,12 @@ def boolean(x: Any) -> bool:
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        val = int(x)
+        if isinstance(x, float) and x != val:
+            raise ValueError("%r is not a valid integer (has decimal part)" % x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
-        return x
+        return val
```

Alternative fix (stricter):
```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -46,6 +46,8 @@ def boolean(x: Any) -> bool:
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
+    if isinstance(x, float):
+        raise TypeError("Integer property cannot accept float values, got %r" % x)
     try:
         int(x)
     except (ValueError, TypeError):
```