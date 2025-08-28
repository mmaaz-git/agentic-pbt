# Bug Report: requests_oauthlib.oauth1_auth UnicodeDecodeError with Non-UTF8 Content-Type Header

**Target**: `requests_oauthlib.oauth1_auth.OAuth1`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

OAuth1 authentication handler crashes with UnicodeDecodeError when the Content-Type header contains non-UTF8 bytes.

## Property-Based Test

```python
@given(
    client_key=st.text(min_size=1),
    content_type_header=st.binary(min_size=1, max_size=100),
    body_with_params=st.just("key=value&other=data"),
)
def test_content_type_detection_logic(client_key, content_type_header, body_with_params):
    oauth = OAuth1(client_key=client_key)
    
    request = mock.Mock()
    request.url = "http://example.com"
    request.method = "POST"
    request.body = body_with_params
    request.headers = {"Content-Type": content_type_header}
    request.prepare_headers = mock.Mock()
    
    result = oauth(request)  # Crashes here
```

**Failing input**: `content_type_header=b'\x80'`

## Reproducing the Bug

```python
from requests_oauthlib import OAuth1
import requests

auth = OAuth1('client_key', 'client_secret')
req = requests.Request('POST', 'http://example.com', data='test')
prepared = req.prepare()
prepared.headers['Content-Type'] = b'\x80'
auth(prepared)
```

## Why This Is A Bug

The requests library allows bytes values in headers, and OAuth1 should handle them gracefully. When a Content-Type header contains non-UTF8 bytes, the code blindly attempts to decode it as UTF-8 at line 82 of oauth1_auth.py, causing a crash. This violates the principle that authentication handlers should not crash on valid request objects.

## Fix

```diff
--- a/requests_oauthlib/oauth1_auth.py
+++ b/requests_oauthlib/oauth1_auth.py
@@ -79,7 +79,12 @@ class OAuth1(AuthBase):
         ):
             content_type = CONTENT_TYPE_FORM_URLENCODED
         if not isinstance(content_type, str):
-            content_type = content_type.decode("utf-8")
+            try:
+                content_type = content_type.decode("utf-8")
+            except (UnicodeDecodeError, AttributeError):
+                # If decoding fails or object doesn't have decode method,
+                # treat as unknown content type
+                content_type = ""
 
         is_form_encoded = CONTENT_TYPE_FORM_URLENCODED in content_type
```