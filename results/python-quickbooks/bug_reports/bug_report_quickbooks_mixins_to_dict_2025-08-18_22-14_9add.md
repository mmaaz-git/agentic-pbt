# Bug Report: quickbooks.mixins.to_dict Circular Reference RecursionError

**Target**: `quickbooks.mixins.to_dict`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `to_dict()` function in quickbooks.mixins crashes with RecursionError when processing objects containing circular references.

## Property-Based Test

```python
def test_circular_reference_to_dict():
    """Test to_dict behavior with circular references"""
    
    class TestObject(QuickbooksBaseObject):
        def __init__(self):
            self.value = "test"
            self.ref = None
    
    obj1 = TestObject()
    obj2 = TestObject()
    
    # Create circular reference
    obj1.ref = obj2
    obj2.ref = obj1
    
    # This causes RecursionError
    dict_repr = to_dict(obj1)
```

**Failing input**: Any two objects with mutual references

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from quickbooks.objects.base import QuickbooksBaseObject
from quickbooks.mixins import to_dict

class SimpleObject(QuickbooksBaseObject):
    def __init__(self):
        self.name = ""
        self.reference = None

obj1 = SimpleObject()
obj1.name = "Object 1"

obj2 = SimpleObject()
obj2.name = "Object 2"

obj1.reference = obj2
obj2.reference = obj1

result = to_dict(obj1)  # Raises RecursionError
```

## Why This Is A Bug

The `to_dict()` function recursively converts objects to dictionaries but lacks cycle detection. When objects reference each other, the function enters infinite recursion, violating the expected behavior of safely converting any QuickBooks object to a dictionary representation.

## Fix

```diff
--- a/quickbooks/mixins.py
+++ b/quickbooks/mixins.py
@@ -59,8 +59,14 @@
 
 
 # Based on http://stackoverflow.com/a/1118038
-def to_dict(obj, classkey=None):
+def to_dict(obj, classkey=None, _visited=None):
     """
     Recursively converts Python object into a dictionary
     """
+    if _visited is None:
+        _visited = set()
+    
+    if id(obj) in _visited:
+        return None  # or return a placeholder like "<circular reference>"
+    
     if isinstance(obj, dict):
         data = {}
+        _visited.add(id(obj))
         for (k, v) in obj.items():
-            data[k] = to_dict(v, classkey)
+            data[k] = to_dict(v, classkey, _visited)
+        _visited.discard(id(obj))
         return data
     elif hasattr(obj, "_ast"):
-        return to_dict(obj._ast())
+        return to_dict(obj._ast(), classkey, _visited)
     elif hasattr(obj, "__iter__") and not isinstance(obj, str):
-        return [to_dict(v, classkey) for v in obj]
+        return [to_dict(v, classkey, _visited) for v in obj]
     elif hasattr(obj, "__dict__"):
-        data = dict([(key, to_dict(value, classkey))
+        _visited.add(id(obj))
+        data = dict([(key, to_dict(value, classkey, _visited))
                     for key, value in obj.__dict__.items()
                     if not callable(value) and not key.startswith('_')])
+        _visited.discard(id(obj))
 
         if classkey is not None and hasattr(obj, "__class__"):
             data[classkey] = obj.__class__.__name__
```