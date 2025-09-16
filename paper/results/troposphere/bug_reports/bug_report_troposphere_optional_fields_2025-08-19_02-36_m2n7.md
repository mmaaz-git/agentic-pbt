# Bug Report: troposphere Optional Fields Reject None Values

**Target**: `troposphere.BaseAWSObject`
**Severity**: Medium  
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Optional fields in troposphere AWS resources reject `None` values with a TypeError, even though they are marked as optional in the props definition. This forces users to omit optional fields entirely rather than explicitly setting them to None.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.kendraranking as kr

@given(
    name=st.text(min_size=1),
    description=st.one_of(st.text(), st.none())
)
def test_optional_field_accepts_none(name, description):
    plan = kr.ExecutionPlan(
        "TestPlan",
        Name=name,
        Description=description
    )
    if description is None:
        assert 'Description' not in plan.properties or plan.properties['Description'] is None
```

**Failing input**: `description=None`

## Reproducing the Bug

```python
import troposphere.kendraranking as kr

plan = kr.ExecutionPlan(
    "MyPlan",
    Name="TestPlan",
    Description=None
)
```

## Why This Is A Bug

The `Description` field is marked as optional (`False`) in the props definition, indicating it's not required. However, when explicitly passing `None` for this optional field, the code raises a TypeError expecting a string. This violates the principle that optional fields should accept None values. Users must completely omit optional fields instead of being able to explicitly set them to None, which is inconsistent with typical Python conventions.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -247,6 +247,10 @@ class BaseAWSObject:
                 self.resource[name] = value
             return None
         elif name in self.propnames:
+            # Allow None for optional properties
+            if value is None and not self.props[name][1]:
+                return None  # Don't set the property if None and optional
+            
             # Check the type of the object and compare against what we were
             # expecting.
             expected_type = self.props[name][0]
```