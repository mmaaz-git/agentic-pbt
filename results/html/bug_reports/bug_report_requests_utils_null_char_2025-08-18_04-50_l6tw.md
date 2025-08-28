# Bug Report: requests.utils.is_ipv4_address Crashes on Null Character

**Target**: `requests.utils.is_ipv4_address`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `is_ipv4_address` function crashes with a ValueError when given a string containing null bytes (\x00), which can occur when parsing malformed URLs.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import requests.utils

@given(st.text())
def test_is_ipv4_address_doesnt_crash(ip_string):
    """Property: is_ipv4_address should never crash on any string input"""
    result = requests.utils.is_ipv4_address(ip_string)
    assert isinstance(result, bool)
```

**Failing input**: `'\x00'`

## Reproducing the Bug

```python
import requests.utils
from urllib.parse import urlparse

# Direct crash
requests.utils.is_ipv4_address('\x00')  # ValueError: embedded null character

# Real-world scenario: parsing a malformed URL
url = 'http://example.com\x00.evil.com/path'
parsed = urlparse(url)
hostname = parsed.hostname  # 'example.com\x00.evil.com'

# This would crash in should_bypass_proxies()
requests.utils.is_ipv4_address(hostname)  # ValueError: embedded null character
```

## Why This Is A Bug

The function is supposed to validate whether a string is a valid IPv4 address and should return False for invalid inputs rather than crashing. The function is used internally in `should_bypass_proxies()` where it processes hostnames from parsed URLs, which can contain null bytes. A malformed URL could cause the entire request to fail unexpectedly.

## Fix

```diff
--- a/requests/utils.py
+++ b/requests/utils.py
@@ -700,7 +700,10 @@ def is_ipv4_address(string_ip):
     :rtype: bool
     """
     try:
+        if '\x00' in string_ip:
+            return False
         socket.inet_aton(string_ip)
     except OSError:
         return False
     return True
```