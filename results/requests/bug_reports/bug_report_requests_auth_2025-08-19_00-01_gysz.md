# Bug Report: requests.auth Unicode Encoding Failure

**Target**: `requests.auth._basic_auth_str` and `requests.auth.HTTPBasicAuth`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `_basic_auth_str` function crashes with UnicodeEncodeError when given usernames or passwords containing characters outside the latin-1 encoding range (characters with code points > 255).

## Property-Based Test

```python
from hypothesis import given, strategies as st
import requests.auth

@given(
    st.text(min_size=1).filter(lambda x: '\x00' not in x),
    st.text(min_size=1).filter(lambda x: '\x00' not in x)
)
def test_basic_auth_str_format(username, password):
    """Test that _basic_auth_str produces correct format"""
    auth_str = requests.auth._basic_auth_str(username, password)
    assert auth_str.startswith("Basic ")
```

**Failing input**: `username='Ā', password='0'`

## Reproducing the Bug

```python
import requests.auth

result = requests.auth._basic_auth_str('Ā', 'password')

auth = requests.auth.HTTPBasicAuth('user_Ā', 'pass')
class MockRequest:
    def __init__(self):
        self.headers = {}
r = MockRequest()
auth(r)
```

## Why This Is A Bug

The function accepts Python strings as input but fails on valid Unicode strings that contain characters outside the latin-1 range. This violates the expected contract that string inputs should be handled properly. The issue affects international users who may have non-ASCII characters in their credentials. RFC 7617 recommends UTF-8 support for HTTP Basic Authentication.

## Fix

The bug occurs because the code uses latin-1 encoding which only supports characters 0-255. A fix would be to use UTF-8 encoding instead:

```diff
--- a/requests/auth.py
+++ b/requests/auth.py
@@ -54,10 +54,10 @@ def _basic_auth_str(username, password):
     # -- End Removal --
 
     if isinstance(username, str):
-        username = username.encode("latin1")
+        username = username.encode("utf-8")
 
     if isinstance(password, str):
-        password = password.encode("latin1")
+        password = password.encode("utf-8")
 
     authstr = "Basic " + to_native_string(
         b64encode(b":".join((username, password))).strip()
```