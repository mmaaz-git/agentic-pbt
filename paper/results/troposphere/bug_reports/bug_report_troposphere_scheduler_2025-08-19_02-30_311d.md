# Bug Report: troposphere.scheduler Deferred Validation of Required Fields

**Target**: `troposphere.scheduler` (all AWSProperty classes)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Required field validation in troposphere.scheduler AWSProperty classes is deferred until serialization (`to_dict()`), allowing invalid objects to be created and passed around before failing.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.scheduler import (
    FlexibleTimeWindow,
    EventBridgeParameters,
    KinesisParameters,
    SageMakerPipelineParameter,
    CapacityProviderStrategyItem,
    AwsVpcConfiguration,
    Target,
    EcsParameters
)

@given(st.sampled_from([
    FlexibleTimeWindow,
    EventBridgeParameters,
    KinesisParameters,
    SageMakerPipelineParameter,
    CapacityProviderStrategyItem,
    AwsVpcConfiguration,
    Target,
    EcsParameters
]))
def test_all_classes_have_deferred_validation(cls):
    """All classes allow instantiation without required fields"""
    instance = cls()  # Should fail here but doesn't
    
    with pytest.raises(ValueError, match="Resource .* required"):
        instance.to_dict()  # Only fails here
```

**Failing input**: Any of the listed classes instantiated without required fields

## Reproducing the Bug

```python
from troposphere.scheduler import FlexibleTimeWindow, EventBridgeParameters

ftw = FlexibleTimeWindow()
ebp = EventBridgeParameters(DetailType="test")

print(f"FlexibleTimeWindow created: {ftw}")
print(f"EventBridgeParameters created: {ebp}")

try:
    ftw.to_dict()
except ValueError as e:
    print(f"FlexibleTimeWindow validation error: {e}")

try:
    ebp.to_dict()
except ValueError as e:
    print(f"EventBridgeParameters validation error: {e}")
```

## Why This Is A Bug

This violates the fail-fast principle and API contract expectations:

1. **Delayed error detection**: Objects appear valid at creation but fail later during serialization
2. **Error distance**: The error occurs far from where the mistake was made, making debugging difficult
3. **Invalid state propagation**: Invalid objects can be passed through multiple functions before failing
4. **API contract violation**: Required fields should be enforced at object creation, not serialization

## Fix

Move required field validation from `_validate_props()` to `__init__()`:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -123,6 +123,9 @@ class BaseAWSObject:
         for k, v in kwargs.items():
             self.__setattr__(k, v)
 
+        # Validate required properties immediately
+        if self.do_validation:
+            self._validate_props()
         self.add_to_template()
 
     def _validate_props(self) -> None:
@@ -321,8 +324,7 @@ class BaseAWSObject:
         return self.properties
 
     def to_dict(self, validation: bool = True) -> Dict[str, Any]:
         if validation and self.do_validation:
-            self._validate_props()
             self.validate()
 
         if self.properties:
```