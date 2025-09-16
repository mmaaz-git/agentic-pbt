# Bug Report: Troposphere Parameter Accepts Invalid Empty String for Number Type

**Target**: `troposphere.Parameter`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-01-18

## Summary

The Parameter class incorrectly accepts an empty string as a default value for Number type parameters, violating CloudFormation's type contract.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import Parameter

@given(
    param_type=st.sampled_from(["Number"]),
    default_value=st.text(max_size=50)
)
def test_number_parameter_validation(param_type, default_value):
    if not default_value or not default_value.strip():
        # Empty or whitespace-only strings should be rejected
        try:
            param = Parameter("Test", Type=param_type, Default=default_value)
            param.validate()
            assert False, "Empty string accepted for Number type"
        except (ValueError, TypeError):
            pass  # Expected
```

**Failing input**: `param_type='Number', default_value=''`

## Reproducing the Bug

```python
from troposphere import Parameter

param = Parameter("NumberParam", Type="Number", Default="")
param.validate()
print(f"Default value: '{param.properties.get('Default')}'")
print("No error raised - empty string accepted as Number default!")
```

## Why This Is A Bug

CloudFormation Number parameters must have numeric default values. An empty string is not a valid number and will cause template validation errors when deployed to AWS. The validation logic attempts to convert the default to float/int but doesn't handle the empty string case properly, allowing it through without raising an error.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -1086,6 +1086,9 @@ class Parameter(AWSDeclaration):
                 if not isinstance(default, str):
                     raise ValueError(error_str % (param_type, type(default), default))
                 allowed = [float, int]
+                # Empty string is not a valid number
+                if not default.strip():
+                    raise ValueError(error_str % (param_type, type(default), default))
                 dlist = default.split(",")
                 for d in dlist:
                     # Verify the split array are all numbers
```