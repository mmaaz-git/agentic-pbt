# Bug Report: troposphere.elasticbeanstalk Misleading "not alphanumeric" Error Message

**Target**: `troposphere.elasticbeanstalk.Application` (and all AWSObject subclasses)
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The title validation error message claims a name is "not alphanumeric" when rejecting Unicode alphanumeric characters like 'ª', '²', 'µ', but these characters ARE alphanumeric according to Python's `isalnum()` method.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.elasticbeanstalk as eb

@given(st.text(min_size=1))
def test_title_validation(title):
    """AWSObject titles must be alphanumeric only."""
    is_alphanumeric = title.isalnum()
    
    try:
        app = eb.Application(title)
        assert is_alphanumeric, f"Non-alphanumeric title '{title}' was incorrectly accepted"
    except ValueError as e:
        assert not is_alphanumeric, f"Alphanumeric title '{title}' was incorrectly rejected"
        assert 'not alphanumeric' in str(e)
```

**Failing input**: `'ª'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.elasticbeanstalk as eb

test_char = 'ª'
print(f"Python isalnum(): {test_char.isalnum()}")  # True

try:
    app = eb.Application(test_char)
except ValueError as e:
    print(f"Error: {e}")  # Name "ª" not alphanumeric
```

## Why This Is A Bug

The error message "not alphanumeric" is misleading because:
1. Python's `isalnum()` returns `True` for Unicode alphanumeric characters like 'ª', '²', 'µ'
2. The actual validation uses regex `^[a-zA-Z0-9]+$` which only accepts ASCII alphanumerics
3. The error message contradicts Python's definition of "alphanumeric"

This violates the API contract implied by the error message. Users seeing "not alphanumeric" would reasonably expect that `isalnum()` returns False, but it returns True.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -325,7 +325,7 @@ class BaseAWSObject:
 
     def validate_title(self) -> None:
         if not self.title or not valid_names.match(self.title):
-            raise ValueError('Name "%s" not alphanumeric' % self.title)
+            raise ValueError('Name "%s" must contain only ASCII letters and digits (a-z, A-Z, 0-9)' % self.title)
 
     def validate(self) -> None:
         pass
```