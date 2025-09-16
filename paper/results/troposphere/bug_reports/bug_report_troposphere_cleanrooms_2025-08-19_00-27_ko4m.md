# Bug Report: troposphere.cleanrooms None Handling for Optional Properties

**Target**: `troposphere.cleanrooms`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Optional properties in troposphere.cleanrooms classes cannot be explicitly set to None, causing a TypeError instead of treating None as an unset value.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.cleanrooms as cleanrooms
import pytest

@given(
    name=st.text(min_size=1, max_size=100),
    param_type=st.text(min_size=1, max_size=50)
)
def test_optional_property_none_handling(name, param_type):
    """Test that optional properties can be set to None."""
    # DefaultValue is optional but setting it to None raises TypeError
    with pytest.raises(TypeError, match="DefaultValue is <class 'NoneType'>, expected"):
        obj = cleanrooms.AnalysisParameter(
            Name=name,
            Type=param_type,
            DefaultValue=None
        )
        obj.to_dict()
```

**Failing input**: `name='test', param_type='STRING'`

## Reproducing the Bug

```python
import troposphere.cleanrooms as cleanrooms

obj = cleanrooms.AnalysisParameter(
    Name="test",
    Type="STRING", 
    DefaultValue=None
)
```

## Why This Is A Bug

The DefaultValue property is marked as optional (False) in the props definition, meaning it should be acceptable to omit it or explicitly unset it. However, when users explicitly pass None for an optional property, the library raises a TypeError. This violates the expected contract that optional properties can be None or omitted. The bug affects multiple classes including AnalysisParameter, AthenaTableReference, AnalysisRuleAggregation, ProtectedQueryS3OutputConfiguration, and others.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -248,6 +248,11 @@ class BaseAWSObject:
             return None
         elif name in self.propnames:
             # Check the type of the object and compare against what we were
             # expecting.
             expected_type = self.props[name][0]
+            required = self.props[name][1]
+            
+            # Allow None for optional properties
+            if value is None and not required:
+                return None
 
             # If the value is a AWSHelperFn we can't do much validation
```