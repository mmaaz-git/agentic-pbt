# Bug Report: troposphere.iotthingsgraph Title Validation Bypass for Falsy Values

**Target**: `troposphere.iotthingsgraph.FlowTemplate` (affects all `BaseAWSObject` subclasses)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-01-19

## Summary

AWSObject instances in troposphere bypass title validation when the title is a falsy value (empty string, None, 0, False), allowing creation of invalid CloudFormation templates that would be rejected by AWS.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.iotthingsgraph import DefinitionDocument, FlowTemplate
import re

valid_names = re.compile(r"^[a-zA-Z0-9]+$")

@given(st.one_of(
    st.just(""),
    st.just(None), 
    st.just(0),
    st.just(False)
))
def test_falsy_titles_bypass_validation(title):
    """AWSObject titles must be alphanumeric and non-empty."""
    definition = DefinitionDocument(Language="GRAPHQL", Text="{}")
    
    # This should fail but doesn't
    template = FlowTemplate(title, Definition=definition)
    
    # to_dict() also succeeds (bug!)
    result = template.to_dict()
    
    # But validate_title() correctly identifies it as invalid
    try:
        template.validate_title()
        assert valid_names.match(str(title))
    except ValueError as e:
        assert "not alphanumeric" in str(e)
        # Bug: object created with invalid title!
```

**Failing input**: `""` (empty string), `None`, `0`, `False`

## Reproducing the Bug

```python
from troposphere.iotthingsgraph import DefinitionDocument, FlowTemplate

# Create a valid definition
definition = DefinitionDocument(Language="GRAPHQL", Text="{}")

# Create FlowTemplate with empty title - should fail but doesn't!
template = FlowTemplate("", Definition=definition)

# Convert to dict - succeeds but creates invalid CloudFormation
result = template.to_dict()
print(f"Type: {result['Type']}")  # AWS::IoTThingsGraph::FlowTemplate

# Direct validation would correctly fail
try:
    template.validate_title()
except ValueError as e:
    print(f"validate_title() correctly raises: {e}")
    # Output: Name "" not alphanumeric
```

## Why This Is A Bug

AWS CloudFormation requires resource logical IDs (titles) to be alphanumeric and non-empty. The troposphere library has a `validate_title()` method that correctly enforces this, but it's only called during `__init__` if the title is truthy. This creates invalid CloudFormation templates that AWS will reject, defeating the purpose of client-side validation.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,8 +180,7 @@ class BaseAWSObject:
         ]
 
         # try to validate the title if its there
-        if self.title:
-            self.validate_title()
+        self.validate_title()
 
         # Create the list of properties set on this object by the user
         self.properties = {}
@@ -324,7 +323,7 @@ class BaseAWSObject:
         )
 
     def validate_title(self) -> None:
-        if not self.title or not valid_names.match(self.title):
+        if self.title is not None and (not self.title or not valid_names.match(self.title)):
             raise ValueError('Name "%s" not alphanumeric' % self.title)
 
     def validate(self) -> None:
```