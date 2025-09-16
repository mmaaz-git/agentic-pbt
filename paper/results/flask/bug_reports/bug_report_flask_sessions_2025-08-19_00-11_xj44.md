# Bug Report: flask.sessions Setting permanent Flag Incorrectly Modifies Session

**Target**: `flask.sessions.SecureCookieSession`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

Setting the `permanent` attribute on a `SecureCookieSession` incorrectly marks the session as modified and stores `_permanent` as a dictionary key, causing unnecessary Set-Cookie headers to be sent.

## Property-Based Test

```python
@given(st.booleans(), st.booleans())
def test_should_set_cookie_logic(modified, permanent):
    """should_set_cookie should follow documented logic."""
    app = flask.Flask(__name__)
    app.secret_key = "test-key"
    
    interface = flask.sessions.SecureCookieSessionInterface()
    session = flask.sessions.SecureCookieSession()
    
    # Set the session state
    if modified:
        session['key'] = 'value'  # This sets modified=True
    session.permanent = permanent  # BUG: This always sets modified=True
    
    # Test should_set_cookie
    should_set = interface.should_set_cookie(app, session)
    
    # Check actual config value
    refresh_each_request = app.config.get('SESSION_REFRESH_EACH_REQUEST', True)
    expected = modified or (permanent and refresh_each_request)
    assert should_set == expected
```

**Failing input**: `modified=False, permanent=False`

## Reproducing the Bug

```python
import flask.sessions

# Create a fresh session
session = flask.sessions.SecureCookieSession()
print(f"Initial state: modified={session.modified}")  # False

# Set permanent to its default value
session.permanent = False

print(f"After setting permanent: modified={session.modified}")  # True (BUG!)
print(f"Session keys: {list(session.keys())}")  # ['_permanent'] (BUG!)

# This causes should_set_cookie to incorrectly return True
app = flask.Flask(__name__)
app.secret_key = "key"
interface = flask.sessions.SecureCookieSessionInterface()
print(f"should_set_cookie: {interface.should_set_cookie(app, session)}")  # True (wrong!)
```

## Why This Is A Bug

1. Setting `permanent` to its default value (False) shouldn't modify the session
2. The `_permanent` key is incorrectly stored in the session dictionary itself, polluting the session data
3. This causes `should_set_cookie()` to return True for unmodified sessions, sending unnecessary Set-Cookie headers
4. It violates the documented contract that unmodified sessions don't trigger cookie updates

## Fix

The issue is that `permanent` is implemented as a property that stores its value in the session dictionary. The setter should check if the value is actually changing before marking the session as modified:

```diff
class SessionMixin:
    @property
    def permanent(self):
        return self.get('_permanent', False)
    
    @permanent.setter
    def permanent(self, value):
-       self['_permanent'] = value
+       # Only modify if the value is actually changing
+       current = self.get('_permanent', False)
+       if current != value:
+           self['_permanent'] = value
```

Alternatively, the `_permanent` flag should be stored as an instance attribute rather than in the session dictionary to avoid polluting session data.