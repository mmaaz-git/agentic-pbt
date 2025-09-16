# Bug Report: troposphere.redshift validate() Method Doesn't Check Required Fields

**Target**: `troposphere.redshift` (and likely all troposphere modules)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `validate()` method in troposphere AWS resource classes doesn't check for required fields, while `to_dict()` does, leading to inconsistent validation behavior.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.redshift as redshift

@given(
    skip_field=st.sampled_from(['ClusterType', 'DBName', 'MasterUsername', 'NodeType'])
)
def test_cluster_required_fields(skip_field):
    """Test that Cluster enforces required fields consistently"""
    fields = {
        'ClusterType': 'single-node',
        'DBName': 'testdb',
        'MasterUsername': 'admin',
        'NodeType': 'dc2.large'
    }
    
    del fields[skip_field]
    
    cluster = redshift.Cluster('TestCluster', **fields)
    
    # validate() should fail for missing required field but doesn't
    cluster.validate()  # Passes incorrectly
    
    try:
        cluster.to_dict()  # Fails correctly
        assert False, f"to_dict() should have failed for missing {skip_field}"
    except ValueError:
        pass  # Expected
```

**Failing input**: Any of the required fields ('ClusterType', 'DBName', 'MasterUsername', 'NodeType')

## Reproducing the Bug

```python
import troposphere.redshift as redshift

# Create a Cluster missing the required 'ClusterType' field
cluster = redshift.Cluster(
    'MyCluster',
    DBName='testdb',
    MasterUsername='admin',
    NodeType='dc2.large'
)

# validate() incorrectly passes
cluster.validate()
print("validate() passed (BUG: should have failed)")

# to_dict() correctly fails
try:
    cluster.to_dict()
    print("to_dict() passed")
except ValueError as e:
    print(f"to_dict() failed: {e}")
```

## Why This Is A Bug

The `validate()` method's purpose is to validate that an AWS resource object is correctly configured. Required fields are a fundamental part of AWS CloudFormation resource specifications. Users expect `validate()` to catch missing required fields before attempting to generate CloudFormation templates via `to_dict()`.

This inconsistency violates the principle of least surprise and the documented contract that `validate()` should validate the resource configuration. The bug affects multiple classes including Cluster, ClusterParameterGroup, ClusterSecurityGroup, ClusterSubnetGroup, and EndpointAccess.

## Fix

The root cause is in the BaseAWSObject class where `validate()` is defined as a no-op while `_validate_props()` contains the actual validation logic:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ class BaseAWSObject:
     def validate(self) -> None:
-        pass
+        self._validate_props()
 
     def _validate_props(self) -> None:
         for k, (_, required) in self.props.items():
             if required and k not in self.properties:
                 rtype = getattr(self, "resource_type", type(self))
                 title = getattr(self, "title")
                 msg = "Resource %s required in type %s" % (k, rtype)
                 if title:
                     msg += " (title: %s)" % title
                 raise ValueError(msg)
```

Alternatively, if subclasses are meant to override `validate()`, it should at least call `_validate_props()` as a baseline validation.