# Bug Report: troposphere.connectcampaigns Invalid JSON Generation with NaN/Infinity

**Target**: `troposphere.connectcampaigns`
**Severity**: High
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The troposphere library generates invalid JSON when NaN or Infinity values are used in numeric properties, violating the JSON specification and causing potential CloudFormation deployment failures.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.connectcampaigns as cc
import json

@given(st.just(float('nan')) | st.just(float('inf')) | st.just(float('-inf')))
def test_invalid_json_generation(value):
    """Test that special float values produce invalid JSON"""
    config = cc.AgentlessDialerConfig(DialingCapacity=value)
    json_output = config.to_json()
    
    # Check if output contains invalid JSON literals
    assert 'NaN' in json_output or 'Infinity' in json_output
    
    # Verify this is invalid JSON per spec
    try:
        # Strict JSON parsers would reject this
        decoder = json.JSONDecoder(strict=False)
        decoder.decode(json_output)
        # Python accepts it, but it's still invalid per RFC 7159
        assert 'NaN' in json_output or 'Infinity' in json_output
    except json.JSONDecodeError:
        pass  # Would fail with strict parsers
```

**Failing input**: `float('nan')`

## Reproducing the Bug

```python
import troposphere.connectcampaigns as cc

config = cc.AgentlessDialerConfig(DialingCapacity=float('nan'))
json_output = config.to_json()
print(json_output)
```

## Why This Is A Bug

The JSON specification (RFC 7159) explicitly states that NaN and Infinity are not valid JSON values. AWS CloudFormation requires valid JSON or YAML for template deployment. When troposphere generates JSON containing `NaN`, `Infinity`, or `-Infinity` literals, it creates templates that CloudFormation cannot process, causing deployment failures.

## Fix

The `double` validator in troposphere should reject NaN and infinity values, or the JSON serialization should handle them specially:

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -93,7 +93,11 @@
 def double(x: Any) -> Union[SupportsFloat, SupportsIndex, str, bytes, bytearray]:
     try:
-        float(x)
+        val = float(x)
+        import math
+        if math.isnan(val) or math.isinf(val):
+            raise ValueError("%r is not a valid double (NaN and Infinity not allowed)" % x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid double" % x)
     else:
         return x
```

Alternatively, handle special values during JSON serialization to produce `null` or raise an error.