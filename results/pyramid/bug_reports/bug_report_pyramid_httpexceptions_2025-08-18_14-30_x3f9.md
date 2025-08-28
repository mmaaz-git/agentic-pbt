# Bug Report: pyramid.httpexceptions HTTP Redirect Exceptions Crash with Control Characters in Location

**Target**: `pyramid.httpexceptions._HTTPMove` and subclasses
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

HTTP redirect exception classes (HTTPFound, HTTPMovedPermanently, etc.) crash during construction when the location parameter contains control characters like `\r` or `\n`, raising ValueError instead of handling or sanitizing the input.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pyramid.httpexceptions as httpexc
import pytest

REDIRECT_CLASSES = [
    httpexc.HTTPFound,
    httpexc.HTTPMovedPermanently,
    httpexc.HTTPSeeOther,
    # ... other redirect classes
]

@given(
    st.sampled_from(REDIRECT_CLASSES),
    st.text(min_size=1, max_size=200)
)
def test_httpmove_preserves_location(redirect_class, location):
    """HTTPMove subclasses should preserve the location parameter"""
    exc = redirect_class(location=location)
    assert 'Location' in exc.headers
    assert exc.headers['Location'] == location
```

**Failing input**: `HTTPFound(location='0\r')`

## Reproducing the Bug

```python
import pyramid.httpexceptions as httpexc

# This crashes with ValueError
try:
    exc = httpexc.HTTPFound(location='http://example.com/path\r\nX-Injected: malicious')
except ValueError as e:
    print(f"Error: {e}")  # "Header value may not contain control characters"

# Real-world scenario: user input in redirect
def handle_form(next_url):
    # Developer expects this to work or produce HTTP exception, not ValueError
    return httpexc.HTTPFound(location=f'/success?next={next_url}')

# Attacker input causes unexpected ValueError
malicious = 'page\r\nSet-Cookie: admin=true'
handle_form(malicious)  # Crashes with ValueError
```

## Why This Is A Bug

1. **Inconsistent behavior**: The exception classes are meant to be response objects that can be constructed and returned from views, but they crash on certain inputs rather than handling them gracefully.

2. **Unexpected exception type**: Developers expect HTTP exceptions or proper validation, not ValueError during construction.

3. **Security implications**: While WebOb's validation prevents header injection (good), the error occurs at construction time rather than allowing the application to handle invalid input appropriately.

## Fix

```diff
--- a/pyramid/httpexceptions.py
+++ b/pyramid/httpexceptions.py
@@ -532,6 +532,11 @@ class _HTTPMove(HTTPRedirection):
     ):
         if location is None:
             raise ValueError("HTTP redirects need a location to redirect to.")
+        # Validate location doesn't contain control characters
+        if isinstance(location, str):
+            if any(c in location for c in ['\r', '\n', '\x00']):
+                # Either sanitize or raise a more specific error
+                location = ''.join(c for c in location if c not in ['\r', '\n', '\x00'])
         super().__init__(
             detail=detail,
             headers=headers,
```

Alternatively, document that location parameters must be pre-validated and may raise ValueError if they contain control characters.