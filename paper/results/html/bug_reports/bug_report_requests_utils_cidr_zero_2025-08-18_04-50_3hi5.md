# Bug Report: requests.utils.is_valid_cidr Incorrectly Rejects /0 CIDR Notation

**Target**: `requests.utils.is_valid_cidr`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `is_valid_cidr` function incorrectly rejects CIDR notation with /0 mask, which is valid and represents all IPv4 addresses (0.0.0.0/0).

## Property-Based Test

```python
from hypothesis import given, strategies as st
import requests.utils

def valid_ipv4_strategy():
    return st.builds(
        lambda a, b, c, d: f"{a}.{b}.{c}.{d}",
        st.integers(0, 255), st.integers(0, 255), 
        st.integers(0, 255), st.integers(0, 255)
    )

@given(valid_ipv4_strategy(), st.integers(min_value=0, max_value=32))
def test_is_valid_cidr_accepts_valid_cidrs(ip, mask):
    """Property: is_valid_cidr should accept all valid CIDR notations"""
    cidr = f"{ip}/{mask}"
    assert requests.utils.is_valid_cidr(cidr) == True
```

**Failing input**: `'0.0.0.0/0'` (or any IP with mask=0)

## Reproducing the Bug

```python
import requests.utils

# Bug: rejects valid /0 CIDR
result = requests.utils.is_valid_cidr('0.0.0.0/0')
print(f"is_valid_cidr('0.0.0.0/0') = {result}")  # False, should be True

# The related functions handle /0 correctly
netmask = requests.utils.dotted_netmask(0)  # Works: returns '0.0.0.0'
in_network = requests.utils.address_in_network('192.168.1.1', '0.0.0.0/0')  # Works: returns True
```

## Why This Is A Bug

CIDR notation allows masks from /0 to /32. The /0 mask means "match all addresses" and is commonly used in routing tables and firewall rules. For example, `NO_PROXY=0.0.0.0/0` would bypass proxy for all IP addresses. The function incorrectly limits the range to 1-32 instead of 0-32, preventing valid use cases.

## Fix

```diff
--- a/requests/utils.py
+++ b/requests/utils.py
@@ -718,7 +718,7 @@ def is_valid_cidr(string_network):
         except ValueError:
             return False
 
-        if mask < 1 or mask > 32:
+        if mask < 0 or mask > 32:
             return False
 
         try:
```