# Bug Report: troposphere.servicediscovery Accepts Invalid Negative TTL Values

**Target**: `troposphere.servicediscovery.DnsRecord`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `DnsRecord` class accepts negative TTL values, which violate DNS specifications and will be rejected by AWS CloudFormation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.servicediscovery import DnsRecord

@given(st.integers(max_value=-1))
def test_negative_ttl_accepted(value):
    """Negative TTL values are incorrectly accepted."""
    dns_record = DnsRecord(TTL=value, Type='A')
    dict_result = dns_record.to_dict()
    assert dict_result['TTL'] == value
```

**Failing input**: `-1`, `-100`, `-2147483648`

## Reproducing the Bug

```python
from troposphere.servicediscovery import DnsRecord

dns_record = DnsRecord(TTL=-100, Type='A')
print(dns_record.to_dict())
print(dns_record.to_json())
```

Output:
```python
{'TTL': -100, 'Type': 'A'}
{
    "TTL": -100,
    "Type": "A"
}
```

## Why This Is A Bug

DNS TTL (Time To Live) values must be non-negative integers representing seconds. Negative TTL values:
1. Violate RFC 2181 which specifies TTL as an unsigned 32-bit integer (0 to 2147483647)
2. Will be rejected by AWS CloudFormation when deploying the stack
3. Are semantically meaningless (can't cache for negative time)

## Fix

```diff
--- a/troposphere/validators.py
+++ b/troposphere/validators.py
@@ -1,8 +1,14 @@
 def double(x: Any) -> Union[SupportsFloat, SupportsIndex, str, bytes, bytearray]:
     try:
-        float(x)
+        val = float(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid double" % x)
     else:
         return x
+
+def ttl_validator(x: Any) -> Union[int, float]:
+    val = double(x)
+    if float(val) < 0 or float(val) > 2147483647:
+        raise ValueError("TTL must be between 0 and 2147483647, got %r" % x)
+    return val
```

Then update the `DnsRecord` and `SOA` classes to use `ttl_validator` instead of `double` for TTL fields.