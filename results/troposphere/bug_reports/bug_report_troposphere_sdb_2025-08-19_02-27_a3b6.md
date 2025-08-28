# Bug Report: troposphere.sdb Round-Trip Serialization Failure

**Target**: `troposphere.sdb.Domain`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `from_dict` method cannot deserialize the output of `to_dict`, violating the expected round-trip property for serialization methods.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.sdb

@given(
    title=st.text(min_size=1).filter(lambda x: x.isalnum()),
    description=st.text()
)
def test_domain_round_trip_full_dict(title, description):
    """Test that Domain objects can round-trip through to_dict/from_dict"""
    original = troposphere.sdb.Domain(title, Description=description)
    dict_repr = original.to_dict()
    
    # This should work but doesn't - from_dict should handle the full to_dict output
    restored = troposphere.sdb.Domain.from_dict(title, dict_repr)
    restored_dict = restored.to_dict()
    
    assert dict_repr == restored_dict
```

**Failing input**: `title='ValidDomain', description='Test'`

## Reproducing the Bug

```python
import troposphere.sdb

domain = troposphere.sdb.Domain('ValidDomain', Description='Test')
dict_repr = domain.to_dict()
print('to_dict output:', dict_repr)

restored = troposphere.sdb.Domain.from_dict('ValidDomain', dict_repr)
```

## Why This Is A Bug

The `to_dict()` method produces `{'Properties': {'Description': 'Test'}, 'Type': 'AWS::SDB::Domain'}`, but `from_dict()` expects just the properties dictionary `{'Description': 'Test'}`. This breaks the expected contract that serialization/deserialization methods should be inverses, making round-trip persistence impossible without manual intervention.

## Fix

The `from_dict` method should handle both formats - the full CloudFormation structure and just the properties:

```diff
@classmethod
def from_dict(cls, title, d):
+   # Handle both full CloudFormation dict and just properties
+   if 'Properties' in d and 'Type' in d:
+       # Full CloudFormation structure from to_dict()
+       return cls._from_dict(title, **d['Properties'])
    return cls._from_dict(title, **d)
```