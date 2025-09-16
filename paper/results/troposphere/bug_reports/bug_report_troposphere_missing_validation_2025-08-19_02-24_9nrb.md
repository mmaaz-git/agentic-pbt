# Bug Report: troposphere Missing Required Property Validation

**Target**: `troposphere.route53recoveryreadiness.ResourceSet.validate`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `validate()` method does not check for missing required properties as defined in the `props` dictionary, allowing invalid CloudFormation resources to pass validation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.route53recoveryreadiness import ResourceSet

@given(resource_set_name=st.text(min_size=1, max_size=100))
def test_resourceset_required_property_validation(resource_set_name):
    # ResourceSetType and Resources are marked as required (True) in props
    resource_set = ResourceSet(
        title="TestResourceSet",
        ResourceSetName=resource_set_name,
        # Missing required: ResourceSetType and Resources
    )
    
    # Should raise ValueError for missing required properties
    with pytest.raises(ValueError):
        resource_set.validate()
```

**Failing input**: `resource_set_name='0'`

## Reproducing the Bug

```python
from troposphere.route53recoveryreadiness import ResourceSet

print(f"ResourceSetType required: {ResourceSet.props['ResourceSetType'][1]}")
print(f"Resources required: {ResourceSet.props['Resources'][1]}")

resource_set = ResourceSet(
    title="TestResourceSet",
    ResourceSetName="MyResourceSet",
)

try:
    resource_set.validate()
    print("ERROR: validate() did not raise exception for missing required properties")
except ValueError as e:
    print(f"Correctly raised: {e}")
```

## Why This Is A Bug

The `props` dictionary clearly marks `ResourceSetType` and `Resources` as required (the second element of the tuple is `True`), but the `validate()` method does not enforce this requirement. This allows creation of invalid CloudFormation templates that will fail when deployed to AWS.

## Fix

The `validate()` method should check for missing required properties:

```diff
 def validate(self):
+    # Check for missing required properties
+    for prop_name, (prop_type, required) in self.props.items():
+        if required and prop_name not in self.properties:
+            raise ValueError(f"Required property '{prop_name}' is missing from {self.__class__.__name__}")
+    
     # Existing validation logic...
     super().validate()
```