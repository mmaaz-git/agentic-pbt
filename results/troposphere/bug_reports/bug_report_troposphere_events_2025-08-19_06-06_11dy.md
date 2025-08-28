# Bug Report: troposphere.events Title Validation Bypass

**Target**: `troposphere.events` (BaseAWSObject classes)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The title validation in troposphere's AWSObject classes can be bypassed by using None or empty string values, creating objects with invalid titles that would fail explicit validation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.events as events

@given(st.sampled_from([None, ""]))
def test_title_validation_bypass(title):
    # Object creation succeeds (validation skipped)
    eb = events.EventBus(title, Name='test')
    
    # But the title is invalid according to validate_title
    try:
        eb.validate_title()
        assert False, f"validate_title() should have failed for {title!r}"
    except ValueError as e:
        assert "not alphanumeric" in str(e)
```

**Failing input**: `None` and `""`

## Reproducing the Bug

```python
import troposphere.events as events

# Create EventBus with None title - succeeds
eb1 = events.EventBus(None, Name='test-bus')
print(f"Created with None: {eb1.to_dict()}")

# Create EventBus with empty title - succeeds  
eb2 = events.EventBus("", Name='test-bus')
print(f"Created with empty: {eb2.to_dict()}")

# But validation would fail if called explicitly
for eb in [eb1, eb2]:
    try:
        eb.validate_title()
    except ValueError as e:
        print(f"Validation error: {e}")
```

## Why This Is A Bug

The `validate_title()` method checks `if not self.title or not valid_names.match(self.title)` indicating that None/empty titles should be invalid. However, the `__init__` method only calls validation when `if self.title:` is truthy, allowing falsy values to bypass the alphanumeric requirement. This creates inconsistent behavior where:

1. Objects can be created with invalid titles (None or empty string)
2. These same titles would fail if `validate_title()` is called directly
3. The validation logic contradicts the bypass logic

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,9 +180,8 @@ class BaseAWSObject(BaseAWSObjectAbstractClass):
         ]
 
-        # try to validate the title if its there
-        if self.title:
-            self.validate_title()
+        # Always validate the title
+        self.validate_title()
 
         # Create the list of properties set on this object by the user
         self.properties = {}
```