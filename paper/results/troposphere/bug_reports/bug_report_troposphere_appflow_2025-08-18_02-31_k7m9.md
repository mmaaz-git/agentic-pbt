# Bug Report: troposphere.appflow Property Name Conflicts with Internal Attributes

**Target**: `troposphere.appflow` (and all troposphere modules)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The troposphere library allows users to define CloudFormation properties with any name in the `props` dictionary, but certain property names conflict with internal BaseAWSObject attributes, causing silent data corruption and validation failures.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import AWSProperty

@given(
    st.sampled_from(['template', 'title', 'properties', 'resource', 'do_validation']),
    st.text(min_size=1, max_size=20)
)
def test_property_name_conflicts(internal_attr, value):
    """Test that property names don't conflict with internal attributes"""
    
    class TestProperty(AWSProperty):
        props = {
            internal_attr: (str, True)
        }
    
    obj = TestProperty()
    setattr(obj, internal_attr, value)
    
    # Property should be stored in properties dict, not as internal attribute
    assert internal_attr in obj.properties
    
    # Validation should succeed
    result = obj.to_dict(validation=True)
    assert internal_attr in result
```

**Failing input**: `internal_attr='template', value='any_value'`

## Reproducing the Bug

```python
from troposphere import AWSProperty

class UserDefinedProperty(AWSProperty):
    props = {
        'template': (str, True),
        'normal_field': (str, True)
    }

obj = UserDefinedProperty()
obj.template = "my_template_value"
obj.normal_field = "my_normal_value"

print(f"'template' in obj.properties: {'template' in obj.properties}")
print(f"'normal_field' in obj.properties: {'normal_field' in obj.properties}")

try:
    obj.to_dict(validation=True)
except ValueError as e:
    print(f"Validation error: {e}")
```

## Why This Is A Bug

This violates the expected contract of the troposphere API:
1. Users can define properties with any valid Python identifier name
2. Setting a property should store it in the properties dictionary
3. Required properties should pass validation when set

Instead, properties with names matching internal attributes are silently stored in the wrong location, causing validation failures and data loss.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -236,10 +236,16 @@ class BaseAWSObject:
 
     def __setattr__(self, name: str, value: Any) -> None:
         if (
             name in self.__dict__.keys()
             or "_BaseAWSObject__initialized" not in self.__dict__
         ):
             return dict.__setattr__(self, name, value)  # type: ignore
+        elif name in self.propnames:
+            # Check properties BEFORE attributes to prevent conflicts
+            # Handle property setting logic here...
+            expected_type = self.props[name][0]
+            # ... validation logic ...
+            return self.properties.__setitem__(name, value)
         elif name in self.attributes:
             if name == "DependsOn":
                 self.resource[name] = depends_on_helper(value)
             else:
                 self.resource[name] = value
             return None
-        elif name in self.propnames:
-            # Check the type of the object and compare against what we were
-            # expecting.
```

The fix involves checking if a name is in `propnames` before checking if it's in `attributes`, preventing internal attribute names from shadowing user-defined properties.