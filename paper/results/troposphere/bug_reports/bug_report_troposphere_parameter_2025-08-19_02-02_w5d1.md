# Bug Report: troposphere.Parameter Accepts Invalid Empty String for Number Type

**Target**: `troposphere.Parameter`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Parameters with Type="Number" incorrectly accept empty strings as default values, which are not valid numbers and will cause CloudFormation template validation to fail.

## Property-Based Test

```python
@given(
    param_type=st.sampled_from(["String", "Number", "List<Number>", "CommaDelimitedList"]),
    default_value=st.one_of(
        st.text(max_size=20),
        st.integers(min_value=0, max_value=1000),
        st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False)
    )
)
def test_parameter_type_validation(param_type, default_value):
    try:
        param = Parameter("TestParam", Type=param_type, Default=default_value)
        param.validate()
        
        if param_type == "Number":
            assert isinstance(default_value, (int, float)) or (
                isinstance(default_value, str) and (
                    default_value.replace(".", "").replace("-", "").isdigit()
                )
            )
    except ValueError as e:
        if param_type == "Number" and isinstance(default_value, str):
            try:
                float(default_value)
                int(default_value)
                assert False, "Should have failed but didn't"
            except:
                pass
```

**Failing input**: `param_type='Number', default_value=''`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import Parameter

param = Parameter("TestParam", Type="Number", Default="")
param.validate()

print(f"Parameter created: {param.properties}")
print(f"Default value: '{param.properties['Default']}'")

try:
    float("")
except ValueError as e:
    print(f"Python float('') raises: {e}")
```

## Why This Is A Bug

An empty string is not a valid number. Python's `float("")` and `int("")` both raise ValueError. CloudFormation will reject templates with Number parameters that have empty string defaults. The validation in troposphere should catch this at template creation time rather than allowing invalid templates to be generated.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -1078,6 +1078,8 @@ class Parameter(AWSDeclaration):
                 raise ValueError(error_str % ("String", type(default), default))
             elif param_type == "Number":
                 allowed = [float, int]
+                if isinstance(default, str) and default.strip() == "":
+                    raise ValueError(error_str % (param_type, type(default), default))
                 # See if the default value can be coerced into one
                 # of the correct types
                 if not any(check_type(x, default) for x in allowed):
```