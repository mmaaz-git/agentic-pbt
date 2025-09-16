# Bug Report: requests.sessions ValueError on Invalid Port Numbers in Redirects

**Target**: `requests.sessions.SessionRedirectMixin.should_strip_auth`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `should_strip_auth` method crashes with `ValueError` when processing redirect URLs containing invalid port numbers (outside the 0-65535 range), which can occur when a server sends malformed Location headers.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from requests.sessions import SessionRedirectMixin


@given(
    old_port=st.integers(min_value=1, max_value=65535),
    new_port=st.integers(min_value=65536, max_value=99999)
)
def test_should_strip_auth_invalid_port_crash(old_port, new_port):
    """Test that should_strip_auth crashes on invalid port numbers"""
    mixin = SessionRedirectMixin()
    
    old_url = f"http://example.com:{old_port}/"
    new_url = f"http://example.com:{new_port}/"
    
    # This will raise ValueError for invalid ports
    result = mixin.should_strip_auth(old_url, new_url)
```

**Failing input**: `old_port=1, new_port=65536`

## Reproducing the Bug

```python
from requests.sessions import SessionRedirectMixin

mixin = SessionRedirectMixin()
old_url = "http://example.com/"
new_url = "http://example.com:70000/"

result = mixin.should_strip_auth(old_url, new_url)
```

## Why This Is A Bug

The `should_strip_auth` method is called during redirect handling to determine whether to strip authentication headers. When a server sends a Location header with an invalid port number (e.g., due to misconfiguration or malicious intent), the method crashes instead of handling the error gracefully. This causes the entire redirect handling to fail with an unhandled exception, preventing the client from processing the response.

## Fix

```diff
--- a/requests/sessions.py
+++ b/requests/sessions.py
@@ -126,8 +126,18 @@ class SessionRedirectMixin:
 
     def should_strip_auth(self, old_url, new_url):
         """Decide whether Authorization header should be removed when redirecting"""
-        old_parsed = urlparse(old_url)
-        new_parsed = urlparse(new_url)
+        try:
+            old_parsed = urlparse(old_url)
+            new_parsed = urlparse(new_url)
+            # Accessing .port may raise ValueError for invalid ports
+            old_port = old_parsed.port
+            new_port = new_parsed.port
+        except ValueError:
+            # Invalid port number - strip auth for safety
+            return True
+        except Exception:
+            # Any other parsing error - strip auth for safety
+            return True
+        
         if old_parsed.hostname != new_parsed.hostname:
             return True
         # Special case: allow http -> https redirect when using the standard
@@ -137,15 +147,15 @@ class SessionRedirectMixin:
         # that allowed any redirects on the same host.
         if (
             old_parsed.scheme == "http"
-            and old_parsed.port in (80, None)
+            and old_port in (80, None)
             and new_parsed.scheme == "https"
-            and new_parsed.port in (443, None)
+            and new_port in (443, None)
         ):
             return False
 
         # Handle default port usage corresponding to scheme.
-        changed_port = old_parsed.port != new_parsed.port
+        changed_port = old_port != new_port
         changed_scheme = old_parsed.scheme != new_parsed.scheme
         default_port = (DEFAULT_PORTS.get(old_parsed.scheme, None), None)
         if (
             not changed_scheme
-            and old_parsed.port in default_port
-            and new_parsed.port in default_port
+            and old_port in default_port
+            and new_port in default_port
         ):
```