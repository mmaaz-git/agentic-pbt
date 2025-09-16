# Bug Report: InquirerPy.validator.PasswordValidator Negative Length Silently Rejects All Passwords

**Target**: `InquirerPy.validator.PasswordValidator`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

PasswordValidator silently accepts negative length values but creates a regex pattern that rejects all passwords, regardless of their actual length.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from prompt_toolkit.validation import ValidationError
import pytest
from unittest.mock import Mock
from InquirerPy.validator import PasswordValidator

def create_document(text):
    doc = Mock()
    doc.text = text
    doc.cursor_position = len(text)
    return doc

@given(st.integers(min_value=-100, max_value=-1))
def test_password_validator_negative_length(negative_length):
    """PasswordValidator with negative length should either raise an error or behave sensibly."""
    validator = PasswordValidator(length=negative_length)
    
    # Any password should fail with negative length due to regex .{-n,} never matching
    doc = create_document("anypassword123")
    with pytest.raises(ValidationError):
        validator.validate(doc)
    
    # Even empty string fails
    doc = create_document("")
    with pytest.raises(ValidationError):
        validator.validate(doc)
```

**Failing input**: `negative_length=-1` (or any negative value)

## Reproducing the Bug

```python
from unittest.mock import Mock
from InquirerPy.validator import PasswordValidator

def create_document(text):
    doc = Mock()
    doc.text = text
    doc.cursor_position = len(text)
    return doc

validator = PasswordValidator(length=-5)
print(f"Regex pattern created: {validator._re.pattern}")

test_passwords = ["", "a", "abc", "password", "verylongpassword123"]
for password in test_passwords:
    doc = create_document(password)
    try:
        validator.validate(doc)
        print(f"'{password}' - ACCEPTED")
    except:
        print(f"'{password}' - REJECTED")
```

## Why This Is A Bug

The PasswordValidator constructor accepts negative length values without validation, creating a regex pattern like `^.{-5,}$`. While Python's regex engine doesn't raise an error for this pattern, it never matches any string. This results in all passwords being rejected, which is unexpected behavior. Users would expect either:
1. An error when constructing the validator with negative length
2. Negative lengths to be treated as 0 (no minimum length)

The current behavior silently creates a validator that always fails, which could be confusing for users.

## Fix

```diff
--- a/InquirerPy/validator.py
+++ b/InquirerPy/validator.py
@@ -136,6 +136,8 @@ class PasswordValidator(Validator):
         number: bool = False,
     ) -> None:
         password_pattern = r"^"
+        if length is not None and length < 0:
+            raise ValueError(f"Password length cannot be negative (got {length})")
         if cap:
             password_pattern += r"(?=.*[A-Z])"
         if special:
```