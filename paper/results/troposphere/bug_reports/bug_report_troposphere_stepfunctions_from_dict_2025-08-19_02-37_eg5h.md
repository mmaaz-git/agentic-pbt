# Bug Report: troposphere from_dict/to_dict Round-Trip Failure

**Target**: `troposphere.stepfunctions.Activity.from_dict` and related classes
**Severity**: Medium  
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `from_dict()` method cannot reconstruct objects from the output of `to_dict()`, breaking the expected round-trip property between these complementary methods.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.stepfunctions as sf

@given(st.text(min_size=1, max_size=50).filter(lambda x: x.isidentifier()))
def test_activity_from_dict_round_trip(name):
    """Test that from_dict can recreate objects from to_dict output."""
    original = sf.Activity('TestActivity', Name=name)
    dict_repr = original.to_dict()
    
    # This should work but fails
    recreated = sf.Activity.from_dict('TestActivity', dict_repr)
    assert recreated.to_dict() == dict_repr
```

**Failing input**: Any valid name value

## Reproducing the Bug

```python
import troposphere.stepfunctions as sf

activity = sf.Activity('TestActivity', Name='MyActivity')
dict_repr = activity.to_dict()
print(f"to_dict() output: {dict_repr}")

try:
    recreated = sf.Activity.from_dict('TestActivity', dict_repr)
    print("Successfully recreated")
except AttributeError as e:
    print(f"Failed to recreate: {e}")

recreated_workaround = sf.Activity.from_dict('TestActivity', dict_repr['Properties'])
print(f"Workaround succeeds: {recreated_workaround.to_dict() == dict_repr}")
```

## Why This Is A Bug  

The `to_dict()` method produces CloudFormation resource format: `{'Properties': {...}, 'Type': '...'}`, but `from_dict()` expects only the properties dictionary. This violates the principle that serialization/deserialization methods should be inverses of each other. Users would reasonably expect `from_dict(title, obj.to_dict())` to recreate the object.

## Fix

The `from_dict` method should handle both formats - accept either the full CloudFormation dict or just the properties:

```diff
@classmethod
def from_dict(cls, title, d):
+    # Handle both full CloudFormation dict and just properties
+    if 'Type' in d and 'Properties' in d:
+        # Full CloudFormation format from to_dict()
+        d = d['Properties']
    return cls._from_dict(title, **d)
```