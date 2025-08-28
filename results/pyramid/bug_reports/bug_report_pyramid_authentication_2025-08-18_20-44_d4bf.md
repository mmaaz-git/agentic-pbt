# Bug Report: pyramid.authentication Invalid IP Address Handling Causes Crash

**Target**: `pyramid.authentication.encode_ip_timestamp`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `encode_ip_timestamp` function crashes with UnicodeEncodeError when given an IPv4 address with octets greater than 255, causing authentication failures in AuthTicket creation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyramid.authentication import encode_ip_timestamp

@given(
    ip=st.from_regex(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'),
    timestamp=st.integers(min_value=0, max_value=2**32-1)
)
def test_encode_ip_timestamp(ip, timestamp):
    """Test encode_ip_timestamp handles all regex-valid IPs"""
    result = encode_ip_timestamp(ip, timestamp)
    assert isinstance(result, bytes)
    assert len(result) == 8
```

**Failing input**: `ip='0.0.0.260', timestamp=0`

## Reproducing the Bug

```python
from pyramid.authentication import encode_ip_timestamp

# IP address with octet > 255
ip = '192.168.1.260'
timestamp = 1234567890

try:
    result = encode_ip_timestamp(ip, timestamp)
    print(f"Result: {result}")
except UnicodeEncodeError as e:
    print(f"UnicodeEncodeError: {e}")
```

## Why This Is A Bug

The function accepts any string matching the IPv4 regex pattern but doesn't validate that octets are within the valid range (0-255). When octets exceed 255, `chr(260)` produces Unicode character U+0104 which cannot be encoded as latin-1, causing a crash. This violates the expected behavior that valid-looking IP addresses should be handled gracefully.

## Fix

```diff
--- a/pyramid/authentication.py
+++ b/pyramid/authentication.py
@@ -810,6 +810,11 @@ def calculate_digest(
 # this function licensed under the MIT license (stolen from Paste)
 def encode_ip_timestamp(ip, timestamp):
+    # Validate IP octets are in valid range
+    octets = list(map(int, ip.split('.')))
+    if any(octet > 255 or octet < 0 for octet in octets):
+        raise ValueError(f"Invalid IP address: {ip}")
+    
     ip_chars = ''.join(map(chr, map(int, ip.split('.'))))
     t = int(timestamp)
     ts = (
```