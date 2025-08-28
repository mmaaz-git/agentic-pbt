# Bug Report: sqlalchemy.orm.polymorphic_union IndexError with Empty Table Map

**Target**: `sqlalchemy.orm.polymorphic_union`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

`polymorphic_union` raises an `IndexError` when called with an empty dictionary as the table_map argument, instead of handling the edge case gracefully.

## Property-Based Test

```python
def test_polymorphic_union_empty():
    """Test polymorphic_union with edge cases."""
    
    # Empty table map - should handle gracefully
    with pytest.raises((ValueError, KeyError, TypeError)):
        orm.polymorphic_union({}, 'type')
```

**Failing input**: `orm.polymorphic_union({}, 'type')`

## Reproducing the Bug

```python
import sqlalchemy.orm as orm

result = orm.polymorphic_union({}, 'type')
```

## Why This Is A Bug

The function documentation states it expects "a mapping of polymorphic identities to Table objects". An empty dictionary is a valid mapping, but the implementation crashes with `IndexError: list index out of range` instead of either:
1. Returning a valid empty union structure
2. Raising a more appropriate exception like `ValueError("table_map cannot be empty")`

The current behavior exposes implementation details through an uninformative error message.

## Fix

```diff
--- a/sqlalchemy/orm/util.py
+++ b/sqlalchemy/orm/util.py
@@ -390,6 +390,9 @@ def polymorphic_union(table_map, typecolname, aliasname='p_union', cast_nulls=T
     """
     colnames = util.OrderedSet()
     colnamemaps = {}
+    
+    if not table_map:
+        raise ValueError("table_map cannot be empty")
+        
     types = {}
     for key in table_map:
         table = table_map[key]
```