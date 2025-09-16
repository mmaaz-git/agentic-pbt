# Bug Report: troposphere Parameter Validation Bypassed for Falsy Values

**Target**: `troposphere.Parameter`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The Parameter class in troposphere incorrectly accepts falsy values (0, False) as Default values for String type parameters, and accepts empty string as a valid title, both violating documented validation rules.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import Parameter

@given(
    default_value=st.one_of(
        st.text(),
        st.integers(),
        st.floats(allow_nan=False),
        st.booleans()
    )
)
def test_parameter_string_default_validation(default_value):
    """Test that Parameter validates Default value matches String type"""
    if default_value is None:
        return  # None means no default
    
    try:
        param = Parameter("TestParam", Type="String", Default=default_value)
        param.validate()
        # If successful, default should be a string
        assert isinstance(default_value, str)
    except (ValueError, TypeError) as e:
        # Should fail if default is not a string
        assert not isinstance(default_value, str)
```

**Failing input**: `default_value=0` and `default_value=False`

## Reproducing the Bug

```python
from troposphere import Parameter

# Bug 1: Integer 0 accepted as Default for String type
param1 = Parameter("TestParam1", Type="String", Default=0)
param1.validate()  # Should raise ValueError but doesn't
print(f"Integer {param1.Default} accepted as String default")

# Bug 2: Boolean False accepted as Default for String type  
param2 = Parameter("TestParam2", Type="String", Default=False)
param2.validate()  # Should raise ValueError but doesn't
print(f"Boolean {param2.Default} accepted as String default")

# Bug 3: Empty string accepted as Parameter title
param3 = Parameter("", Type="String")
print(f"Empty title '{param3.title}' accepted")
```

## Why This Is A Bug

The Parameter class documentation and validation logic explicitly state that:
1. String type parameters must have string Default values
2. Parameter titles must match the pattern `^[a-zA-Z0-9]+$` (requiring at least one alphanumeric character)

These bugs violate the type contract and could lead to CloudFormation template generation errors or runtime failures.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,7 +180,7 @@ class BaseAWSObject:
         ]
 
         # try to validate the title if its there
-        if self.title:
+        if self.title is not None:
             self.validate_title()
 
         # Create the list of properties set on this object by the user
@@ -1065,7 +1065,7 @@ class Parameter(AWSDeclaration):
 
         # Validate the Default parameter value
         default = self.properties.get("Default")
-        if default:
+        if default is not None:
             error_str = (
                 "Parameter default type mismatch: expecting "
                 "type %s got %s with value %r"
```