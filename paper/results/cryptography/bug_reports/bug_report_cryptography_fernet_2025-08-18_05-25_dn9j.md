# Bug Report: cryptography.fernet ValueError on Non-ASCII Token Strings

**Target**: `cryptography.fernet`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Fernet methods that accept tokens raise `ValueError` instead of `InvalidToken` when given string tokens containing non-ASCII characters, violating the API contract.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from cryptography.fernet import Fernet, InvalidToken
import pytest

@given(st.text(min_size=1).filter(lambda x: any(ord(c) > 127 for c in x)))
def test_fernet_invalid_token_format(invalid_token):
    """Test that malformed tokens are rejected with InvalidToken."""
    key = Fernet.generate_key()
    f = Fernet(key)
    
    with pytest.raises(InvalidToken):
        f.decrypt(invalid_token)
```

**Failing input**: `'\x81'`

## Reproducing the Bug

```python
from cryptography.fernet import Fernet, InvalidToken

key = Fernet.generate_key()
f = Fernet(key)

try:
    f.decrypt('\x81')
except InvalidToken:
    print("InvalidToken raised (expected)")
except ValueError as e:
    print(f"ValueError raised (bug): {e}")
```

## Why This Is A Bug

The `_get_unverified_token_data` method in Fernet attempts to catch base64 decoding errors and convert them to `InvalidToken` exceptions. However, it only catches `TypeError` and `binascii.Error`, missing `ValueError` that `base64.urlsafe_b64decode` raises for non-ASCII strings. This violates the API contract where all invalid tokens should raise `InvalidToken`, creating inconsistent error handling that could break client code expecting only `InvalidToken` exceptions.

## Fix

```diff
@@ -112,7 +112,7 @@ class Fernet:
 
         try:
             data = base64.urlsafe_b64decode(token)
-        except (TypeError, binascii.Error):
+        except (TypeError, binascii.Error, ValueError):
             raise InvalidToken
 
         if not data or data[0] != 0x80:
```