# Bug Report: troposphere.iotevents Title Validation Bypass

**Target**: `troposphere.iotevents` (and all troposphere AWS resources)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Title validation in troposphere resources can be bypassed by using falsy non-string values (0, False, None), allowing invalid types to be used as resource titles when only alphanumeric strings should be accepted.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.iotevents as iotevents

@given(title=st.one_of(
    st.integers(),
    st.booleans(),
    st.none(),
    st.text(min_size=0, max_size=0)  # empty string
))
def test_title_must_be_valid_string(title):
    # Title should be a non-empty alphanumeric string
    try:
        obj = iotevents.Input(
            title=title,
            InputDefinition=iotevents.InputDefinition(
                Attributes=[iotevents.Attribute(JsonPath="/test")]
            )
        )
        # If we get here, check the title type
        assert isinstance(obj.title, str), f"Title {title!r} was accepted but isn't a string"
        assert obj.title, "Empty string shouldn't be accepted as title"
        assert obj.title.isalnum(), f"Title {obj.title!r} should be alphanumeric"
        # These assertions will fail for the bug cases
    except (ValueError, TypeError):
        # Expected for invalid titles
        pass
```

**Failing input**: `0` (integer), `False` (boolean), `None`, `""` (empty string)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.iotevents as iotevents

# Bug: Integer 0 is accepted as a title
obj = iotevents.Input(
    title=0,  # Should fail but doesn't!
    InputDefinition=iotevents.InputDefinition(
        Attributes=[iotevents.Attribute(JsonPath="/test")]
    )
)
print(f"Created object with title: {obj.title} (type: {type(obj.title).__name__})")

# Also works with False
obj2 = iotevents.Input(
    title=False,  # Should fail but doesn't!
    InputDefinition=iotevents.InputDefinition(
        Attributes=[iotevents.Attribute(JsonPath="/test")]
    )
)
print(f"Created object with title: {obj2.title} (type: {type(obj2.title).__name__})")
```

## Why This Is A Bug

The troposphere library documentation and code clearly indicate that resource titles must be alphanumeric strings matching the regex `^[a-zA-Z0-9]+$`. However, due to flawed validation logic, falsy non-string values bypass validation entirely, while truthy non-string values fail with confusing error messages. This violates the API contract and could lead to unexpected behavior when these resources are used in CloudFormation templates.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,8 +180,11 @@ class BaseAWSObject:
         ]
 
         # try to validate the title if its there
-        if self.title:
+        if self.title is not None:
             self.validate_title()
 
         # Create the list of properties set on this object by the user
         self.properties = {}
@@ -324,7 +327,10 @@ class BaseAWSObject:
         )
 
     def validate_title(self) -> None:
-        if not self.title or not valid_names.match(self.title):
+        if not isinstance(self.title, str):
+            raise ValueError('Name must be a string, got %s' % type(self.title).__name__)
+        if not self.title:
+            raise ValueError('Name cannot be empty')
+        if not valid_names.match(self.title):
             raise ValueError('Name "%s" not alphanumeric' % self.title)
 
     def validate(self) -> None:
```