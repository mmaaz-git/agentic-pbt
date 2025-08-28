# Bug Report: OAuth2Session Missing Callable Validation for Compliance Hooks

**Target**: `requests_oauthlib.oauth2_session.OAuth2Session.register_compliance_hook`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `register_compliance_hook` method accepts non-callable objects (None, strings, integers, etc.) without validation, causing runtime TypeErrors when hooks are invoked.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from requests_oauthlib import OAuth2Session

@given(st.one_of(
    st.none(),
    st.text(),
    st.integers(),
    st.floats(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text())
))
def test_hook_must_be_callable(non_callable_value):
    session = OAuth2Session(client_id="test")
    
    # This should reject non-callable values but doesn't
    session.register_compliance_hook("protected_request", non_callable_value)
    
    # The non-callable is accepted and stored
    assert non_callable_value in session.compliance_hook["protected_request"]
    
    # This will cause TypeError when hooks are invoked later
```

**Failing input**: `None`, `"string"`, `42`, `[]`, `{}` - any non-callable object

## Reproducing the Bug

```python
from requests_oauthlib import OAuth2Session

session = OAuth2Session(client_id="test_client")

# Register None as a hook - this should fail but doesn't
session.register_compliance_hook("protected_request", None)

# Verify None was added to the hooks
print(None in session.compliance_hook["protected_request"])  # True

# Later, when making a request with a token, this will crash:
# session.token = {"access_token": "test_token", "token_type": "Bearer"}
# session.get("https://api.example.com/data")
# TypeError: 'NoneType' object is not callable
```

## Why This Is A Bug

The method violates the fail-fast principle by accepting invalid input at registration time that will cause errors at invocation time. The hooks are called with code like `hook(url, headers, data)` which requires `hook` to be callable. Accepting non-callable objects delays error detection until runtime, making debugging harder.

## Fix

```diff
--- a/oauth2_session.py
+++ b/oauth2_session.py
@@ -583,6 +583,8 @@ class OAuth2Session(requests.Session):
         if hook_type not in self.compliance_hook:
             raise ValueError(
                 "Hook type %s is not in %s.", hook_type, self.compliance_hook
             )
+        if not callable(hook):
+            raise TypeError("Hook must be callable, got %s" % type(hook).__name__)
         self.compliance_hook[hook_type].add(hook)
```