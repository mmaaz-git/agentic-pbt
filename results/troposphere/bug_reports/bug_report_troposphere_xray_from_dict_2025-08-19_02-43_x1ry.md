# Bug Report: troposphere.xray from_dict Cannot Parse to_dict Output

**Target**: `troposphere.xray.Group.from_dict`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `from_dict()` method cannot parse the output of `to_dict()`, breaking the expected round-trip property for AWS resource serialization.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.xray as xray

@given(
    group_name=st.text(min_size=1, max_size=100).filter(lambda x: '\x00' not in x)
)
def test_group_from_dict_roundtrip(group_name):
    """Group should support round-trip to_dict/from_dict conversion."""
    original = xray.Group('TestGroup', GroupName=group_name)
    dict_repr = original.to_dict()
    
    # Attempt to reconstruct from the dict representation
    reconstructed = xray.Group.from_dict('TestGroup2', dict_repr)
    assert reconstructed.GroupName == group_name
```

**Failing input**: Any valid group name (e.g., `'MyGroup'`)

## Reproducing the Bug

```python
import troposphere.xray as xray

group = xray.Group('TestGroup', GroupName='MyGroup')
dict_repr = group.to_dict()
print(f"to_dict output: {dict_repr}")

try:
    new_group = xray.Group.from_dict('NewGroup', dict_repr)
    print("from_dict succeeded")
except Exception as e:
    print(f"from_dict failed: {type(e).__name__}: {e}")
```

## Why This Is A Bug

The `to_dict()` method produces a CloudFormation-style dictionary with nested 'Properties' and 'Type' keys, but `from_dict()` expects the properties to be passed as direct keyword arguments. This violates the round-trip property that `from_dict(to_dict(obj))` should reconstruct the original object. This is a fundamental serialization contract violation that affects all AWS resources in the module.

## Fix

The `from_dict()` method needs to handle the CloudFormation dictionary format produced by `to_dict()`:

```diff
@classmethod
def from_dict(cls, title, d):
+   # Handle CloudFormation format with nested Properties
+   if isinstance(d, dict) and 'Properties' in d:
+       # Extract properties from nested structure
+       return cls._from_dict(title, **d['Properties'])
    return cls._from_dict(title, **d)
```