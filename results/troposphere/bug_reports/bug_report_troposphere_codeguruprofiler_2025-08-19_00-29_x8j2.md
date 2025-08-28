# Bug Report: troposphere.codeguruprofiler - None Values for Optional Fields Raise TypeError

**Target**: `troposphere.codeguruprofiler.ProfilingGroup`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Setting `None` to optional fields in troposphere classes raises a TypeError instead of omitting the field from the CloudFormation template output.

## Property-Based Test

```python
@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100),
    profiling_group_name=st.text(min_size=1, max_size=255)
)
def test_none_optional_field(title, profiling_group_name):
    pg = cgp.ProfilingGroup(
        title,
        ProfilingGroupName=profiling_group_name,
        ComputePlatform=None  # Optional field set to None
    )
    
    d = pg.to_dict()
    # None values should not appear in the dictionary
    assert "ComputePlatform" not in d["Properties"]
```

**Failing input**: `title='0', profiling_group_name='0'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.codeguruprofiler as cgp

pg = cgp.ProfilingGroup(
    "MyProfilingGroup",
    ProfilingGroupName="TestGroup",
    ComputePlatform=None
)

print(pg.to_dict())
```

## Why This Is A Bug

Optional fields (marked with `False` in the `props` definition) should accept `None` values to indicate the absence of a value. This is a common Python pattern where `None` means "no value provided". The library should either:
1. Skip adding the property to the output dictionary when the value is `None`
2. Handle `None` values gracefully without raising exceptions

Current behavior violates the principle of least surprise, as developers expect optional fields to accept `None`.

## Fix

The issue is in the `__setattr__` method of `BaseAWSObject` class. It needs to handle `None` values for optional fields:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -248,6 +248,11 @@ class BaseAWSObject:
             return None
         elif name in self.propnames:
+            # Handle None values for optional fields
+            if value is None:
+                if not self.props[name][1]:  # If field is optional (required=False)
+                    return None  # Don't set the property
+                # If required, fall through to normal validation
             # Check the type of the object and compare against what we were
             # expecting.
             expected_type = self.props[name][0]
```

Alternative fix at a higher level:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -204,6 +204,9 @@ class BaseAWSObject:
 
         # Now that it is initialized, populate it with the kwargs
         for k, v in kwargs.items():
+            # Skip None values for optional fields
+            if v is None and k in self.props and not self.props[k][1]:
+                continue
             self.__setattr__(k, v)
```