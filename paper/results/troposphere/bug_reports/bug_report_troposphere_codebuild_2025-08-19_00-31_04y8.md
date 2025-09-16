# Bug Report: troposphere.codebuild EnvironmentVariable validation missing required property checks

**Target**: `troposphere.codebuild.EnvironmentVariable`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `EnvironmentVariable.validate()` method fails to verify that required properties `Name` and `Value` are present, only checking the optional `Type` property if it exists.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.codebuild import EnvironmentVariable

@given(
    has_name=st.booleans(),
    has_value=st.booleans(),
    has_type=st.booleans()
)
def test_environment_variable_required_properties(has_name, has_value, has_type):
    """Property: EnvironmentVariable should enforce required Name and Value."""
    props = {}
    if has_name:
        props["Name"] = "TEST"
    if has_value:
        props["Value"] = "value"
    if has_type:
        props["Type"] = "PLAINTEXT"
    
    env_var = EnvironmentVariable(**props)
    env_var.validate()
    
    # According to the class definition, Name and Value are required
    # But validation passes even without them
    assert has_name and has_value, "Should require Name and Value"
```

**Failing input**: `has_name=False, has_value=False, has_type=False`

## Reproducing the Bug

```python
from troposphere.codebuild import EnvironmentVariable

# Create EnvironmentVariable without required properties
env_var = EnvironmentVariable()
print(f"Properties: {env_var.properties}")  # Output: {}

# This should fail but doesn't
env_var.validate()
print("Validation passed without required Name and Value!")

# Also passes with only one required property
env_var2 = EnvironmentVariable(Name="TEST")
env_var2.validate()  # Should fail without Value

env_var3 = EnvironmentVariable(Value="value")
env_var3.validate()  # Should fail without Name
```

## Why This Is A Bug

The `EnvironmentVariable` class definition specifies that `Name` and `Value` are required properties (marked with `True` in the props definition), but the `validate()` method only checks the optional `Type` property. This violates the API contract and could lead to invalid CloudFormation templates being generated.

## Fix

```diff
--- a/troposphere/validators/codebuild.py
+++ b/troposphere/validators/codebuild.py
@@ -134,6 +134,15 @@ def validate_environment_variable(self):
     """
     Class: EnvironmentVariable
     """
+    # Check required properties
+    if "Name" not in self.properties:
+        raise ValueError(
+            "EnvironmentVariable Name: required property is missing"
+        )
+    if "Value" not in self.properties:
+        raise ValueError(
+            "EnvironmentVariable Value: required property is missing"
+        )
+    
     if "Type" in self.properties:
         valid_types = ["PARAMETER_STORE", "PLAINTEXT", "SECRETS_MANAGER"]
         env_type = self.properties.get("Type")
```