# Bug Report: troposphere.validators.ec2 validate_clientvpnendpoint_vpnport Error Message Formatting

**Target**: `troposphere.validators.ec2.validate_clientvpnendpoint_vpnport`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `validate_clientvpnendpoint_vpnport` function crashes with a TypeError when attempting to format an error message for invalid port values due to trying to join integers with `str.join()`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators.ec2 import validate_clientvpnendpoint_vpnport

@given(st.integers())
def test_clientvpnendpoint_vpnport(port):
    """Property: VPN port must be either 443 or 1194"""
    if port in [443, 1194]:
        assert validate_clientvpnendpoint_vpnport(port) == port
    else:
        with pytest.raises(ValueError, match="VpnPort must be one of"):
            validate_clientvpnendpoint_vpnport(port)
```

**Failing input**: `0` (or any integer other than 443 or 1194)

## Reproducing the Bug

```python
from troposphere.validators.ec2 import validate_clientvpnendpoint_vpnport

validate_clientvpnendpoint_vpnport(8080)
```

## Why This Is A Bug

The function is supposed to raise a ValueError with a helpful message when given an invalid port, but instead crashes with TypeError: "sequence item 0: expected str instance, int found". This prevents users from getting the intended error message about valid port values.

## Fix

```diff
--- a/troposphere/validators/ec2.py
+++ b/troposphere/validators/ec2.py
@@ -188,7 +188,7 @@ def validate_clientvpnendpoint_vpnport(vpnport):
     if vpnport not in VALID_CLIENTVPNENDPOINT_VPNPORT:
         raise ValueError(
             "ClientVpnEndpoint VpnPort must be one of: %s"
-            % ", ".join(VALID_CLIENTVPNENDPOINT_VPNPORT)
+            % ", ".join(str(p) for p in VALID_CLIENTVPNENDPOINT_VPNPORT)
         )
     return vpnport
```