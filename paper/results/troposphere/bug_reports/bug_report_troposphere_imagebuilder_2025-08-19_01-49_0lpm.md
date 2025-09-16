# Bug Report: troposphere.imagebuilder validation=False Parameter Doesn't Disable Validation

**Target**: `troposphere.imagebuilder.Component`  
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `validation=False` parameter in troposphere resource constructors doesn't actually disable validation during object creation, only during serialization, violating the expected behavior that validation should be optional.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.imagebuilder as ib

@given(
    platform=st.text().filter(lambda x: x not in ["Linux", "Windows"])
)
def test_component_validation_disabled(platform):
    """Test that validation=False disables platform validation"""
    # Should accept any platform value when validation is disabled
    component = ib.Component(
        "TestComponent",
        Name="Test",
        Platform=platform,
        Version="1.0",
        validation=False
    )
    assert component.Platform == platform
```

**Failing input**: Any string that is not "Linux" or "Windows" (e.g., `"Ubuntu"`)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.imagebuilder as ib

component = ib.Component(
    "TestComponent",
    Name="Test",
    Platform="Ubuntu",
    Version="1.0",
    validation=False
)
```

## Why This Is A Bug

The `validation` parameter is passed to the BaseAWSObject constructor and stored as `self.do_validation`, which is checked in `to_dict()` method. However, validation functions are still called during property assignment in `__setattr__` regardless of the `validation` flag. This means users cannot create objects with values that would fail validation even when explicitly requesting validation to be disabled. This violates the principle of least surprise and the documented behavior of the validation parameter.

## Fix

The fix requires modifying the `__setattr__` method in BaseAWSObject to check `self.do_validation` before calling validator functions:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -261,7 +261,7 @@ class BaseAWSObject:
                 return self.properties.__setitem__(name, value)
 
             # If it's a function, call it...
-            elif isinstance(expected_type, types.FunctionType):
+            elif isinstance(expected_type, types.FunctionType) and self.do_validation:
                 try:
                     value = expected_type(value)
                 except Exception:
```