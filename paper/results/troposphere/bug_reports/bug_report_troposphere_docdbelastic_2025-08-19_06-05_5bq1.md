# Bug Report: troposphere.docdbelastic Integer Validator Accepts Non-Integer Floats

**Target**: `troposphere.docdbelastic.integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer()` validation function incorrectly accepts non-integer float values like 0.5, 1.5, etc., when it should only accept values that represent whole numbers.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.docdbelastic as target

@given(st.floats(min_value=0.0, max_value=1.0, exclude_min=True, exclude_max=True))
def test_integer_with_small_floats(value):
    """Test integer function with floats between 0 and 1"""
    try:
        result = target.integer(value)
        assert False, f"integer() should reject {value}"
    except ValueError:
        pass
```

**Failing input**: `0.5`

## Reproducing the Bug

```python
import troposphere.docdbelastic as target

result = target.integer(0.5)
print(f"integer(0.5) returned: {result}")
print(f"This is incorrect - 0.5 is not an integer!")

cluster = target.Cluster(
    'TestCluster',
    AdminUserName='admin',
    AuthType='PLAIN_TEXT',
    ClusterName='test-cluster',
    ShardCapacity=2.5,
    ShardCount=1.5
)
print(f"\nCluster created with non-integer values:")
print(f"ShardCapacity: {cluster.to_dict()['Properties']['ShardCapacity']}")
print(f"ShardCount: {cluster.to_dict()['Properties']['ShardCount']}")
```

## Why This Is A Bug

The `integer()` function is meant to validate that values are integers before they're used in AWS CloudFormation templates. AWS DocDB Elastic clusters require integer values for properties like ShardCapacity and ShardCount. By accepting float values like 2.5, the validator allows creation of invalid CloudFormation templates that will fail during deployment. The function currently only checks if `int(x)` succeeds (which truncates floats), rather than checking if the value is actually an integer.

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    try:
        int(x)
+       # For floats, check they represent whole numbers
+       if isinstance(x, float) and not x.is_integer():
+           raise ValueError("%r is not a valid integer" % x)
    except (ValueError, TypeError):
        raise ValueError("%r is not a valid integer" % x)
    else:
        return x
```