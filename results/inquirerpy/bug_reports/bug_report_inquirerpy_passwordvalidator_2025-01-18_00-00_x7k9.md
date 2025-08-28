# Bug Report: InquirerPy PasswordValidator length=0 Not Distinguished from length=None

**Target**: `InquirerPy.validator.PasswordValidator`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-01-18

## Summary

PasswordValidator treats `length=0` the same as `length=None` due to a falsy value check, preventing users from explicitly setting a minimum length of 0.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from InquirerPy.validator import PasswordValidator

@given(length=st.sampled_from([0, None]))
def test_password_validator_length_zero_vs_none(length):
    validator = PasswordValidator(length=length)
    # The regex patterns should be different for length=0 vs length=None
    # but they are the same due to the bug
    if length == 0:
        expected_pattern = r"^.{0,}$"  # Explicit 0 minimum
    else:
        expected_pattern = r"^.*$"      # No length constraint
    
    actual_pattern = validator._re.pattern
    assert actual_pattern == expected_pattern, f"length={length} produces wrong pattern"
```

**Failing input**: `length=0`

## Reproducing the Bug

```python
from InquirerPy.validator import PasswordValidator

# Create validators with length=0 and length=None
validator_zero = PasswordValidator(length=0)
validator_none = PasswordValidator(length=None)

# Both produce the same regex pattern (bug!)
print(f"length=0 pattern: {validator_zero._re.pattern}")
print(f"length=None pattern: {validator_none._re.pattern}")
print(f"Are they the same? {validator_zero._re.pattern == validator_none._re.pattern}")

# Output:
# length=0 pattern: ^.*$
# length=None pattern: ^.*$
# Are they the same? True
```

## Why This Is A Bug

The code uses `if length:` to check if a length constraint was provided, but this treats `length=0` as falsy, making it indistinguishable from `length=None`. Users explicitly setting `length=0` expect to set a minimum length of 0, which is semantically different from not specifying a length constraint at all.

## Fix

```diff
--- a/InquirerPy/validator.py
+++ b/InquirerPy/validator.py
@@ -143,7 +143,7 @@ class PasswordValidator(Validator):
         if number:
             password_pattern += r"(?=.*[0-9])"
         password_pattern += r"."
-        if length:
+        if length is not None:
             password_pattern += r"{%s,}" % length
         else:
             password_pattern += r"*"
```