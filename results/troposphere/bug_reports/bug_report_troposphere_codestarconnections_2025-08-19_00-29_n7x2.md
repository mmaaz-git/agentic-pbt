# Bug Report: troposphere.codestarconnections None Handling for Optional Properties

**Target**: `troposphere.codestarconnections` (affects all troposphere classes)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Troposphere raises TypeError when None is explicitly passed for optional properties, violating Python conventions where None represents absence of value.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.codestarconnections as csc

@given(title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=100))
def test_connection_with_none_values(title):
    """Test that Connection handles None values properly for optional properties"""
    conn = csc.Connection(
        title=title,
        ConnectionName="test",
        HostArn=None,  # Optional property - should be accepted
    )
    conn_dict = conn.to_dict()
    assert "HostArn" not in conn_dict.get("Properties", {})
```

**Failing input**: Any valid title, e.g., `title='Test1'`

## Reproducing the Bug

```python
import troposphere.codestarconnections as csc

# This works - omitting optional property
conn1 = csc.Connection(
    title="Test1",
    ConnectionName="MyConnection"
)
print("Without HostArn:", conn1.to_dict())

# This fails - explicitly passing None for optional property  
conn2 = csc.Connection(
    title="Test2", 
    ConnectionName="MyConnection",
    HostArn=None
)
```

## Why This Is A Bug

This violates Python conventions and user expectations:
1. None is Python's standard representation for "no value"
2. Most Python APIs accept None for optional parameters
3. Users expect `func(param=None)` to behave like `func()` for optional parameters
4. The distinction between omitting a parameter and passing None is unexpected

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -248,6 +248,10 @@ class BaseAWSObject:
             return None
         elif name in self.propnames:
+            # Handle None for optional properties
+            if value is None and not self.props[name][1]:  # [1] is required flag
+                return  # Don't set the property if None and optional
+            
             # Check the type of the object and compare against what we were
             # expecting.
             expected_type = self.props[name][0]
```