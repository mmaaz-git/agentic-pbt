# Bug Report: requests.adapters.HTTPAdapter.proxy_headers Unicode Encoding Crash

**Target**: `requests.adapters.HTTPAdapter.proxy_headers`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

HTTPAdapter.proxy_headers crashes with UnicodeEncodeError when proxy URLs contain non-Latin-1 characters in username or password fields.

## Property-Based Test

```python
@given(urls_with_auth())
def test_proxy_headers_auth_header_presence(proxy_url):
    """
    Property: proxy_headers should include Proxy-Authorization header
    if and only if the proxy URL contains a username.
    """
    adapter = HTTPAdapter()
    headers = adapter.proxy_headers(proxy_url)
    
    username, password = get_auth_from_url(proxy_url)
    
    if username:
        assert "Proxy-Authorization" in headers
    else:
        assert "Proxy-Authorization" not in headers
```

**Failing input**: `'http://Ā:0@0/'` or `'http://0:Ā@0/'`

## Reproducing the Bug

```python
from requests.adapters import HTTPAdapter

adapter = HTTPAdapter()

# Case 1: Non-Latin-1 character in username
proxy_url_1 = 'http://Ā:password@proxy.example.com:8080/'
try:
    adapter.proxy_headers(proxy_url_1)
except UnicodeEncodeError as e:
    print(f"Failed with username 'Ā': {e}")

# Case 2: Non-Latin-1 character in password  
proxy_url_2 = 'http://user:Ā@proxy.example.com:8080/'
try:
    adapter.proxy_headers(proxy_url_2)
except UnicodeEncodeError as e:
    print(f"Failed with password 'Ā': {e}")
```

## Why This Is A Bug

The proxy_headers method should handle international characters in usernames and passwords. Many authentication systems support Unicode characters, and the HTTP Basic Authentication spec (RFC 7617) discusses UTF-8 encoding for credentials. The current implementation assumes all characters fit in Latin-1 encoding, causing crashes for valid international characters.

## Fix

```diff
--- a/requests/auth.py
+++ b/requests/auth.py
@@ -53,11 +53,11 @@ def _basic_auth_str(username, password):
     :rtype: str
     """
     if isinstance(username, str):
-        username = username.encode("latin1")
+        username = username.encode("utf-8")
 
     if isinstance(password, str):
-        password = password.encode("latin1")
+        password = password.encode("utf-8")
 
     authstr = "Basic " + b64encode(b":".join((username, password))).strip().decode("ascii")
```

Alternatively, the function could try UTF-8 first and fall back to Latin-1 for compatibility, or use the charset parameter as specified in RFC 7617.