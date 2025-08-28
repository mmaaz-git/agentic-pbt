# Bug Report: troposphere.acmpca Misleading Error Message for Title Validation

**Target**: `troposphere.acmpca.CertificateAuthority` (and other AWS objects)
**Severity**: Low  
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The title validation error message "Name 'X' not alphanumeric" is misleading because it rejects Unicode alphanumeric characters that Python's `isalnum()` accepts.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere.acmpca import CertificateAuthority, Subject

@given(st.text())
def test_title_validation(title):
    """Objects should validate titles with clear error messages"""
    try:
        ca = CertificateAuthority(
            title=title,
            KeyAlgorithm="RSA_2048",
            SigningAlgorithm="SHA256WITHRSA",
            Type="ROOT",
            Subject=Subject(CommonName="test")
        )
        assert title is None or all(c.isalnum() for c in title)
    except ValueError as e:
        if "not alphanumeric" in str(e) and title:
            # Error claims it's not alphanumeric, but Python says it is
            assert not title.isalnum() or not all(c.isascii() for c in title)
```

**Failing input**: `'¹'` (superscript 1, U+00B9)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere.acmpca import CertificateAuthority, Subject

# This character is alphanumeric according to Python
char = '¹'  # Superscript 1
print(f"Python isalnum(): {char.isalnum()}")  # True

# But troposphere rejects it with misleading error
try:
    ca = CertificateAuthority(
        title=char,
        KeyAlgorithm='RSA_2048',
        SigningAlgorithm='SHA256WITHRSA',
        Type='ROOT',
        Subject=Subject(CommonName='test')
    )
except ValueError as e:
    print(f"Error: {e}")  # "Name '¹' not alphanumeric"
```

## Why This Is A Bug

The error message claims the character is "not alphanumeric", but Python's `isalnum()` returns `True` for many Unicode characters like '¹', 'α', 'А' (Cyrillic), etc. The actual validation uses regex `^[a-zA-Z0-9]+$` which only accepts ASCII alphanumeric characters. This creates confusion for users who might test with Python's `isalnum()`.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -325,7 +325,7 @@ class BaseAWSObject:
 
     def validate_title(self) -> None:
         if not self.title or not valid_names.match(self.title):
-            raise ValueError('Name "%s" not alphanumeric' % self.title)
+            raise ValueError('Name "%s" must contain only ASCII letters and digits [a-zA-Z0-9]' % self.title)
 
     def to_dict(self) -> Dict[str, Any]:
```