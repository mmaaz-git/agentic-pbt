# Bug Report: troposphere.kafkaconnect Integer Validator Accepts Bytes Causing JSON Serialization Failure

**Target**: `troposphere.kafkaconnect`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The integer validator in troposphere accepts bytes objects, which then causes JSON serialization to fail when generating CloudFormation templates, resulting in a TypeError.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import json
import troposphere.kafkaconnect as kc

@given(st.integers(0, 100))
def test_bytes_creates_invalid_cloudformation(value):
    bytes_value = str(value).encode('utf-8')
    
    policy = kc.ScaleInPolicy(CpuUtilizationPercentage=bytes_value)
    dict_repr = policy.to_dict()
    
    assert isinstance(dict_repr['CpuUtilizationPercentage'], bytes)
    
    with pytest.raises(TypeError) as exc_info:
        json.dumps(dict_repr)
    
    assert "not JSON serializable" in str(exc_info.value) or \
           "bytes" in str(exc_info.value).lower()
```

**Failing input**: `b'50'`

## Reproducing the Bug

```python
import json
import troposphere.kafkaconnect as kc

bytes_value = b'50'
policy = kc.ScaleInPolicy(CpuUtilizationPercentage=bytes_value)
dict_repr = policy.to_dict()

print(f"Object created: {dict_repr}")

json_output = json.dumps(dict_repr)
```

## Why This Is A Bug

The integer validator accepts bytes objects that can be converted to integers via `int(b'50')`, but it returns the bytes object unchanged. When troposphere attempts to generate CloudFormation JSON, the bytes object cannot be serialized, causing template generation to fail. This violates the expectation that validated values should be JSON-serializable for CloudFormation output.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -1,7 +1,10 @@
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
         int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
+    if isinstance(x, bytes):
+        # Convert bytes to string to ensure JSON serializability
+        return x.decode('utf-8')
     else:
         return x
```