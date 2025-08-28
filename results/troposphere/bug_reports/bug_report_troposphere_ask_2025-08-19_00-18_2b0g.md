# Bug Report: troposphere.ask Misleading Title Validation Error Message

**Target**: `troposphere.ask.Skill` and all `troposphere` AWS resource classes
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The title validation error message incorrectly states that Unicode alphanumeric characters are "not alphanumeric" when they fail validation, even though they are alphanumeric according to Python's `isalnum()` method.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.ask as ask

# Strategy generates Unicode letters that are alphanumeric but not ASCII
valid_titles = st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50)

@given(valid_titles)
def test_skill_title_validation(title):
    skill = ask.Skill(title)  # Fails with Unicode characters like 'µ'
```

**Failing input**: `'µ'`

## Reproducing the Bug

```python
import troposphere.ask as ask

title = 'µ'
assert title.isalnum() == True

skill = ask.Skill(title)
```

## Why This Is A Bug

The validation regex `^[a-zA-Z0-9]+$` only accepts ASCII alphanumeric characters, which is correct per AWS CloudFormation requirements. However, the error message "Name 'µ' not alphanumeric" is misleading because:

1. The character 'µ' IS alphanumeric according to Python's `isalnum()` method
2. The actual requirement is ASCII-only alphanumeric characters
3. The error message should clarify that only ASCII alphanumeric characters are allowed

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -325,7 +325,7 @@ class BaseAWSObject:
 
     def validate_title(self) -> None:
         if not self.title or not valid_names.match(self.title):
-            raise ValueError('Name "%s" not alphanumeric' % self.title)
+            raise ValueError('Name "%s" must contain only ASCII alphanumeric characters (A-Z, a-z, 0-9)' % self.title)
 
     def validate(self) -> None:
         pass
```