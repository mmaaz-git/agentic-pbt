# Bug Report: troposphere.evidently Numeric String Kwargs Cause AttributeError

**Target**: `troposphere.evidently`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

All AWS resource classes in troposphere.evidently raise confusing AttributeError when passed kwargs with numeric string keys (e.g., '0', '123', '-1').

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.evidently as evidently
import pytest

@given(st.dictionaries(
    st.text(min_size=1, max_size=50),
    st.one_of(st.none(), st.text(), st.integers(), st.floats(), st.booleans()),
    min_size=0,
    max_size=10
))
def test_arbitrary_kwargs_to_classes(kwargs):
    """Test what happens with arbitrary keyword arguments"""
    try:
        var = evidently.VariationObject(**kwargs)
        result = var.to_dict()
        if 'VariationName' in result:
            assert result['VariationName'] is not None
    except (TypeError, ValueError):
        pass
```

**Failing input**: `{'0': None}`

## Reproducing the Bug

```python
import troposphere.evidently as evidently

# Minimal reproduction
var = evidently.VariationObject(**{'0': 'value'})
```

Output:
```
AttributeError: VariationObject object does not support attribute 0
```

## Why This Is A Bug

The error occurs because the BaseAWSObject.__setattr__ method checks if attribute names are in the valid `propnames` set. Numeric string keys aren't valid CloudFormation properties, but the error message is misleading - it suggests the attribute '0' isn't supported rather than explaining it's an invalid property name. This affects all AWS classes in the module and could confuse users who accidentally pass numeric keys.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -313,7 +313,10 @@ class BaseAWSObject:
         else:
             type_name = type(self).__name__
             raise AttributeError(
-                "%s object does not support attribute %s" % (type_name, name)
+                "%s object does not support attribute %s. "
+                "Valid attributes are: %s" % (
+                    type_name, name, ", ".join(sorted(self.propnames))
+                )
             )
 
     def __repr__(self) -> str:
```