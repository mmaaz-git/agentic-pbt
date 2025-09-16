# Bug Report: troposphere.servicediscovery Invalid JSON Generation with Non-Finite Values

**Target**: `troposphere.servicediscovery` (specifically `DnsRecord`, `SOA`, and related classes)
**Severity**: High
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `double` validator in troposphere accepts non-finite float values (infinity, -infinity, NaN) which causes the `to_json()` method to generate invalid JSON that violates RFC 7159 and will be rejected by AWS CloudFormation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.servicediscovery import DnsRecord
import math

@given(st.sampled_from([float('inf'), float('-inf'), float('nan')]))
def test_to_json_produces_invalid_json(value):
    """to_json() produces invalid JSON with non-finite values."""
    dns_record = DnsRecord(TTL=value, Type='A')
    json_str = dns_record.to_json()
    
    # These strings are not valid JSON per RFC 7159
    assert any(invalid in json_str for invalid in ['Infinity', '-Infinity', 'NaN'])
```

**Failing input**: `float('inf')`, `float('-inf')`, `float('nan')`

## Reproducing the Bug

```python
from troposphere.servicediscovery import DnsRecord

dns_record = DnsRecord(TTL=float('inf'), Type='A')
json_output = dns_record.to_json()
print(json_output)
```

Output:
```json
{
    "TTL": Infinity,
    "Type": "A"
}
```

## Why This Is A Bug

The JSON specification (RFC 7159) explicitly states that numeric values in JSON must be finite - infinity and NaN are not allowed. While Python's `json` module accepts these values by default, they produce invalid JSON that will be rejected by:
1. Strict JSON parsers
2. AWS CloudFormation API
3. Other tools in the CloudFormation ecosystem

AWS CloudFormation expects valid JSON and will reject templates containing `Infinity`, `-Infinity`, or `NaN` literals.

## Fix

```diff
--- a/troposphere/validators.py
+++ b/troposphere/validators.py
@@ -1,8 +1,11 @@
+import math
+
 def double(x: Any) -> Union[SupportsFloat, SupportsIndex, str, bytes, bytearray]:
     try:
-        float(x)
+        val = float(x)
+        if not math.isfinite(val):
+            raise ValueError("%r is not a valid double (must be finite)" % x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid double" % x)
     else:
         return x
```