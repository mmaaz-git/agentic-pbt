# Bug Report: requests.utils.is_ipv4_address crashes on null byte input

**Target**: `requests.utils.is_ipv4_address`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `is_ipv4_address` function crashes with a ValueError when given input containing null bytes, instead of returning False as expected for invalid IP addresses.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import requests.utils

@given(st.text())
def test_is_ipv4_address_handles_all_strings(text):
    """Test that is_ipv4_address returns a boolean for any string input."""
    result = requests.utils.is_ipv4_address(text)
    assert isinstance(result, bool)
```

**Failing input**: `'\x00'`

## Reproducing the Bug

```python
import requests.utils

# This should return False but raises ValueError instead
try:
    result = requests.utils.is_ipv4_address('\x00')
    print(f"Result: {result}")
except ValueError as e:
    print(f"ValueError: {e}")
```

## Why This Is A Bug

The function `is_ipv4_address` is a validation function that should return `True` or `False` to indicate whether the input is a valid IPv4 address. According to its signature and usage pattern, it should handle any string input gracefully and return `False` for invalid inputs rather than raising an exception.

This function is used internally by `should_bypass_proxies` to check if a hostname is an IPv4 address. If a malformed URL with null bytes in the hostname is processed, it could cause an unexpected crash in the proxy bypass logic.

## Fix

```diff
def is_ipv4_address(string_ip):
    """
    :rtype: bool
    """
    try:
        socket.inet_aton(string_ip)
-   except OSError:
+   except (OSError, ValueError):
        return False
    return True
```

The fix is simple: catch `ValueError` in addition to `OSError`. The `socket.inet_aton` function can raise `ValueError` for certain invalid inputs like null bytes, and these should be treated as invalid IP addresses by returning `False`.