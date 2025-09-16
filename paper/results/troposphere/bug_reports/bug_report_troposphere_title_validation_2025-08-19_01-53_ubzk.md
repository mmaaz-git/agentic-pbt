# Bug Report: troposphere Title Validation Inconsistent with Python's isalnum()

**Target**: `troposphere.BaseAWSObject.validate_title`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The title validation regex in troposphere only accepts ASCII alphanumeric characters, but Python's `isalnum()` returns True for non-ASCII alphanumeric characters like 'ª', causing an inconsistency.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.iotwireless as iotwireless

@given(st.text(min_size=1, max_size=50))
def test_title_validation_consistency(title):
    """Test that title validation is consistent with Python's isalnum()."""
    try:
        obj = iotwireless.Destination(
            title=title,
            Expression="test",
            ExpressionType="RuleName",
            Name="TestDest"
        )
    except ValueError:
        if title and title.isalnum():
            raise AssertionError(f"Alphanumeric title {title!r} was rejected")
```

**Failing input**: `'ª'`

## Reproducing the Bug

```python
import troposphere.iotwireless as iotwireless

char = 'ª'
print(f"Python isalnum(): {char.isalnum()}")  # True

obj = iotwireless.Destination(
    title=char,
    Expression="test", 
    ExpressionType="RuleName",
    Name="TestDest"
)  # Raises ValueError: Name "ª" not alphanumeric
```

## Why This Is A Bug

The validation error message states the name is "not alphanumeric", but Python's built-in `isalnum()` method returns `True` for the character. This creates confusion as users may expect any character where `isalnum()` returns `True` to be accepted.

## Fix

Either update the error message to be more specific about ASCII-only requirements, or update the regex to accept all Unicode alphanumeric characters:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -68,7 +68,7 @@
 PARAMETER_TITLE_MAX: Final[int] = 255
 
 
-valid_names = re.compile(r"^[a-zA-Z0-9]+$")
+valid_names = re.compile(r"^[a-zA-Z0-9]+$")  # ASCII only
 
 
 def validate_title(self) -> None:
     if not self.title or not valid_names.match(self.title):
-        raise ValueError('Name "%s" not alphanumeric' % self.title)
+        raise ValueError('Name "%s" must contain only ASCII alphanumeric characters' % self.title)
```