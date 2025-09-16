# Bug Report: OAuth1Session.authorization_url Converts None to String 'None'

**Target**: `requests_oauthlib.oauth1_session.OAuth1Session.authorization_url`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `authorization_url` method incorrectly converts `None` values to the string `'None'` in URL parameters, causing OAuth providers to receive invalid token values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from urllib.parse import parse_qs, urlparse
from requests_oauthlib import OAuth1Session

@given(
    extra_params=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(st.none(), st.text(min_size=1, max_size=50)),
        max_size=3
    )
)
def test_authorization_url_none_values(extra_params):
    session = OAuth1Session('client_key', client_secret='secret')
    session._client.client.resource_owner_key = None
    
    auth_url = session.authorization_url('https://example.com/auth', 
                                         request_token=None, 
                                         **extra_params)
    
    parsed = urlparse(auth_url)
    params = parse_qs(parsed.query)
    
    # None should not be converted to string 'None'
    for key, values in params.items():
        for value in values:
            assert value != 'None', f"None converted to string 'None' for {key}"
```

**Failing input**: `extra_params={}` or any dict with None values

## Reproducing the Bug

```python
from requests_oauthlib import OAuth1Session

session = OAuth1Session('client_key', client_secret='secret')
session._client.client.resource_owner_key = None

url = session.authorization_url('https://example.com/auth', request_token=None)
print(url)  # https://example.com/auth?oauth_token=None

# Also affects extra parameters
url2 = session.authorization_url('https://example.com/auth', 
                                 request_token=None,
                                 extra_param=None)
print(url2)  # https://example.com/auth?extra_param=None&oauth_token=None
```

## Why This Is A Bug

1. **OAuth Specification Violation**: The OAuth 1.0 spec doesn't define 'None' as a valid token value. OAuth providers expect either a valid token or no oauth_token parameter at all.

2. **API Contract Violation**: The docstring states the method "appends request_token and optional kwargs to url" but doesn't indicate that None values will be converted to strings.

3. **Security/Functionality Impact**: OAuth providers receiving 'None' as a literal token value will likely reject the request, breaking the OAuth flow for applications that don't have a token yet.

## Fix

```diff
--- a/requests_oauthlib/oauth1_session.py
+++ b/requests_oauthlib/oauth1_session.py
@@ -248,7 +248,10 @@ class OAuth1Session(requests.Session):
         >>> oauth_session.authorization_url(authorization_url)
         'https://api.twitter.com/oauth/authorize?oauth_token=sdf0o9823sjdfsdf&oauth_callback=https%3A%2F%2F127.0.0.1%2Fcallback'
         """
-        kwargs["oauth_token"] = request_token or self._client.client.resource_owner_key
+        token = request_token or self._client.client.resource_owner_key
+        if token is not None:
+            kwargs["oauth_token"] = token
         log.debug("Adding parameters %s to url %s", kwargs, url)
-        return add_params_to_uri(url, kwargs.items())
+        # Filter out None values from kwargs
+        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
+        return add_params_to_uri(url, filtered_kwargs.items())
```

This fix ensures that None values are omitted from the URL parameters rather than being converted to the string 'None'.