# Bug Report: python_http_client Version 0 Not Added to URL

**Target**: `python_http_client.client.Client`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The Client class incorrectly ignores version=0 when building URLs, treating 0 as falsy instead of a valid version number.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from python_http_client.client import Client

@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text()
))
def test_client_version_types(version):
    """Test Client with various version types"""
    client = Client(host='http://test', version=version)
    url = client._build_url(None)
    assert f'/v{str(version)}' in url
```

**Failing input**: `version=0`

## Reproducing the Bug

```python
from python_http_client.client import Client

client = Client(host='http://api.example.com', version=0, url_path=['users'])
url = client._build_url({'id': '123'})

print(f"URL with version=0: {url}")
print(f"Expected: http://api.example.com/v0/users?id=123")
print(f"Actual:   {url}")

assert '/v0' not in url
```

## Why This Is A Bug

The bug occurs in `client.py` lines 132-135 where `if self._version:` treats 0 as falsy. Version 0 is a valid API version (commonly used for beta/experimental APIs), but the current implementation silently ignores it. This violates the principle that all valid version values should be handled consistently.

## Fix

```diff
--- a/python_http_client/client.py
+++ b/python_http_client/client.py
@@ -129,7 +129,7 @@ class Client(object):
             url_values = urlencode(sorted(query_params.items()), True)
             url = '{}?{}'.format(url, url_values)
 
-        if self._version:
+        if self._version is not None:
             url = self._build_versioned_url(url)
         else:
             url = '{}{}'.format(self.host, url)
```