# Bug Report: troposphere.route53 Optional Fields Reject None Values

**Target**: `troposphere.route53` (multiple classes)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Optional fields in troposphere.route53 classes raise TypeError when explicitly passed None, despite being marked as optional in the props definition. This affects programmatic config generation where optional parameters naturally default to None.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.route53 as r53

@given(
    resource_path=st.one_of(st.none(), st.text(min_size=0, max_size=255))
)
def test_optional_field_none_handling(resource_path):
    """Test that optional fields handle None gracefully"""
    # ResourcePath is optional (marked False in props)
    if resource_path is None:
        # Should either accept None or filter it out
        config = r53.HealthCheckConfig(
            IPAddress='1.2.3.4',
            Port=80,
            Type='HTTP',
            ResourcePath=resource_path
        )
        # If None is accepted, it shouldn't appear in the dict
        assert 'ResourcePath' not in config.to_dict()
```

**Failing input**: `resource_path=None`

## Reproducing the Bug

```python
import troposphere.route53 as r53

# This works - omitting optional field
config1 = r53.HealthCheckConfig(
    IPAddress='1.2.3.4',
    Port=80,
    Type='HTTP'
)
print("Without ResourcePath:", config1.to_dict())

# This fails - explicit None for optional field
config2 = r53.HealthCheckConfig(
    IPAddress='1.2.3.4',
    Port=80,
    Type='HTTP',
    ResourcePath=None  # TypeError!
)
```

## Why This Is A Bug

1. The field is marked as optional (`(<class 'str'>, False)` in props definition)
2. Omitting the field works fine, but passing None doesn't
3. This breaks common Python patterns where optional parameters default to None
4. Affects multiple classes: RecordSet.TTL, RecordSet.HealthCheckId, GeoLocation.CountryCode, HealthCheckConfig.ResourcePath

## Fix

The `__setattr__` method in the base class should filter out None values for optional fields instead of type-checking them:

```diff
# In troposphere/__init__.py, around line 305 in __setattr__
 def __setattr__(self, name, value):
     if name in self.props:
         expected_type, required = self.props[name]
+        # Skip None values for optional fields
+        if value is None and not required:
+            return
         if not self._validate_type(value, expected_type):
             self._raise_type(name, value, expected_type)
```