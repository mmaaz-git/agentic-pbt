# Bug Report: pyramid.request IPv6 Address Mangling in URL Generation

**Target**: `pyramid.request.Request._partial_application_url`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `_partial_application_url` method in pyramid.request completely mangles IPv6 addresses, resulting in invalid URLs when IPv6 hosts are provided.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyramid.request import Request

@given(
    ipv6=st.sampled_from(['::1', '2001:db8::1', 'fe80::1', '[::1]', '[2001:db8::1]']),
    port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535).map(str))
)
def test_ipv6_url_generation(ipv6, port):
    request = Request.blank('/')
    request.environ['wsgi.url_scheme'] = 'http'
    request.environ['SERVER_NAME'] = 'default.com'
    request.environ['SERVER_PORT'] = '80'
    
    url = request._partial_application_url(host=ipv6, port=port)
    
    if not ipv6.startswith('['):
        assert f'[{ipv6}]' in url or ipv6 in url
    else:
        assert ipv6 in url
```

**Failing input**: `ipv6='::1', port='8080'`

## Reproducing the Bug

```python
from pyramid.request import Request

request = Request.blank('/')
request.environ['wsgi.url_scheme'] = 'http'
request.environ['SERVER_NAME'] = 'default.com'
request.environ['SERVER_PORT'] = '80'

url = request._partial_application_url(host='::1', port='8080')
print(f"Expected: http://[::1]:8080")
print(f"Got: {url}")
# Output: Got: http://:8080

url = request._partial_application_url(host='[::1]', port='8080')
print(f"Expected: http://[::1]:8080")
print(f"Got: {url}")
# Output: Got: http://[:8080
```

## Why This Is A Bug

The method incorrectly splits IPv6 addresses on ':' characters to separate host and port, but IPv6 addresses contain colons as part of their syntax (e.g., '::1', '2001:db8::1'). This causes the IPv6 address to be split incorrectly, losing the actual host information and creating invalid URLs.

## Fix

```diff
--- a/pyramid/url.py
+++ b/pyramid/url.py
@@ -88,10 +88,18 @@ class URLMethodsMixin:
                 host = e['SERVER_NAME']
         if port is None:
-            if ':' in host:
-                host, port = host.split(':', 1)
+            # Handle IPv6 addresses properly
+            if host.startswith('[') and ']' in host:
+                # Bracketed IPv6 with possible port
+                if ']:' in host:
+                    host, port = host.rsplit(']:', 1)
+                    host = host + ']'
+            elif ':' in host and not host.count(':') > 1:
+                # Regular host:port (not IPv6)
+                host, port = host.rsplit(':', 1)
             else:
                 port = e['SERVER_PORT']
         else:
             port = str(port)
-            if ':' in host:
-                host, _ = host.split(':', 1)
+            # Handle IPv6 addresses when port is explicitly provided
+            if host.startswith('[') and ']' in host:
+                # Remove port from bracketed IPv6 if present
+                if ']:' in host:
+                    host = host.split(']:')[0] + ']'
+            elif ':' in host and host.count(':') == 1:
+                # Regular host:port (not IPv6)
+                host, _ = host.rsplit(':', 1)
+            elif ':' in host and host.count(':') > 1:
+                # Unbracketed IPv6 - should be bracketed
+                host = f'[{host}]'
```