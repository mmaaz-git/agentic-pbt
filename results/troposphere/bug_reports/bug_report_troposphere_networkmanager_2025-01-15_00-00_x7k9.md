# Bug Report: troposphere.networkmanager None Handling for Optional Properties

**Target**: `troposphere.networkmanager` (and likely all troposphere modules)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-01-15

## Summary

Optional properties in troposphere classes reject None values with a TypeError, even though they are marked as optional. This prevents programmatic setting of optional properties to None.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.networkmanager as nm

@given(
    include_address=st.booleans(),
    include_latitude=st.booleans(), 
    include_longitude=st.booleans()
)
def test_location_none_handling(include_address, include_latitude, include_longitude):
    """Test that Location should handle None values for optional properties"""
    kwargs = {}
    
    if include_address:
        kwargs["Address"] = None
    if include_latitude:
        kwargs["Latitude"] = None
    if include_longitude:
        kwargs["Longitude"] = None
    
    if not kwargs:
        kwargs["Address"] = None
    
    # This should work for optional properties but raises TypeError
    location = nm.Location(**kwargs)
    return location.to_dict()
```

**Failing input**: Any test case where None is passed to an optional property

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.networkmanager as nm

# This works - not providing optional property
location1 = nm.Location()
print(location1.to_dict())  # Output: {}

# This works - providing empty string
location2 = nm.Location(Address="")
print(location2.to_dict())  # Output: {'Address': ''}

# This fails with TypeError - providing None
location3 = nm.Location(Address=None)
# TypeError: <class 'troposphere.networkmanager.Location'>: None.Address is <class 'NoneType'>, expected <class 'str'>
```

## Why This Is A Bug

The bug violates the expected behavior of optional properties in Python. When a property is marked as optional (False in the props definition), users should be able to:
1. Not provide the property at all
2. Provide None to indicate absence of value

Currently, only option 1 works. This is inconsistent with Python conventions where None is commonly used to represent optional/missing values, especially in programmatic contexts where values are determined at runtime.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -249,6 +249,12 @@ class BaseAWSObject:
         elif name in self.propnames:
             # Check the type of the object and compare against what we were
             # expecting.
             expected_type = self.props[name][0]
+            is_required = self.props[name][1]
+            
+            # Allow None for optional properties
+            if value is None and not is_required:
+                # Don't add None values to properties dict
+                return None
 
             # If the value is a AWSHelperFn we can't do much validation
             # we'll have to leave that to Amazon. Maybe there's another way
```