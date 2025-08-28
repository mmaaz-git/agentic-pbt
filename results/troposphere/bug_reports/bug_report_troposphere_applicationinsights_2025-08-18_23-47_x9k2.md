# Bug Report: troposphere.applicationinsights Title Validation Error Message Bug

**Target**: `troposphere.applicationinsights.Application` (and all AWS objects with title validation)
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The title validation in troposphere incorrectly reports Unicode alphanumeric characters as "not alphanumeric" despite them being valid according to Python's `isalnum()` method.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import troposphere.applicationinsights as appinsights

@given(st.text(min_size=0, max_size=20))
@settings(max_examples=100)
def test_title_validation(title):
    """Test Application title validation error message accuracy."""
    is_valid = bool(title and title.isalnum())
    
    try:
        app = appinsights.Application(
            title,
            ResourceGroupName="TestGroup"
        )
        if title and not is_valid:
            assert False, f"Invalid title {title!r} was accepted"
    except ValueError as e:
        if is_valid:
            assert False, f"Valid alphanumeric title {title!r} was rejected: {e}"
        assert "not alphanumeric" in str(e)
```

**Failing input**: `'¹'` (superscript 1)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.applicationinsights as appinsights

title = '¹'
print(f"Character '{title}' is alphanumeric: {title.isalnum()}")  # Prints: True

app = appinsights.Application(
    title,
    ResourceGroupName="TestGroup"
)
```

## Why This Is A Bug

The error message "Name '¹' not alphanumeric" is misleading because:
1. Python's `isalnum()` returns `True` for '¹', confirming it IS alphanumeric
2. The regex `^[a-zA-Z0-9]+$` only matches ASCII alphanumeric characters
3. The error message claims the character is "not alphanumeric" which contradicts Python's definition

This creates confusion as the error message is technically incorrect - the character IS alphanumeric, just not ASCII alphanumeric.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -325,7 +325,7 @@ class BaseAWSObject:
 
     def validate_title(self) -> None:
         if not self.title or not valid_names.match(self.title):
-            raise ValueError('Name "%s" not alphanumeric' % self.title)
+            raise ValueError('Name "%s" must contain only ASCII alphanumeric characters (a-z, A-Z, 0-9)' % self.title)
 
     def validate(self) -> None:
         pass
```