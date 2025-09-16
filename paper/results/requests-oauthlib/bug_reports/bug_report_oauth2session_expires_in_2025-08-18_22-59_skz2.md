# Bug Report: OAuth2Session Invalid expires_in Causes Crash

**Target**: `requests_oauthlib.OAuth2Session`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

OAuth2Session crashes with ValueError when setting a token containing `expires_in` field with a non-integer string value, instead of handling the invalid input gracefully.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from requests_oauthlib import OAuth2Session

@given(token=st.dictionaries(
    st.sampled_from(['access_token', 'token_type', 'expires_in']),
    st.one_of(st.text(min_size=1), st.integers()),
    min_size=1
))
def test_oauth2_session_token_expires_in_handling(token):
    """OAuth2Session should handle invalid expires_in gracefully"""
    session = OAuth2Session(client_id='test_client')
    session.token = token  # Should not crash for invalid expires_in
```

**Failing input**: `{'expires_in': ':'}`

## Reproducing the Bug

```python
from requests_oauthlib import OAuth2Session

session = OAuth2Session(client_id='test_client')
session.token = {'expires_in': ':'}
```

## Why This Is A Bug

The OAuth2Session should validate token fields before passing them to internal components. While the OAuth2 spec requires `expires_in` to be an integer, the library should handle invalid input gracefully rather than crashing with an unhandled exception. This could cause applications to crash when processing tokens from untrusted or malformed sources.

## Fix

```diff
--- a/requests_oauthlib/oauth2_session.py
+++ b/requests_oauthlib/oauth2_session.py
@@ -146,7 +146,15 @@ class OAuth2Session(requests.Session):
 
     @token.setter
     def token(self, value):
+        # Validate expires_in if present
+        if value and 'expires_in' in value:
+            expires_in = value['expires_in']
+            if expires_in is not None and not isinstance(expires_in, (int, float)):
+                try:
+                    value['expires_in'] = int(expires_in)
+                except (ValueError, TypeError):
+                    # Remove invalid expires_in rather than crash
+                    del value['expires_in']
         self._client.token = value
         self._client.populate_token_attributes(value)
```