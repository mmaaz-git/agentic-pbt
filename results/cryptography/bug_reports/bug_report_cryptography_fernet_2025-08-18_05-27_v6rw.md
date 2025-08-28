# Bug Report: cryptography.fernet Raises Wrong Exception for Non-ASCII Tokens

**Target**: `cryptography.fernet.Fernet` and `cryptography.fernet.MultiFernet`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Fernet's token decryption methods raise `ValueError` instead of `InvalidToken` when given non-ASCII string tokens, violating the documented API contract that all invalid tokens should raise `InvalidToken`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from cryptography.fernet import Fernet, InvalidToken

@st.composite
def fernet_keys(draw):
    raw_key = draw(st.binary(min_size=32, max_size=32))
    return base64.urlsafe_b64encode(raw_key)

@given(
    key=fernet_keys(),
    bad_token=st.text(min_size=1, max_size=100).filter(lambda x: not x.isspace())
)
def test_fernet_malformed_tokens(key, bad_token):
    f = Fernet(key)
    try:
        f.decrypt(bad_token)
        assert False, "Should have rejected malformed token"
    except (InvalidToken, TypeError):
        pass  # Expected
```

**Failing input**: `bad_token='\x80'` (any non-ASCII character)

## Reproducing the Bug

```python
from cryptography.fernet import Fernet, InvalidToken

key = Fernet.generate_key()
f = Fernet(key)

non_ascii_token = "\x80"

try:
    f.decrypt(non_ascii_token)
except ValueError as e:
    print(f"BUG: Got ValueError: {e}")
except InvalidToken:
    print("Got InvalidToken (expected)")
```

## Why This Is A Bug

The Fernet API documentation and consistent error handling patterns indicate that `InvalidToken` should be raised for ALL invalid tokens. The current behavior:

1. **Violates API contract**: Methods like `decrypt()`, `decrypt_at_time()`, and `extract_timestamp()` are documented to raise `InvalidToken` for invalid tokens
2. **Inconsistent error handling**: ASCII invalid tokens raise `InvalidToken`, but non-ASCII invalid tokens raise `ValueError`
3. **Breaks exception handling**: Code that catches `InvalidToken` to handle bad tokens will miss `ValueError`, potentially causing unexpected failures

This affects all token-accepting methods in both `Fernet` and `MultiFernet` classes.

## Fix

```diff
--- a/cryptography/fernet.py
+++ b/cryptography/fernet.py
@@ -112,7 +112,7 @@ class Fernet:
 
         try:
             data = base64.urlsafe_b64decode(token)
-        except (TypeError, binascii.Error):
+        except (TypeError, binascii.Error, ValueError):
             raise InvalidToken
 
         if not data or data[0] != 0x80:
```

The fix is simple: catch `ValueError` in addition to `TypeError` and `binascii.Error` when decoding the token, since `base64.urlsafe_b64decode()` raises `ValueError` for non-ASCII input strings.