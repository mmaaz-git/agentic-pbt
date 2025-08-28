# Bug Report: troposphere.arczonalshift None Values for Optional Properties Rejected

**Target**: `troposphere.arczonalshift` (and likely all troposphere modules)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Optional properties in troposphere AWS resource classes reject None values, even though they are marked as optional. This violates the expected API contract where optional properties should accept None to indicate absence.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.arczonalshift import ZonalAutoshiftConfiguration

@given(resource_id=st.text(min_size=1))
def test_none_values_for_optional_properties(resource_id):
    """None values for optional properties should work correctly"""
    config = ZonalAutoshiftConfiguration(
        "TestConfig",
        ResourceIdentifier=resource_id,
        PracticeRunConfiguration=None,  # Optional property (False in props)
        ZonalAutoshiftStatus=None       # Optional property (False in props)
    )
    result = config.to_dict(validation=True)
    assert 'PracticeRunConfiguration' not in result['Properties']
    assert 'ZonalAutoshiftStatus' not in result['Properties']
```

**Failing input**: Any valid input triggers this bug when None is passed for optional properties

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.arczonalshift import ZonalAutoshiftConfiguration

config = ZonalAutoshiftConfiguration(
    "TestConfig",
    ResourceIdentifier="test-resource",
    PracticeRunConfiguration=None
)
```

## Why This Is A Bug

The properties are defined as optional in the class definition:
- `PracticeRunConfiguration: (PracticeRunConfiguration, False)` - False means optional
- `ZonalAutoshiftStatus: (str, False)` - False means optional

However, the type validation logic in `BaseAWSObject.__setattr__` (line 302-305 in `__init__.py`) doesn't check if a property is optional before rejecting None values. It only checks if the value matches the expected type, causing TypeError for None values even on optional properties.

This creates an inconsistency:
- Omitting an optional property entirely works fine
- Explicitly setting an optional property to None fails with TypeError

This violates the principle of least surprise and the typical Python/CloudFormation pattern where None indicates absence of an optional value.

## Fix

The bug can be fixed by checking if a property is optional and allowing None values for optional properties:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -248,6 +248,11 @@ class BaseAWSObject:
             return None
         elif name in self.propnames:
             # Check the type of the object and compare against what we were
             # expecting.
             expected_type = self.props[name][0]
+            is_required = self.props[name][1]
+            
+            # Allow None for optional properties
+            if not is_required and value is None:
+                return self.properties.__setitem__(name, value)
 
             # If the value is a AWSHelperFn we can't do much validation
```