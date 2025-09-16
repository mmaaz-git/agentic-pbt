# Bug Report: troposphere.redshiftserverless from_dict() Fails on Extra Fields

**Target**: `troposphere.redshiftserverless.ConfigParameter.from_dict` (and all AWSProperty classes)
**Severity**: Medium  
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `from_dict()` method raises AttributeError when the input dictionary contains extra fields, breaking compatibility with CloudFormation templates that commonly include metadata fields.

## Property-Based Test

```python
import troposphere.redshiftserverless as rs
from hypothesis import given, strategies as st

@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.text(min_size=0, max_size=50),
        min_size=3, max_size=10
    ).filter(lambda d: 'ParameterKey' in d and 'ParameterValue' in d)
)
def test_from_dict_extra_fields(data):
    """from_dict should handle extra fields gracefully."""
    # Ensure required fields are present
    data['ParameterKey'] = 'test_key'
    data['ParameterValue'] = 'test_value'
    
    # from_dict should ignore extra fields
    cp = rs.ConfigParameter.from_dict('Test', data)
    result = cp.to_dict()
    
    # Should only have the recognized fields
    assert result == {'ParameterKey': 'test_key', 'ParameterValue': 'test_value'}
```

**Failing input**: `{'ParameterKey': 'key', 'ParameterValue': 'value', 'ExtraField': 'data'}`

## Reproducing the Bug

```python
import troposphere.redshiftserverless as rs

data = {
    'ParameterKey': 'database',
    'ParameterValue': 'prod',
    'Description': 'Database parameter'
}

try:
    cp = rs.ConfigParameter.from_dict('DBConfig', data)
    print(f'Success: {cp.to_dict()}')
except AttributeError as e:
    print(f'Error: {e}')
```

## Why This Is A Bug

CloudFormation templates commonly include extra metadata fields like 'DependsOn', 'Metadata', 'Condition', and custom annotations. The from_dict() method should follow the robustness principle: "be liberal in what you accept, conservative in what you send." Currently, it fails when parsing real-world CloudFormation templates that contain standard CF metadata.

## Fix

The from_dict method should filter the input dictionary to only include recognized properties before instantiation:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -365,8 +365,10 @@ class BaseAWSObject:
     def _from_dict(cls, title=None, **d):
         prop_values = {}
         for prop_name, prop_value in d.items():
-            try:
-                prop_attrs = cls.props[prop_name]
+            if prop_name not in cls.props:
+                # Ignore extra fields not in props
+                continue
+            prop_attrs = cls.props[prop_name]
```