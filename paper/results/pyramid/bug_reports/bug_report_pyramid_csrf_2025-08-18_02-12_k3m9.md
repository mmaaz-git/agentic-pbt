# Bug Report: pyramid.csrf CookieCSRFStoragePolicy Modifies Request State

**Target**: `pyramid.csrf.CookieCSRFStoragePolicy.new_csrf_token`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `CookieCSRFStoragePolicy.new_csrf_token()` method incorrectly modifies the `request.cookies` dictionary, making it appear as if the client sent a CSRF token when it was actually generated server-side.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyramid.csrf import CookieCSRFStoragePolicy
from unittest.mock import Mock

@given(st.text(min_size=5, max_size=20))
def test_cookie_policy_should_not_modify_request(cookie_name):
    """Request.cookies should remain immutable - representing only what client sent."""
    request = Mock()
    request.cookies = {}  # Client sent no cookies
    request.add_response_callback = Mock()
    
    original_cookies = request.cookies.copy()
    
    policy = CookieCSRFStoragePolicy(cookie_name=cookie_name)
    token = policy.new_csrf_token(request)
    
    # Bug: request.cookies is modified
    assert request.cookies == original_cookies  # This assertion fails!
```

**Failing input**: Any valid cookie name (e.g., `"csrf_token"`)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.csrf import CookieCSRFStoragePolicy
from unittest.mock import Mock

request = Mock()
request.cookies = {}
request.add_response_callback = Mock()

policy = CookieCSRFStoragePolicy(cookie_name='csrf_token')
token = policy.new_csrf_token(request)

print(f"request.cookies before: {{}}")
print(f"request.cookies after: {request.cookies}")
print(f"Token in cookies: {'csrf_token' in request.cookies}")
```

## Why This Is A Bug

The `request.cookies` dictionary represents cookies sent BY the client TO the server. It should be treated as immutable request data. By modifying it to include a server-generated token, the code:

1. Violates the principle that request objects represent client-sent data
2. Can cause confusion in debugging (appears client sent a token when they didn't)
3. May mask bugs where CSRF tokens aren't properly transmitted
4. Could interfere with other middleware or code that expects unmodified request state

## Fix

```diff
--- a/pyramid/csrf.py
+++ b/pyramid/csrf.py
@@ -136,7 +136,7 @@ class CookieCSRFStoragePolicy:
     def new_csrf_token(self, request):
         """Sets a new CSRF token into the request and returns it."""
         token = self._token_factory()
-        request.cookies[self.cookie_name] = token
+        # Don't modify request.cookies - it represents client data
 
         def set_cookie(request, response):
             self.cookie_profile.set_cookies(response, token)
@@ -147,10 +147,12 @@ class CookieCSRFStoragePolicy:
     def get_csrf_token(self, request):
         """Returns the currently active CSRF token by checking the cookies
         sent with the current request."""
         bound_cookies = self.cookie_profile.bind(request)
         token = bound_cookies.get_value()
         if not token:
             token = self.new_csrf_token(request)
+        # Store the token in request attributes if needed for later access
+        request._generated_csrf_token = token
         return token
```