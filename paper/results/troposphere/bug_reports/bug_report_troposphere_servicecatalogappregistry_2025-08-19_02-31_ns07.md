# Bug Report: troposphere.servicecatalogappregistry Empty String Validation

**Target**: `troposphere.servicecatalogappregistry`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Required string fields in all Service Catalog App Registry resource classes incorrectly accept empty strings and whitespace-only strings, violating CloudFormation's validation requirements.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.servicecatalogappregistry as module


@given(st.sampled_from(['', ' ', '  ', '\t', '\n', '   \t   ']))
def test_empty_string_accepted_for_required_fields(empty_value):
    """Bug: Required Name fields accept empty/whitespace-only strings"""
    app = module.Application('TestApp', Name=empty_value)
    result = app.to_dict()
    
    assert result['Properties']['Name'] == empty_value
    assert module.Application.props['Name'][1] == True  # Field is marked as required
```

**Failing input**: `''` (empty string)

## Reproducing the Bug

```python
import troposphere.servicecatalogappregistry as module

# All these should fail validation but don't
app = module.Application('App', Name='')
print(app.to_dict())
# Output: {'Properties': {'Name': ''}, 'Type': 'AWS::ServiceCatalogAppRegistry::Application'}

ag = module.AttributeGroup('AG', Name='', Attributes={'key': 'val'})
print(ag.to_dict())
# Output: {'Properties': {'Name': '', 'Attributes': {'key': 'val'}}, 'Type': 'AWS::ServiceCatalogAppRegistry::AttributeGroup'}

ra = module.ResourceAssociation('RA', Application='', Resource='', ResourceType='')
print(ra.to_dict())
# Output: {'Properties': {'Application': '', 'Resource': '', 'ResourceType': ''}, 'Type': 'AWS::ServiceCatalogAppRegistry::ResourceAssociation'}
```

## Why This Is A Bug

1. CloudFormation rejects empty strings for required Name fields in actual deployments
2. The troposphere library marks these fields as required (`True` in the props definition) but doesn't enforce non-empty validation
3. This creates a false sense of security - templates pass troposphere validation but fail in CloudFormation
4. Affects all resource types in the module: Application, AttributeGroup, AttributeGroupAssociation, and ResourceAssociation

## Fix

The validation logic should check that required string fields are not empty or whitespace-only. The fix would need to be applied in the parent AWSObject class validation method:

```diff
# In troposphere/__init__.py or validation logic
def validate_property(self, prop_name, prop_value, prop_type, required):
    if required and prop_value is None:
        raise ValueError(f"{prop_name} is required")
    
    if prop_type == str and prop_value is not None:
        if not isinstance(prop_value, str):
            raise TypeError(f"{prop_name} must be a string")
+       if required and not prop_value.strip():
+           raise ValueError(f"{prop_name} is required and cannot be empty or whitespace-only")
```