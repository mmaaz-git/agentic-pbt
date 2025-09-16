# Bug Report: troposphere.systemsmanagersap Round-Trip Serialization Failure

**Target**: `troposphere.systemsmanagersap.Application`, `troposphere.systemsmanagersap.Credential`, `troposphere.systemsmanagersap.ComponentInfo`
**Severity**: High
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `from_dict()` method cannot deserialize the output of `to_dict()`, violating the fundamental round-trip property that `from_dict(to_dict(x))` should preserve data.

## Property-Based Test

```python
@given(
    title=aws_id_strategy,
    app_id=aws_id_strategy,
    app_type=aws_type_strategy
)
def test_application_from_dict_handles_full_dict(title, app_id, app_type):
    """Test that Application.from_dict can handle the full output of to_dict"""
    app1 = sap.Application(title, ApplicationId=app_id, ApplicationType=app_type)
    full_dict = app1.to_dict()
    
    # This should work but doesn't - it's the bug
    app2 = sap.Application.from_dict(title + '_new', full_dict)
    dict2 = app2.to_dict()
    
    assert full_dict['Properties'] == dict2['Properties']
```

**Failing input**: `title='0', app_id='0', app_type='SAP/HANA'`

## Reproducing the Bug

```python
import troposphere.systemsmanagersap as sap

app1 = sap.Application('MyApp', ApplicationId='app-123', ApplicationType='SAP/HANA')
full_dict = app1.to_dict()
# Returns: {'Properties': {'ApplicationId': 'app-123', 'ApplicationType': 'SAP/HANA'}, 'Type': 'AWS::SystemsManagerSAP::Application'}

# This fails with AttributeError
app2 = sap.Application.from_dict('MyApp2', full_dict)
# AttributeError: Object type Application does not have a Properties property.
```

## Why This Is A Bug

The `to_dict()` method returns a dictionary with structure `{'Properties': {...}, 'Type': '...'}`, but `from_dict()` expects only the properties dictionary without the wrapper. This breaks the standard serialization/deserialization pattern that users expect to work for saving and loading CloudFormation templates.

## Fix

The `from_dict()` method should detect and handle the full dictionary structure produced by `to_dict()`:

```diff
@classmethod
def from_dict(cls, title, d):
+    # Handle both full dict (with Properties) and properties-only dict
+    if 'Properties' in d and 'Type' in d:
+        # Extract properties from full dict structure
+        return cls._from_dict(title, **d['Properties'])
     return cls._from_dict(title, **d)
```