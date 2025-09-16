# Bug Report: troposphere.workspacesweb double() Accepts Non-JSON-Serializable Types

**Target**: `troposphere.workspacesweb.double`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `double()` validator function accepts bytes and bytearray objects, which causes JSON serialization to fail when these values are used in AWS CloudFormation template properties.

## Property-Based Test

```python
import json
from hypothesis import given, strategies as st
import troposphere.workspacesweb as target


@given(st.one_of(
    st.binary(min_size=1, max_size=10).filter(lambda b: b.decode('ascii', errors='ignore').replace('.','').replace('-','').isdigit() if b.decode('ascii', errors='ignore') else False),
    st.builds(bytearray, st.binary(min_size=1, max_size=10))
))
def test_double_accepts_bytes_causing_json_serialization_failure(byte_value):
    """double() accepts bytes/bytearray which causes JSON serialization to fail"""
    try:
        float(byte_value)
    except (ValueError, TypeError):
        return
    
    result = target.double(byte_value)
    assert result == byte_value
    
    pattern = target.InlineRedactionPattern(
        ConfidenceLevel=byte_value,
        RedactionPlaceHolder=target.RedactionPlaceHolder(
            RedactionPlaceHolderType='Text'
        )
    )
    
    pattern_dict = pattern.to_dict()
    assert pattern_dict['ConfidenceLevel'] == byte_value
    
    try:
        json.dumps(pattern_dict)
        assert False, f"JSON serialization should have failed for bytes value {byte_value!r}"
    except TypeError as e:
        assert "not JSON serializable" in str(e)
```

**Failing input**: `b'123'`

## Reproducing the Bug

```python
import json
import troposphere.workspacesweb as target

# The double() function accepts bytes
confidence_bytes = b'0.75'
validated = target.double(confidence_bytes)
print(f"double(b'0.75') = {validated!r}")

# Create an AWS property with bytes confidence level
pattern = target.InlineRedactionPattern(
    ConfidenceLevel=confidence_bytes,
    RedactionPlaceHolder=target.RedactionPlaceHolder(
        RedactionPlaceHolderType='Text'
    )
)

# Convert to dictionary (works)
pattern_dict = pattern.to_dict()
print(f"Pattern dict: {pattern_dict}")

# Try to serialize to JSON (fails)
json_output = json.dumps(pattern_dict)
```

## Why This Is A Bug

AWS CloudFormation templates must be JSON-serializable. The `double()` validator is meant to validate numeric "double" values for CloudFormation properties. By accepting bytes/bytearray objects (which `float()` can parse but JSON cannot serialize), it allows creating template objects that will fail during the JSON serialization step, preventing successful CloudFormation deployment.

## Fix

```diff
def double(x: Any) -> Union[SupportsFloat, SupportsIndex, str, bytes, bytearray]:
+    # Reject bytes-like objects to ensure JSON serializability
+    if isinstance(x, (bytes, bytearray, memoryview)):
+        raise ValueError("%r is not a valid double" % x)
     try:
         float(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid double" % x)
     else:
         return x
```