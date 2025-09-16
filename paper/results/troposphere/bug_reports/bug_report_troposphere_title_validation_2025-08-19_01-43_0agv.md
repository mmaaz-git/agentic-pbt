# Bug Report: troposphere Title Validation Inconsistency

**Target**: `troposphere.BaseAWSObject.validate_title`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The title validation error message states "not alphanumeric" but rejects Unicode alphanumeric characters that Python's `isalnum()` accepts, creating a misleading error message.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.guardduty import Detector

@given(st.text(min_size=1, max_size=100))
def test_title_validation_property(title):
    """Title must be alphanumeric - matches regex ^[a-zA-Z0-9]+$"""
    try:
        detector = Detector(title, Enable=True)
        assert title.isalnum(), f"Non-alphanumeric title {title!r} was accepted"
    except ValueError as e:
        assert not title.isalnum(), f"Alphanumeric title {title!r} was rejected"
        assert 'not alphanumeric' in str(e)
```

**Failing input**: `'¹'` (superscript 1)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere.guardduty import Detector

test_char = '¹'
print(f"Python isalnum(): {test_char.isalnum()}")  # True

detector = Detector(test_char, Enable=True)  # Raises ValueError: Name "¹" not alphanumeric
```

## Why This Is A Bug

The error message claims the title is "not alphanumeric", but Python's `isalnum()` returns `True` for characters like '¹' and 'ª'. The actual requirement is ASCII-only alphanumeric characters ([a-zA-Z0-9]), but the error message is misleading. This violates the principle of least surprise and creates confusion about what constitutes valid input.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -325,7 +325,7 @@ class BaseAWSObject:
 
     def validate_title(self) -> None:
         if not self.title or not valid_names.match(self.title):
-            raise ValueError('Name "%s" not alphanumeric' % self.title)
+            raise ValueError('Name "%s" must contain only ASCII letters and numbers (a-z, A-Z, 0-9)' % self.title)
 
     def validate(self) -> None:
         pass
```