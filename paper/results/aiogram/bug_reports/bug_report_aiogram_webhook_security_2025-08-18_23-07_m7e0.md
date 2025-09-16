# Bug Report: aiogram.webhook.security IPFilter Network Address Parsing

**Target**: `aiogram.webhook.security.IPFilter`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

IPFilter.allow_ip() crashes when given CIDR network notation with host bits set (e.g., "192.168.1.100/24"), even though this is a common way users specify networks.

## Property-Based Test

```python
@given(
    st.integers(0, 255),
    st.integers(0, 255),
    st.integers(0, 255),
    st.integers(0, 255),
    st.integers(24, 30)
)
def test_ipfilter_network_expansion(a, b, c, d, prefix):
    network_str = f"{a}.{b}.{c}.{d}/{prefix}"
    
    try:
        network = IPv4Network(network_str, strict=False)
    except:
        assume(False)
    
    if network.num_addresses > 1024:
        assume(False)
    
    ip_filter = IPFilter()
    ip_filter.allow_ip(network_str)  # Fails here
    
    hosts = list(network.hosts())
    if not hosts:
        hosts = [network.network_address]
    
    for host in hosts:
        host_str = str(host)
        assert ip_filter.check(host_str)
```

**Failing input**: `allow_ip("0.0.0.1/24")`

## Reproducing the Bug

```python
from aiogram.webhook.security import IPFilter

ip_filter = IPFilter()
ip_filter.allow_ip("192.168.1.100/24")
```

## Why This Is A Bug

Users commonly specify networks using any IP within that network (e.g., "192.168.1.100/24" to mean the /24 network containing that IP). Many networking tools accept this notation. The current implementation crashes instead of handling it gracefully.

## Fix

```diff
--- a/aiogram/webhook/security.py
+++ b/aiogram/webhook/security.py
@@ -20,7 +20,7 @@ class IPFilter:
 
     def allow_ip(self, ip: Union[str, IPv4Network, IPv4Address]) -> None:
         if isinstance(ip, str):
-            ip = IPv4Network(ip) if "/" in ip else IPv4Address(ip)
+            ip = IPv4Network(ip, strict=False) if "/" in ip else IPv4Address(ip)
         if isinstance(ip, IPv4Address):
             self._allowed_ips.add(ip)
         elif isinstance(ip, IPv4Network):
```