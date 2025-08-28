# Bug Report: django.middleware.csrf _unmask_cipher_token Contract Violation

**Target**: `django.middleware.csrf._unmask_cipher_token`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The internal function `_unmask_cipher_token` returns wrong-length results for invalid inputs instead of validating input and raising an exception, violating defensive programming principles and its implicit contract.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import django.middleware.csrf as csrf

@given(st.text(min_size=0, max_size=200))
def test_unmask_returns_correct_length(token):
    if len(token) == csrf.CSRF_TOKEN_LENGTH:
        result = csrf._unmask_cipher_token(token)
        assert len(result) == csrf.CSRF_SECRET_LENGTH
    else:
        result = csrf._unmask_cipher_token(token)
        assert len(result) == csrf.CSRF_SECRET_LENGTH
```

**Failing input**: `""`

## Reproducing the Bug

```python
import django
from django.conf import settings
settings.configure(DEBUG=True, SECRET_KEY='test', MIDDLEWARE=[], 
                  DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
django.setup()

import django.middleware.csrf as csrf

result = csrf._unmask_cipher_token("")
print(f"Result: {repr(result)}")
print(f"Length: {len(result)} (expected: {csrf.CSRF_SECRET_LENGTH})")

secret = csrf._get_new_csrf_string()
try:
    csrf._does_token_match("", secret)
except AssertionError:
    print("AssertionError in _does_token_match due to wrong-length unmask result")
```

## Why This Is A Bug

The function `_unmask_cipher_token` assumes it receives a 64-character token but doesn't validate this assumption. It returns wrong-length results (e.g., empty string for empty input) instead of the expected 32-character secret. This violates the contract that `_does_token_match` relies on, which asserts the unmasked result has length `CSRF_SECRET_LENGTH`. While not exploitable in current Django (validation happens earlier), this violates defensive programming principles.

## Fix

```diff
def _unmask_cipher_token(token):
    """
    Given a token (assumed to be a string of CSRF_ALLOWED_CHARS, of length
    CSRF_TOKEN_LENGTH, and that its first half is a mask), use it to decrypt
    the second half to produce the original secret.
    """
+   if len(token) != CSRF_TOKEN_LENGTH:
+       raise InvalidTokenFormat(REASON_INCORRECT_LENGTH)
    mask = token[:CSRF_SECRET_LENGTH]
    token = token[CSRF_SECRET_LENGTH:]
    chars = CSRF_ALLOWED_CHARS
    pairs = zip((chars.index(x) for x in token), (chars.index(x) for x in mask))
    return "".join(chars[x - y] for x, y in pairs)
```