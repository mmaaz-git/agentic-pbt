# Bug Report: troposphere.glue String Formatting Error in Validators

**Target**: `troposphere.validators.glue`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

All five validators in troposphere.validators.glue crash with TypeError when given invalid input due to incorrect string formatting syntax using `%` instead of `%s`.

## Property-Based Test

```python
import hypothesis.strategies as st
from hypothesis import given, assume
import pytest
from troposphere.validators.glue import connection_type_validator

@given(st.text(min_size=1))
def test_connection_type_validator_formatting_bug(invalid_type):
    """Test that validator crashes on invalid input due to string formatting bug"""
    valid_types = ["CUSTOM", "JDBC", "KAFKA", "MARKETPLACE", "MONGODB", "NETWORK", "SFTP", "SNOWFLAKE"]
    assume(invalid_type not in valid_types)
    
    with pytest.raises(TypeError):
        connection_type_validator(invalid_type)
```

**Failing input**: `"INVALID"` (or any string not in the valid list)

## Reproducing the Bug

```python
from troposphere.validators.glue import connection_type_validator

connection_type_validator("INVALID")
```

## Why This Is A Bug

The validators are supposed to raise ValueError with a helpful error message when given invalid input. Instead, they crash with TypeError because the string formatting uses `%` instead of `%s`. This affects all five validators in the module:
- connection_type_validator (line 32)
- delete_behavior_validator (line 46) 
- update_behavior_validator (line 59)
- table_type_validator (line 72)
- trigger_type_validator (line 87)

## Fix

```diff
--- a/troposphere/validators/glue.py
+++ b/troposphere/validators/glue.py
@@ -29,7 +29,7 @@ def connection_type_validator(type):
         "SNOWFLAKE",
     ]
     if type not in valid_types:
-        raise ValueError("% is not a valid value for ConnectionType" % type)
+        raise ValueError("%s is not a valid value for ConnectionType" % type)
     return type
 
 
@@ -43,7 +43,7 @@ def delete_behavior_validator(value):
         "DEPRECATE_IN_DATABASE",
     ]
     if value not in valid_values:
-        raise ValueError("% is not a valid value for DeleteBehavior" % value)
+        raise ValueError("%s is not a valid value for DeleteBehavior" % value)
     return value
 
 
@@ -56,7 +56,7 @@ def update_behavior_validator(value):
         "UPDATE_IN_DATABASE",
     ]
     if value not in valid_values:
-        raise ValueError("% is not a valid value for UpdateBehavior" % value)
+        raise ValueError("%s is not a valid value for UpdateBehavior" % value)
     return value
 
 
@@ -69,7 +69,7 @@ def table_type_validator(type):
         "VIRTUAL_VIEW",
     ]
     if type not in valid_types:
-        raise ValueError("% is not a valid value for TableType" % type)
+        raise ValueError("%s is not a valid value for TableType" % type)
     return type
 
 
@@ -84,6 +84,6 @@ def trigger_type_validator(type):
         "EVENT",
     ]
     if type not in valid_types:
-        raise ValueError("% is not a valid value for Type" % type)
+        raise ValueError("%s is not a valid value for Type" % type)
     return type
```