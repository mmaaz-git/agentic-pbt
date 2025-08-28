# Bug Report: trino.types.NamedRowTuple Shadows Tuple Methods

**Target**: `trino.types.NamedRowTuple`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

NamedRowTuple allows field names that shadow built-in tuple methods, making those methods inaccessible and causing TypeError when called.

## Property-Based Test

```python
def test_namedrowtuple_getattr_with_count_method():
    values = [1, 2, 3]
    names = ["count", "field2", "field3"]
    types = ["int", "int", "int"]
    
    row = NamedRowTuple(values, names, types)
    
    assert row.count == 1  # Returns the value, not the method
    assert row.count(1) == 1  # Should count occurrences but fails
```

**Failing input**: Field name "count" shadows tuple's count() method

## Reproducing the Bug

```python
from trino.types import NamedRowTuple

row = NamedRowTuple([1, 2, 3], ["count", "field2", "field3"], ["int", "int", "int"])
print(row.count)  # Prints: 1
row.count(1)  # TypeError: 'int' object is not callable
```

## Why This Is A Bug

NamedRowTuple inherits from tuple but allows field names that shadow tuple methods. This violates the Liskov Substitution Principle - a NamedRowTuple should be usable wherever a tuple is expected, but shadowing methods breaks this contract.

## Fix

```diff
--- a/trino/types.py
+++ b/trino/types.py
@@ -111,8 +111,11 @@ class NamedRowTuple(Tuple[Any, ...]):
         self.__annotations__["types"] = types
         elements: List[Any] = []
         for name, value in zip(names, values):
-            if name is not None and names.count(name) == 1:
-                setattr(self, name, value)
+            if name is not None and names.count(name) == 1:
+                # Don't shadow tuple methods
+                if not hasattr(tuple, name):
+                    setattr(self, name, value)
                 elements.append(f"{name}: {repr(value)}")
             else:
                 elements.append(repr(value))
```