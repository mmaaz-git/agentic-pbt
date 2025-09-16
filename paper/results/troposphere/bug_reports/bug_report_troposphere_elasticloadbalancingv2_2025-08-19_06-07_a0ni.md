# Bug Report: troposphere.elasticloadbalancingv2 Port Validator Accepts Invalid Strings with Whitespace

**Target**: `troposphere.elasticloadbalancingv2.tg_healthcheck_port` and `troposphere.validators.network_port`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The port validation functions accept strings with trailing/leading whitespace (e.g., '80\r', '443\n', '8080\t') which are invalid port specifications and would create malformed CloudFormation templates.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
import troposphere.elasticloadbalancingv2 as elbv2

@given(st.text())
def test_tg_healthcheck_port_rejects_invalid_strings(text):
    """Test that tg_healthcheck_port properly validates port strings"""
    if text == "traffic-port":
        result = elbv2.tg_healthcheck_port(text)
        assert result == "traffic-port"
    elif text.strip().isdigit() and text.isdigit():
        # Only pure digit strings should be accepted
        port = int(text)
        if -1 <= port <= 65535:
            result = elbv2.tg_healthcheck_port(text)
            assert result == text
        else:
            with pytest.raises(ValueError):
                elbv2.tg_healthcheck_port(text)
    else:
        # Should reject non-numeric strings and strings with whitespace
        with pytest.raises((ValueError, TypeError)):
            elbv2.tg_healthcheck_port(text)
```

**Failing input**: `'0\r'`

## Reproducing the Bug

```python
import troposphere.elasticloadbalancingv2 as elbv2

# These invalid port strings are incorrectly accepted
invalid_ports = ['80\r', '443\n', '8080\t', ' 22', '3000 ']

for port_str in invalid_ports:
    result = elbv2.tg_healthcheck_port(port_str)
    print(f"Input: {repr(port_str)} -> Output: {repr(result)}")

# This creates invalid CloudFormation template
tg = elbv2.TargetGroup(
    'TestTG',
    HealthCheckPort='80\r',
    Port=80,
    Protocol='HTTP',
    VpcId='vpc-12345'
)

cf_dict = tg.to_dict()
print(f"\nCloudFormation: {cf_dict['Properties']['HealthCheckPort']!r}")
```

## Why This Is A Bug

The validation functions should reject port strings containing whitespace characters. While Python's `int()` function accepts strings with whitespace, the raw string with whitespace is returned unchanged and embedded in CloudFormation templates. AWS CloudFormation expects clean numeric strings for port values, not strings with control characters or whitespace. This violates the contract that validators should ensure only valid CloudFormation values are accepted.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -84,6 +84,9 @@ def positive_integer(x: Any) -> int:
 
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
+    # Reject strings with whitespace for CloudFormation compatibility
+    if isinstance(x, str) and x != x.strip():
+        raise ValueError("%r contains whitespace and is not a valid integer" % x)
     try:
         int(x)
     except (ValueError, TypeError):
```