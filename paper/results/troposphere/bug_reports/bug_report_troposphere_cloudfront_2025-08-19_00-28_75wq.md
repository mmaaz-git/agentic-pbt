# Bug Report: troposphere.cloudfront Delayed Required Properties Validation

**Target**: `troposphere.cloudfront`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Required properties in CloudFront resource classes are not validated at object instantiation, only when converting to dict/JSON, violating the fail-fast principle and causing delayed runtime errors.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import cloudfront

def test_required_properties_not_validated_at_instantiation():
    # DefaultCacheBehavior requires TargetOriginId and ViewerProtocolPolicy
    behavior = cloudfront.DefaultCacheBehavior()
    
    # BUG: Object created successfully without required properties
    assert behavior.properties == {}
    
    # Error only occurs when serializing
    with pytest.raises(ValueError, match="Resource TargetOriginId required"):
        behavior.to_dict()
```

**Failing input**: No specific input - structural bug in validation timing

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import cloudfront

# Create DefaultCacheBehavior without required properties
behavior = cloudfront.DefaultCacheBehavior()
print("Object created successfully:", behavior)
print("Properties:", behavior.properties)

# Error only happens when converting to dict
try:
    behavior.to_dict()
except ValueError as e:
    print(f"Error during serialization: {e}")

# This affects many CloudFront classes
dist = cloudfront.Distribution("TestDist")
print("Distribution created without required DistributionConfig")

try:
    dist.to_dict()
except ValueError as e:
    print(f"Error during serialization: {e}")
```

## Why This Is A Bug

This violates the principle of failing fast. Developers expect that if an object has required properties, it should fail at construction time if those properties are missing. The current behavior allows invalid objects to be created and passed around, only failing much later when serialization is attempted. This makes debugging harder and can lead to runtime failures in production code.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -206,6 +206,15 @@ class BaseAWSObject:
         for k, v in kwargs.items():
             self.__setattr__(k, v)
 
+        # Validate required properties are present
+        if self.do_validation:
+            for prop_name, (prop_type, is_required) in self.props.items():
+                if is_required and prop_name not in self.properties:
+                    raise ValueError(
+                        "Resource %s required in %s"
+                        % (prop_name, self.__class__)
+                    )
+
         self.add_to_template()
 
     def add_to_template(self) -> None:
```