# Bug Report: troposphere.appintegrations None Handling for Optional Fields

**Target**: `troposphere.appintegrations` (and all troposphere modules)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The troposphere library incorrectly rejects `None` values for optional fields (marked with `False` in props), causing TypeError when users explicitly pass None for optional parameters.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.appintegrations import ScheduleConfig

@given(
    schedule_expr=st.text(min_size=1, max_size=100),
    first_exec=st.one_of(st.none(), st.text(min_size=1))
)
def test_schedule_config_optional_fields(schedule_expr, first_exec):
    """Test that ScheduleConfig accepts None for optional fields"""
    sc = ScheduleConfig(
        ScheduleExpression=schedule_expr,
        FirstExecutionFrom=first_exec  # Should accept None
    )
    sc.to_dict()  # Should not raise
```

**Failing input**: `schedule_expr='0', first_exec=None`

## Reproducing the Bug

```python
from troposphere.appintegrations import ScheduleConfig

sc = ScheduleConfig(
    ScheduleExpression="rate(1 hour)",
    FirstExecutionFrom=None
)
```

## Why This Is A Bug

The library's props definition marks `FirstExecutionFrom` as optional with `(str, False)`, where `False` indicates the field is not required. However, the type validation in `BaseAWSObject.__setattr__` doesn't check if a field is optional before rejecting `None` values. This creates an inconsistency where:

- Not providing the field at all: ✓ Works
- Providing `None` explicitly: ✗ Raises TypeError

This breaks common Python patterns like `dict.get("key")` (returns None if missing) and mapping API responses where optional fields may be explicitly set to None.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -249,6 +249,11 @@ class BaseAWSObject:
         elif name in self.propnames:
             # Check the type of the object and compare against what we were
             # expecting.
             expected_type = self.props[name][0]
+            required = self.props[name][1]
+            
+            # Allow None for optional fields
+            if not required and value is None:
+                return self.properties.__setitem__(name, value)
 
             # If the value is a AWSHelperFn we can't do much validation
             # we'll have to leave that to Amazon. Maybe there's another way
```