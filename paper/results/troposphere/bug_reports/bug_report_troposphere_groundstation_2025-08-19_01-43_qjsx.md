# Bug Report: troposphere.groundstation Properties Not Included in to_dict()

**Target**: `troposphere.groundstation` (affects all AWSProperty classes)
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

When properties are directly assigned to an AWSProperty object after initialization, the `to_dict()` method returns an empty dictionary instead of the assigned properties due to a broken reference between `self.properties` and `self.resource`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.groundstation import IntegerRange

@given(
    min_val=st.integers(),
    max_val=st.integers()
)
def test_integer_range_properties_in_to_dict(min_val, max_val):
    """Test that properties set after initialization appear in to_dict()"""
    int_range = IntegerRange()
    int_range.properties = {
        "Minimum": min_val,
        "Maximum": max_val
    }
    result = int_range.to_dict()
    assert result.get("Minimum") == min_val
    assert result.get("Maximum") == max_val
```

**Failing input**: `min_val=0, max_val=0` (any values fail)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.groundstation import IntegerRange

# Create object and set properties directly
int_range = IntegerRange()
int_range.properties = {"Minimum": 10, "Maximum": 20}

# to_dict() returns empty dict instead of properties
result = int_range.to_dict()
print(f"Expected: {{'Minimum': 10, 'Maximum': 20}}")
print(f"Actual: {result}")
assert result == {}, "Bug: to_dict() returns empty dict"

# Root cause: properties and resource are no longer the same object
print(f"properties is resource: {int_range.properties is int_range.resource}")
```

## Why This Is A Bug

This violates the principle of least surprise. When an object allows setting properties via the `.properties` attribute, users reasonably expect `to_dict()` to include those properties. The bug occurs because the initialization creates `self.resource` as a reference to `self.properties`, but directly reassigning `self.properties` breaks this reference. The `to_dict()` method uses `self.resource`, not `self.properties`, leading to unexpected empty results.

## Fix

The issue is in the BaseAWSObject class. When `self.properties` is reassigned, it breaks the reference to `self.resource`. Here's a fix that makes the properties attribute a property that maintains the resource reference:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -184,7 +184,7 @@ class BaseAWSObject:
             self.validate_title()
 
         # Create the list of properties set on this object by the user
-        self.properties = {}
+        self._properties = {}
         dictname = getattr(self, "dictname", None)
         if dictname:
             self.resource = {
@@ -194,6 +194,20 @@ class BaseAWSObject:
             self.resource = self.properties
         if hasattr(self, "resource_type") and self.resource_type is not None:
             self.resource["Type"] = self.resource_type
+            
+    @property
+    def properties(self):
+        return self._properties
+        
+    @properties.setter
+    def properties(self, value):
+        self._properties = value
+        # Update resource to maintain the reference
+        dictname = getattr(self, "dictname", None)
+        if dictname:
+            self.resource[dictname] = self._properties
+        else:
+            self.resource = self._properties
```

Alternatively, document that properties should not be directly reassigned and provide an update method instead.