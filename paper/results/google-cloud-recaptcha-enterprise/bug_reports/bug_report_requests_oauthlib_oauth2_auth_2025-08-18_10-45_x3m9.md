# Bug Report: requests_oauthlib.oauth2_auth Special Attribute Injection

**Target**: `requests_oauthlib.oauth2_auth.OAuth2`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The OAuth2 class crashes when a token dictionary contains special Python attribute names like `__class__`, causing a TypeError during initialization.

## Property-Based Test

```python
@given(
    special_keys=st.lists(
        st.sampled_from(['__init__', '__class__', '__dict__', '_client', 'items', '__setattr__']),
        min_size=1,
        max_size=3,
        unique=True
    )
)
def test_token_with_special_attribute_names(special_keys):
    """Test token dict with keys that might conflict with object attributes."""
    token = {'access_token': 'test', 'token_type': 'Bearer'}
    for key in special_keys:
        token[key] = f'special_{key}'
    
    oauth2 = OAuth2(client_id='test', token=token)
```

**Failing input**: `special_keys=['__class__']`

## Reproducing the Bug

```python
from requests_oauthlib.oauth2_auth import OAuth2

token = {
    'access_token': 'test_token',
    'token_type': 'Bearer',
    '__class__': 'malicious_string'
}

oauth2 = OAuth2(client_id='test_client', token=token)
```

## Why This Is A Bug

The OAuth2 class blindly copies all token dictionary entries as attributes on the client object using `setattr()` without validating the attribute names. This violates the principle that user-provided data should not directly control object internals. Special attributes like `__class__` have restrictions and cannot be set to arbitrary values, causing the code to crash.

## Fix

```diff
--- a/requests_oauthlib/oauth2_auth.py
+++ b/requests_oauthlib/oauth2_auth.py
@@ -19,7 +19,9 @@ class OAuth2(AuthBase):
         self._client = client or WebApplicationClient(client_id, token=token)
         if token:
             for k, v in token.items():
-                setattr(self._client, k, v)
+                # Skip special/private attributes to prevent crashes
+                if not k.startswith('__'):
+                    setattr(self._client, k, v)
 
     def __call__(self, r):
         """Append an OAuth 2 token to the request.
```