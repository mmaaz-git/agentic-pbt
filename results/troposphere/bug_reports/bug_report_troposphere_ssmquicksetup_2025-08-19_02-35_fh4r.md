# Bug Report: troposphere.ssmquicksetup Round-Trip Serialization Failure

**Target**: `troposphere.ssmquicksetup.ConfigurationManager`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `ConfigurationManager.from_dict()` method cannot deserialize the output of `ConfigurationManager.to_dict()`, violating the fundamental round-trip property that `from_dict(to_dict(x))` should reconstruct the original object.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.ssmquicksetup import ConfigurationDefinition, ConfigurationManager

@given(
    title=st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and x.isalnum()),
    params=st.dictionaries(st.text(min_size=1), st.text(), min_size=1),
    type_str=st.text(min_size=1).filter(lambda x: x.strip())
)
def test_configuration_manager_round_trip(title, params, type_str):
    cd = ConfigurationDefinition(Parameters=params, Type=type_str)
    cm1 = ConfigurationManager(title, ConfigurationDefinitions=[cd])
    
    dict1 = cm1.to_dict()
    cm2 = ConfigurationManager.from_dict(title, dict1)  # This fails
    dict2 = cm2.to_dict()
    
    assert dict1 == dict2
```

**Failing input**: `title='MyManager', params={'key': 'value'}, type_str='TestType'`

## Reproducing the Bug

```python
from troposphere.ssmquicksetup import ConfigurationDefinition, ConfigurationManager

cd = ConfigurationDefinition(
    Parameters={'key': 'value'},
    Type='TestType'
)

cm1 = ConfigurationManager(
    'MyManager',
    ConfigurationDefinitions=[cd]
)

dict1 = cm1.to_dict()
print("to_dict() output:", dict1)

cm2 = ConfigurationManager.from_dict('MyManager', dict1)
```

## Why This Is A Bug

This violates the expected round-trip serialization property that is fundamental to any serialization/deserialization API. The `to_dict()` method outputs CloudFormation template format with properties nested under a 'Properties' key:

```python
{'Properties': {...}, 'Type': 'AWS::SSMQuickSetup::ConfigurationManager'}
```

However, `from_dict()` expects properties at the top level of the dictionary. This incompatibility makes it impossible to serialize and deserialize ConfigurationManager objects, affecting not just ssmquicksetup but all AWSObject subclasses in troposphere.

## Fix

The `from_dict` method should handle the CloudFormation format output by `to_dict`. Here's a potential fix:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -406,6 +406,11 @@ class BaseAWSObject(BaseAWSObjectBase):
     @classmethod
     def from_dict(cls, title: str, d: dict[str, Any]) -> "BaseAWSObject":
+        # Handle CloudFormation format with 'Properties' wrapper
+        if 'Properties' in d and 'Type' in d:
+            # Extract properties from CloudFormation format
+            properties = d.get('Properties', {})
+            return cls._from_dict(title, **properties)
         return cls._from_dict(title, **d)
 
     def to_dict(self) -> dict[str, Any]:
```