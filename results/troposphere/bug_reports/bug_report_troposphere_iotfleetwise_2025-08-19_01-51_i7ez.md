# Bug Report: troposphere.iotfleetwise Optional Properties Reject None Values

**Target**: `troposphere.iotfleetwise` (affects all AWS resource classes)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Optional properties in troposphere.iotfleetwise classes raise TypeError when explicitly set to None, despite being marked as optional. This creates inconsistent behavior between omitting a property and explicitly setting it to None.

## Property-Based Test

```python
import hypothesis.strategies as st
from hypothesis import given
import troposphere.iotfleetwise as iotfleetwise

@given(
    name=st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    signal_catalog_arn=st.text(min_size=20, max_size=100),
    state_props=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5),
    description=st.text(max_size=200),
)
def test_state_template_round_trip(name, signal_catalog_arn, state_props, description):
    """Test StateTemplate to_dict/from_dict round-trip."""
    original = iotfleetwise.StateTemplate(
        title="TestStateTemplate",
        Name=name,
        SignalCatalogArn=signal_catalog_arn,
        StateTemplateProperties=state_props,
        Description=description if description else None  # This fails when None
    )
    
    dict_repr = original.to_dict(validation=False)
    if "Properties" in dict_repr:
        props = dict_repr["Properties"]
        reconstructed = iotfleetwise.StateTemplate.from_dict("TestStateTemplate", props)
        assert original == reconstructed
```

**Failing input**: Any test case where `description` is an empty string, causing `Description=None` to be passed

## Reproducing the Bug

```python
import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")
import troposphere.iotfleetwise as iotfleetwise

# This works - omitting optional Description
fleet1 = iotfleetwise.Fleet(
    title="Fleet1",
    Id="fleet-1",
    SignalCatalogArn="arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/test"
)
print("✓ Created Fleet without Description")

# This fails - explicitly setting optional Description to None
fleet2 = iotfleetwise.Fleet(
    title="Fleet2",
    Id="fleet-2",
    SignalCatalogArn="arn:aws:iotfleetwise:us-east-1:123456789012:signal-catalog/test",
    Description=None
)
```

## Why This Is A Bug

1. The Description property is marked as optional (False) in the props definition, meaning it should accept None
2. There's inconsistent behavior: omitting a property works, but explicitly setting it to None fails
3. This violates Python conventions where None is commonly used for optional values
4. It breaks common patterns like dict unpacking where optional values may be None
5. Affects all optional string properties across the entire iotfleetwise module (7+ different classes)

## Fix

The bug is in the `BaseAWSObject.__setattr__` method in troposphere/__init__.py. It needs to check if a property is optional before validating the type when the value is None:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -249,6 +249,11 @@ class BaseAWSObject:
         elif name in self.propnames:
             # Check the type of the object and compare against what we were
             # expecting.
             expected_type = self.props[name][0]
+            is_required = self.props[name][1]
+            
+            # Allow None for optional properties
+            if value is None and not is_required:
+                return self.properties.__setitem__(name, value)
 
             # If the value is a AWSHelperFn we can't do much validation
             # we'll have to leave that to Amazon. Maybe there's another way
```