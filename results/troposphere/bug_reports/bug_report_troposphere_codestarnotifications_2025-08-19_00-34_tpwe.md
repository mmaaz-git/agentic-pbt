# Bug Report: troposphere.codestarnotifications Empty List Validation

**Target**: `troposphere.codestarnotifications`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The troposphere.codestarnotifications module accepts empty lists for required properties EventTypeIds and Targets, which violates AWS CloudFormation requirements and will cause deployment failures.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
import troposphere.codestarnotifications as csn

@given(empty_list=st.just([]))
def test_empty_event_type_ids(empty_list):
    """Test behavior with empty EventTypeIds list"""
    target = csn.Target(TargetAddress="arn:test", TargetType="SNS")
    
    with pytest.raises((ValueError, TypeError)):
        # Empty EventTypeIds should fail validation
        rule = csn.NotificationRule(
            "Rule",
            Name="Test",
            DetailType="BASIC",
            EventTypeIds=empty_list,  # Empty list
            Resource="arn:resource",
            Targets=[target]
        )
        rule.to_dict()
```

**Failing input**: `empty_list=[]`

## Reproducing the Bug

```python
import troposphere.codestarnotifications as csn

# Create NotificationRule with empty EventTypeIds
rule = csn.NotificationRule(
    "MyRule",
    Name="TestNotification",
    DetailType="BASIC",
    EventTypeIds=[],  # Empty list - should be rejected
    Resource="arn:aws:codecommit:us-east-1:123456789012:MyRepo",
    Targets=[csn.Target(TargetAddress="arn:aws:sns:us-east-1:123456789012:topic", TargetType="SNS")]
)

# Generate CloudFormation template
template = rule.to_dict()
print("Generated template with empty EventTypeIds:")
print(template['Properties']['EventTypeIds'])  # Outputs: []

# Similarly for empty Targets:
rule2 = csn.NotificationRule(
    "MyRule2",
    Name="TestNotification",
    DetailType="BASIC",
    EventTypeIds=["event1"],
    Resource="arn:aws:codecommit:us-east-1:123456789012:MyRepo",
    Targets=[]  # Empty targets list
)

template2 = rule2.to_dict()
print("Generated template with empty Targets:")
print(template2['Properties']['Targets'])  # Outputs: []
```

## Why This Is A Bug

AWS CloudFormation requires that both EventTypeIds and Targets have at least one element. When the generated template is deployed, CloudFormation will fail with:
- "Property validation failure: [The property EventTypeIds must have at least 1 element(s)]"
- "Property validation failure: [The property Targets must have at least 1 element(s)]"

Troposphere should validate these constraints to prevent invalid templates from being generated.

## Fix

The module should validate that required list properties contain at least one element. This could be implemented by adding validators to check minimum list length:

```diff
--- a/troposphere/codestarnotifications.py
+++ b/troposphere/codestarnotifications.py
@@ -7,6 +7,11 @@
 
 
 from . import AWSObject, AWSProperty, PropsDictType
+from .validators import validate_list_min_length
+
+def validate_non_empty_list(x):
+    if not isinstance(x, list) or len(x) == 0:
+        raise ValueError("List must contain at least one element")
+    return x
 
 
 class Target(AWSProperty):
@@ -31,8 +36,8 @@ class NotificationRule(AWSObject):
     props: PropsDictType = {
         "CreatedBy": (str, False),
         "DetailType": (str, True),
         "EventTypeId": (str, False),
-        "EventTypeIds": ([str], True),
+        "EventTypeIds": (validate_non_empty_list, True),
         "Name": (str, True),
         "Resource": (str, True),
         "Status": (str, False),
         "Tags": (dict, False),
         "TargetAddress": (str, False),
-        "Targets": ([Target], True),
+        "Targets": (validate_non_empty_list, True),
     }
```