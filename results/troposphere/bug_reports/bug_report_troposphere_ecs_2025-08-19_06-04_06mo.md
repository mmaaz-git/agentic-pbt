# Bug Report: troposphere.ecs ProxyConfiguration Constructor/Validation Inconsistency

**Target**: `troposphere.ecs.ProxyConfiguration`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

ProxyConfiguration allows object construction without required fields, but fails when calling to_dict(), violating the expected contract that constructible objects should be serializable.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.ecs as ecs

@given(st.sampled_from(["APPMESH"]))
def test_proxy_configuration_round_trip(proxy_type):
    """Test ProxyConfiguration to_dict preserves data"""
    proxy = ecs.ProxyConfiguration(Type=proxy_type)
    dict_repr = proxy.to_dict()
    
    assert dict_repr["Type"] == proxy_type
    
    # Round-trip
    proxy2 = ecs.ProxyConfiguration(**dict_repr)
    dict_repr2 = proxy2.to_dict()
    
    assert dict_repr == dict_repr2
```

**Failing input**: `proxy_type='APPMESH'`

## Reproducing the Bug

```python
import troposphere.ecs as ecs

proxy = ecs.ProxyConfiguration(Type='APPMESH')
print(f'Object created: {proxy}')

result = proxy.to_dict()
```

## Why This Is A Bug

The ProxyConfiguration class allows construction with only the `Type` parameter, but marks `ContainerName` as required in its props definition. This creates an inconsistency where:

1. The constructor succeeds without ContainerName
2. The to_dict() method fails with "Resource ContainerName required"

This violates the principle of least surprise - objects that can be constructed should be able to serialize. The class should either:
- Fail at construction time if ContainerName is truly required, or
- Allow to_dict() to succeed without ContainerName if it's actually optional

This same pattern affects multiple other classes in troposphere.ecs including AutoScalingGroupProvider, CapacityProviderStrategy, ContainerDefinition, DeploymentAlarms, DeploymentCircuitBreaker, and others.

## Fix

The fix requires making a design decision about whether these fields are truly required. One approach is to validate required fields at construction time:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -339,6 +339,7 @@ class AWSProperty(BaseAWSObject):
     def __init__(self, **kwargs):
         super().__init__(**kwargs)
+        self._validate_props()  # Validate at construction time
 
     def to_dict(self):
         self._validate_props()
```

Alternatively, make ContainerName optional in the props definition if it's not truly required:

```diff
--- a/troposphere/ecs.py
+++ b/troposphere/ecs.py
@@ -XXX,7 +XXX,7 @@ class ProxyConfiguration(AWSProperty):
     props: PropsDictType = {
-        "ContainerName": (str, True),
+        "ContainerName": (str, False),
         "ProxyConfigurationProperties": (list, False),
         "Type": (ecs_proxy_type, False),
     }
```