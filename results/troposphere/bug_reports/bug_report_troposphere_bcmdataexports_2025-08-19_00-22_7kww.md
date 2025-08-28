# Bug Report: troposphere.bcmdataexports Cannot Set Optional Properties to None

**Target**: `troposphere.bcmdataexports`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Optional properties in troposphere AWS objects cannot be set to None, raising a TypeError instead of allowing the property to be unset.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.bcmdataexports as bcm

@given(query=st.text(min_size=1, max_size=100))
def test_none_values_for_optional_properties(query):
    """Test that None values are handled correctly for optional properties"""
    data_query = bcm.DataQuery(QueryStatement=query)
    
    # Try setting optional property to None
    data_query.TableConfigurations = None  # Raises TypeError
    
    dict_repr = data_query.to_dict()
    assert "QueryStatement" in dict_repr
```

**Failing input**: Any valid query string (e.g., `"0"`)

## Reproducing the Bug

```python
import troposphere.bcmdataexports as bcm

data_query = bcm.DataQuery(QueryStatement="SELECT * FROM table")
data_query.TableConfigurations = None  # Raises TypeError
```

## Why This Is A Bug

Optional properties should be settable to None to unset them or indicate absence. The current implementation incorrectly validates None against the expected type (dict) instead of allowing it for optional properties. This violates the principle that optional properties can be absent or null.

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
+            # Allow None for optional properties
+            if not required and value is None:
+                return self.properties.__setitem__(name, value)
 
             # If the value is a AWSHelperFn we can't do much validation
```