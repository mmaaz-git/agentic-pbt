# Bug Report: troposphere.neptune Hash Inconsistency for Equal Objects

**Target**: `troposphere.neptune` (applies to all troposphere AWS objects)
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

Equal objects in troposphere can have different hash values when properties are set in different orders, violating Python's requirement that equal objects must have equal hashes.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import neptune

@given(
    title=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", min_size=1),
    props=st.dictionaries(
        st.sampled_from(["DBClusterIdentifier", "BackupRetentionPeriod", "DBPort", "KmsKeyId", "EngineVersion"]),
        st.text(min_size=1),
        min_size=2,
        max_size=5
    )
)
def test_equality_property_order(title, props):
    cluster1 = neptune.DBCluster(title)
    cluster2 = neptune.DBCluster(title)
    
    for key, value in props.items():
        if key == "BackupRetentionPeriod" or key == "DBPort":
            value = 10
        setattr(cluster1, key, value)
    
    for key in reversed(list(props.keys())):
        value = props[key]
        if key == "BackupRetentionPeriod" or key == "DBPort":
            value = 10
        setattr(cluster2, key, value)
    
    assert cluster1 == cluster2
    assert hash(cluster1) == hash(cluster2)  # This fails!
```

**Failing input**: `title='0', props={'DBClusterIdentifier': '0', 'BackupRetentionPeriod': '0'}`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import neptune

cluster1 = neptune.DBCluster('TestCluster')
cluster2 = neptune.DBCluster('TestCluster')

cluster1.DBClusterIdentifier = 'my-cluster'
cluster1.BackupRetentionPeriod = 10

cluster2.BackupRetentionPeriod = 10
cluster2.DBClusterIdentifier = 'my-cluster'

print(f'Equal: {cluster1 == cluster2}')  # True
print(f'Same hash: {hash(cluster1) == hash(cluster2)}')  # False!
```

## Why This Is A Bug

Python requires that if `a == b` is True, then `hash(a) == hash(b)` must also be True. This is a fundamental contract for hashable objects in Python. Violating this can cause issues when objects are used in sets or as dictionary keys, where equal objects with different hashes would be treated as distinct.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -431,7 +431,7 @@ class BaseAWSObject:
         return not self == other
 
     def __hash__(self) -> int:
-        return hash(json.dumps({"title": self.title, **self.to_dict()}, indent=0))
+        return hash(json.dumps({"title": self.title, **self.to_dict()}, indent=0, sort_keys=True))
 
 
 class AWSObject(BaseAWSObject):
```