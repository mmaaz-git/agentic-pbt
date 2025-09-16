# Bug Report: troposphere.chatbot Optional Properties Reject None

**Target**: `troposphere.chatbot`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Optional properties in troposphere.chatbot classes incorrectly raise TypeError when explicitly set to None, despite being marked as optional in their property definitions.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from troposphere import chatbot

@given(
    button_text=st.text(min_size=0, max_size=100),
    operator=st.sampled_from(["=", "!=", ">", "<", ">=", "<=", "CONTAINS", "NOT_CONTAINS"]),
    var_name=st.text(min_size=1, max_size=50),
    value=st.text(min_size=0, max_size=100),
    notification_type=st.text(min_size=1, max_size=50),
    num_attachments=st.integers(min_value=0, max_value=10)
)
@settings(max_examples=200)
def test_custom_action_complex_attachments(button_text, operator, var_name, value, notification_type, num_attachments):
    attachments = []
    for i in range(num_attachments):
        criteria = chatbot.CustomActionAttachmentCriteria(
            Operator=operator,
            VariableName=f"{var_name}_{i}",
            Value=value if value else None  # This fails when None
        )
        # ... rest of test
```

**Failing input**: `value='', num_attachments=1` (causes Value=None to be passed)

## Reproducing the Bug

```python
from troposphere import chatbot

# Works: omitting optional property
criteria1 = chatbot.CustomActionAttachmentCriteria(
    Operator="=",
    VariableName="test_var"
)

# Fails: explicitly setting optional property to None
criteria2 = chatbot.CustomActionAttachmentCriteria(
    Operator="=", 
    VariableName="test_var",
    Value=None  # TypeError: expected <class 'str'>
)

# Additional affected properties:
attachment = chatbot.CustomActionAttachment(ButtonText=None)  # Fails
action = chatbot.CustomAction("test")
action.AliasName = None  # Fails

slack = chatbot.SlackChannelConfiguration("test")
slack.LoggingLevel = None  # Fails with validation error
```

## Why This Is A Bug

The props definitions mark these properties as optional (False), meaning they should be omissible. However, the type validation in `__setattr__` doesn't properly handle None values for optional properties. This creates an inconsistency where:

1. Omitting the property entirely works (property not set)
2. Setting the property to None fails with TypeError
3. This violates the expected contract that optional properties should accept None

## Fix

The issue is in the BaseAWSObject.__setattr__ method in troposphere/__init__.py. When a property value is None and the property is optional, it should either skip validation or remove the property, not raise a TypeError.

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -299,6 +299,10 @@ class BaseAWSObject:
             # Final validity check, compare the type of value against
             # expected_type which should now be either a single type or
             # a tuple of types.
+            elif value is None and not self.props[name][1]:
+                # If value is None and property is optional, skip it
+                return None
             elif isinstance(value, cast(type, expected_type)):
                 return self.properties.__setitem__(name, value)
             else:
```