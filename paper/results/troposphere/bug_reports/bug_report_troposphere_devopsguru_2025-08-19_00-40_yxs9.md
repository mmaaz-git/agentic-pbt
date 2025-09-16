# Bug Report: troposphere.devopsguru Misleading Alphanumeric Validation Error

**Target**: `troposphere.devopsguru` (all AWS resource classes)
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The title validation error message claims a title is "not alphanumeric" when it rejects Unicode alphanumeric characters that Python's `isalnum()` considers valid, creating a misleading contract violation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.devopsguru import NotificationChannel, NotificationChannelConfig, SnsChannelConfig

unicode_alphanumeric_titles = st.text(min_size=1).filter(
    lambda x: x.isalnum() and not re.match(r'^[a-zA-Z0-9]+$', x)
)

@given(title=unicode_alphanumeric_titles)
def test_misleading_alphanumeric_error_message(title):
    config = NotificationChannelConfig(Sns=SnsChannelConfig(TopicArn="arn:aws:sns:us-east-1:123456789012:test"))
    try:
        nc = NotificationChannel(title, Config=config)
        nc.to_dict()
        assert False, f"Should have rejected title: {repr(title)}"
    except ValueError as e:
        assert 'not alphanumeric' in str(e)
        assert title.isalnum(), f"Title {repr(title)} is alphanumeric by Python's isalnum()"
```

**Failing input**: `'µ'` (Greek letter mu)

## Reproducing the Bug

```python
from troposphere.devopsguru import NotificationChannel, NotificationChannelConfig, SnsChannelConfig

config = NotificationChannelConfig(Sns=SnsChannelConfig(TopicArn="arn:aws:sns:us-east-1:123456789012:test"))
title = 'µ'

print(f"Python's isalnum(): {title.isalnum()}")

try:
    nc = NotificationChannel(title, Config=config)
    nc.to_dict()
except ValueError as e:
    print(f"Error: {e}")
```

## Why This Is A Bug

The error message states the title is "not alphanumeric" but Python's `isalnum()` returns `True` for characters like 'µ', 'ñ', 'é', etc. The actual validation uses `^[a-zA-Z0-9]+$` which only accepts ASCII letters and digits. This creates confusion as users may reasonably expect Unicode alphanumeric characters to be accepted when the error says "alphanumeric".

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