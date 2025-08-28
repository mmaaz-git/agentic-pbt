# Bug Report: requests.api Inconsistent JSON Parameter API

**Target**: `requests.api`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `put()` and `patch()` functions in requests.api have an inconsistent API compared to `post()`. While all three functions document accepting a `json` parameter, only `post()` explicitly lists it in the function signature.

## Property-Based Test

```python
import inspect
import requests.api
from hypothesis import given, strategies as st


@given(
    url=st.text(min_size=1),
    json_data=st.dictionaries(st.text(), st.text())
)
def test_json_parameter_api_consistency(url, json_data):
    """Test that PUT/PATCH have consistent API with POST for json parameter."""
    
    post_sig = inspect.signature(requests.api.post)
    put_sig = inspect.signature(requests.api.put)
    patch_sig = inspect.signature(requests.api.patch)
    
    # POST explicitly lists json parameter
    assert 'json' in post_sig.parameters
    
    # PUT and PATCH should also list json parameter for consistency
    # since they document it and commonly need it
    assert 'json' in put_sig.parameters  # FAILS
    assert 'json' in patch_sig.parameters  # FAILS
```

**Failing input**: Any non-empty URL and json_data dictionary

## Reproducing the Bug

```python
import inspect
import requests.api

post_sig = inspect.signature(requests.api.post)
put_sig = inspect.signature(requests.api.put) 
patch_sig = inspect.signature(requests.api.patch)

print("POST signature:", post_sig)
print("PUT signature:", put_sig)
print("PATCH signature:", patch_sig)

print("\nPOST has 'json' parameter:", 'json' in post_sig.parameters)
print("PUT has 'json' parameter:", 'json' in put_sig.parameters)
print("PATCH has 'json' parameter:", 'json' in patch_sig.parameters)

print("\nBut all three document accepting json:")
print("POST docs mention json:", 'json:' in requests.api.post.__doc__)
print("PUT docs mention json:", 'json:' in requests.api.put.__doc__)
print("PATCH docs mention json:", 'json:' in requests.api.patch.__doc__)
```

## Why This Is A Bug

This violates the principle of API consistency. POST, PUT, and PATCH are all HTTP methods that commonly send JSON payloads, yet they have different function signatures for the same functionality. The documentation claims all three accept a `json` parameter, but only POST explicitly includes it in the signature. This creates confusion for users and IDE autocomplete, as the json parameter appears as a first-class citizen for POST but not for PUT/PATCH.

## Fix

```diff
--- a/requests/api.py
+++ b/requests/api.py
@@ -110,7 +110,7 @@ def post(url, data=None, json=None, **kwargs):
     return request("post", url, data=data, json=json, **kwargs)
 
 
-def put(url, data=None, **kwargs):
+def put(url, data=None, json=None, **kwargs):
     r"""Sends a PUT request.
 
     :param url: URL for the new :class:`Request` object.
@@ -122,10 +122,10 @@ def put(url, data=None, **kwargs):
     :rtype: requests.Response
     """
 
-    return request("put", url, data=data, **kwargs)
+    return request("put", url, data=data, json=json, **kwargs)
 
 
-def patch(url, data=None, **kwargs):
+def patch(url, data=None, json=None, **kwargs):
     r"""Sends a PATCH request.
 
     :param url: URL for the new :class:`Request` object.
@@ -137,7 +137,7 @@ def patch(url, data=None, **kwargs):
     :rtype: requests.Response
     """
 
-    return request("patch", url, data=data, **kwargs)
+    return request("patch", url, data=data, json=json, **kwargs)
```