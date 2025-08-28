# Bug Report: python_http_client.client Shared Mutable Headers

**Target**: `python_http_client.client.Client`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

Child Client instances created via the `_()` method share the same headers dictionary with their parent, causing header modifications on any client to affect all related clients.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import python_http_client.client as client

@given(
    st.dictionaries(st.text(min_size=1), st.text(), min_size=1),
    st.text(min_size=1),
    st.dictionaries(st.text(min_size=1), st.text(), min_size=1)
)
def test_client_headers_isolation(initial_headers, segment, new_headers):
    """Test that child clients don't share mutable headers with parent"""
    parent = client.Client(
        host="http://example.com",
        request_headers=initial_headers.copy()
    )
    
    original_headers = parent.request_headers.copy()
    child = parent._(segment)
    child._update_headers(new_headers)
    
    assert parent.request_headers == original_headers
```

**Failing input**: `initial_headers={'0': ''}, segment='0', new_headers={'0': '0'}`

## Reproducing the Bug

```python
import python_http_client.client as client

headers = {"Authorization": "Bearer token"}
parent = client.Client(host="http://example.com", request_headers=headers)
child = parent._("api")

print(f"Parent headers before: {parent.request_headers}")
print(f"Same object? {parent.request_headers is child.request_headers}")

child._update_headers({"X-Custom": "value"})

print(f"Parent headers after: {parent.request_headers}")
```

## Why This Is A Bug

When creating child clients, the headers dictionary reference is passed directly without copying, violating the expectation that child clients should be independent. This can lead to unintended header pollution across different API endpoints.

## Fix

```diff
--- a/client.py
+++ b/client.py
@@ -153,7 +153,7 @@ class Client(object):
         """
         url_path = self._url_path + [name] if name else self._url_path
         return Client(host=self.host,
                       version=self._version,
-                      request_headers=self.request_headers,
+                      request_headers=self.request_headers.copy(),
                       url_path=url_path,
                       append_slash=self.append_slash,
                       timeout=self.timeout)
```