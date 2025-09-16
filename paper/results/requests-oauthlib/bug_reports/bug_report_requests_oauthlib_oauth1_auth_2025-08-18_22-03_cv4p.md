# Bug Report: requests_oauthlib.oauth1_auth TypeError with Empty Binary Body

**Target**: `requests_oauthlib.oauth1_auth.OAuth1`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

OAuth1 authentication handler crashes with TypeError when processing an empty binary body (`b''`) without a Content-Type header.

## Property-Based Test

```python
@given(
    url=st.text(min_size=1),
    method=st.sampled_from(["GET", "POST", "PUT", "DELETE"]),
    body=st.just(b''),  # Empty binary body
)
def test_binary_body_handling(url, method, body):
    oauth = OAuth1(client_key="test_key")
    
    request = mock.Mock()
    request.url = url
    request.method = method
    request.body = body
    request.headers = {}  # No Content-Type header
    request.prepare_headers = mock.Mock()
    
    result = oauth(request)  # Crashes here
```

**Failing input**: `body=b''` with no Content-Type header

## Reproducing the Bug

```python
from requests_oauthlib import OAuth1
from unittest.mock import Mock

auth = OAuth1('client_key', 'client_secret')
request = Mock()
request.url = "http://example.com"
request.method = "POST"
request.body = b''
request.headers = {}
request.prepare_headers = Mock()

auth(request)
```

## Why This Is A Bug

When the Content-Type header is missing, the code calls `extract_params(r.body)` at line 77 to check if the body contains URL-encoded parameters. However, if the body is binary (bytes), the `extract_params` function from oauthlib fails with a TypeError because it tries to use a string regex pattern on bytes. This is an edge case where an empty binary body without Content-Type causes a crash.

## Fix

```diff
--- a/requests_oauthlib/oauth1_auth.py
+++ b/requests_oauthlib/oauth1_auth.py
@@ -74,7 +74,7 @@ class OAuth1(AuthBase):
         content_type = r.headers.get("Content-Type", "")
         if (
             not content_type
-            and extract_params(r.body)
+            and r.body and isinstance(r.body, str) and extract_params(r.body)
             or self.client.signature_type == SIGNATURE_TYPE_BODY
         ):
             content_type = CONTENT_TYPE_FORM_URLENCODED
```