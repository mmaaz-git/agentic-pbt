# Bug Report: troposphere BaseAWSObject._from_dict Poor Error Message for Empty Property Names

**Target**: `troposphere.BaseAWSObject._from_dict`
**Severity**: Low  
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

When `from_dict` is called with an empty string as a property name, the error message contains incorrect formatting with a double space, making it unclear and unprofessional.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.cloud9 as cloud9

@given(
    data=st.dictionaries(
        st.text(),
        st.text()
    )
)
def test_from_dict_with_invalid_property_names(data):
    """Test from_dict with various property names including empty string"""
    data["ImageId"] = "ami-12345678"
    data["InstanceType"] = "t2.micro"
    
    if "" in data:
        try:
            env = cloud9.EnvironmentEC2.from_dict("TestEnv", data)
            assert False, "Should reject empty property name"
        except AttributeError as e:
            # Check error message formatting
            error_msg = str(e)
            assert "does not have a  property" not in error_msg, \
                   "Error message has double space"
```

**Failing input**: `data={'': 'value', 'ImageId': 'ami-12345678', 'InstanceType': 't2.micro'}`

## Reproducing the Bug

```python
import troposphere.cloud9 as cloud9

data = {
    "": "some_value",
    "ImageId": "ami-12345678",
    "InstanceType": "t2.micro"
}

env = cloud9.EnvironmentEC2.from_dict("TestEnv", data)
```

## Why This Is A Bug

The error message incorrectly formats the property name, resulting in "Object type EnvironmentEC2 does not have a  property." with a double space. This makes the error message unclear and unprofessional. The error should properly handle empty strings and format the message correctly.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -367,9 +367,10 @@ class BaseAWSObject:
             try:
                 prop_attrs = cls.props[prop_name]
             except KeyError:
+                prop_display = f"'{prop_name}'" if prop_name else "an empty string"
                 raise AttributeError(
-                    "Object type %s does not have a "
-                    "%s property." % (cls.__name__, prop_name)
+                    "Object type %s does not have %s as a property." 
+                    % (cls.__name__, prop_display)
                 )
             prop_type = prop_attrs[0]
             value = kwargs[prop_name]
```