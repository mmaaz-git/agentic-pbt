# Bug Report: troposphere.datapipeline Type Validation Bypass

**Target**: `troposphere.datapipeline`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The troposphere library's type validation system may allow incorrect types (e.g., integers) to be assigned to string-only properties, violating the type contract defined in the props dictionaries.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere import datapipeline

@given(
    st.one_of(
        st.integers(),
        st.floats(),
        st.booleans(),
        st.lists(st.text())
    )
)
def test_pipeline_name_type_validation(value):
    """Test that Pipeline.Name only accepts strings."""
    pipeline = datapipeline.Pipeline("ValidTitle123")
    
    if isinstance(value, str):
        pipeline.Name = value
        assert pipeline.Name == value
    else:
        with pytest.raises(TypeError):
            pipeline.Name = value  # Should raise but might not
```

**Failing input**: Integer values like `12345`

## Reproducing the Bug

```python
from troposphere import datapipeline

# Create a Pipeline object
pipeline = datapipeline.Pipeline("ValidTitle123")

# Name field should only accept strings per props definition: (str, True)
pipeline.Name = 12345  # Should raise TypeError but doesn't

print(f"pipeline.Name = {pipeline.Name}")
print(f"type(pipeline.Name) = {type(pipeline.Name)}")

# The integer is stored without type conversion
assert pipeline.Name == 12345
assert type(pipeline.Name) == int
```

## Why This Is A Bug

The Pipeline class defines Name as `(str, True)` in its props dictionary, indicating it should only accept string values. However, the validation logic in BaseAWSObject.__setattr__ appears to have a path that allows non-string values to be assigned. This violates the type contract and could lead to:

1. Invalid CloudFormation templates when serialized
2. Unexpected runtime errors when AWS processes the template
3. Inconsistent behavior compared to other type-validated properties

## Fix

The issue likely stems from the validation logic in BaseAWSObject.__setattr__. A fix would ensure strict type checking:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -249,6 +249,10 @@ class BaseAWSObject:
         elif name in self.propnames:
             # Check the type of the object and compare against what we were
             # expecting.
             expected_type = self.props[name][0]
+            
+            # Ensure strict type checking for basic types
+            if expected_type in (str, int, float, bool) and not isinstance(value, expected_type):
+                self._raise_type(name, value, expected_type)
 
             # If the value is a AWSHelperFn we can't do much validation
```