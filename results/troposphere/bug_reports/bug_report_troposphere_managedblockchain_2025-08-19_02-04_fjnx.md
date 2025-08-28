# Bug Report: troposphere.managedblockchain Round-Trip Serialization Failure

**Target**: `troposphere.managedblockchain` (affects all AWSObject subclasses)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

AWSObject subclasses in troposphere violate the round-trip property: `from_dict(to_dict())` fails with AttributeError. The `to_dict()` method wraps properties in a 'Properties' key, but `from_dict()` expects unwrapped properties.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import managedblockchain

@given(
    accessor_type=st.text(min_size=1, max_size=100),
    network_type=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_accessor_round_trip(accessor_type, network_type):
    kwargs = {'AccessorType': accessor_type}
    if network_type is not None:
        kwargs['NetworkType'] = network_type
    
    original = managedblockchain.Accessor('TestAccessor', **kwargs)
    dict_repr = original.to_dict()
    reconstructed = managedblockchain.Accessor.from_dict('TestAccessor', dict_repr)
    
    assert original == reconstructed
```

**Failing input**: `accessor_type='0', network_type=None`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import managedblockchain

accessor = managedblockchain.Accessor('TestAccessor', AccessorType='BILLING_TOKEN')
dict_repr = accessor.to_dict()
print("to_dict() returns:", dict_repr)

try:
    reconstructed = managedblockchain.Accessor.from_dict('TestAccessor', dict_repr)
except AttributeError as e:
    print(f"Error: {e}")
    print("\nBug: to_dict() wraps in 'Properties', but from_dict() expects unwrapped dict")
    
    reconstructed = managedblockchain.Accessor.from_dict('TestAccessor', dict_repr['Properties'])
    print("Workaround works: passing dict_repr['Properties']")
```

## Why This Is A Bug

The round-trip property is fundamental for serialization/deserialization. Users expect `from_dict(to_dict())` to reconstruct the original object. This bug breaks workflows that serialize CloudFormation resources to dictionaries and reconstruct them later. The issue affects all AWSObject subclasses across the entire troposphere library, not just managedblockchain.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -405,7 +405,11 @@ class BaseAWSObject:
     @classmethod
     def from_dict(
         cls: Type[__BaseAWSObjectTypeVar], title: str, d: Dict[str, Any]
     ) -> __BaseAWSObjectTypeVar:
-        return cls._from_dict(title, **d)
+        # Handle both wrapped and unwrapped dictionaries
+        if 'Properties' in d and hasattr(cls, 'dictname') and cls.dictname == 'Properties':
+            return cls._from_dict(title, **d['Properties'])
+        else:
+            return cls._from_dict(title, **d)
```