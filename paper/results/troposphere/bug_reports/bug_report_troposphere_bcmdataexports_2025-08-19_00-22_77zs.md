# Bug Report: troposphere.bcmdataexports Cannot Delete Properties After Setting

**Target**: `troposphere.bcmdataexports`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Properties stored in troposphere AWS objects cannot be deleted using `del` after being set, even though they can be accessed via attribute syntax.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
import troposphere.bcmdataexports as bcm

@given(
    query=st.text(min_size=1, max_size=100),
    table_configs=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.dictionaries(st.text(min_size=1), st.text(min_size=1), max_size=3),
        min_size=1,
        max_size=3
    )
)
def test_property_deletion_behavior(query, table_configs):
    """Test what happens when we delete properties after setting them"""
    data_query = bcm.DataQuery(QueryStatement=query)
    data_query.TableConfigurations = table_configs
    
    dict_before = data_query.to_dict()
    assert "TableConfigurations" in dict_before
    
    del data_query.TableConfigurations  # Raises AttributeError
```

**Failing input**: Any valid query and table_configs (e.g., `query='0', table_configs={'0': {}}`)

## Reproducing the Bug

```python
import troposphere.bcmdataexports as bcm

data_query = bcm.DataQuery(QueryStatement="SELECT * FROM table")
data_query.TableConfigurations = {"key": {"nested": "value"}}
print(f"Property accessible: {data_query.TableConfigurations}")
del data_query.TableConfigurations  # AttributeError: 'DataQuery' object has no attribute 'TableConfigurations'
```

## Why This Is A Bug

The asymmetry between setting/getting and deleting violates the principle of least surprise. Properties can be set and accessed via attribute syntax but cannot be deleted the same way, despite being stored in `self.properties` dict. The missing `__delattr__` implementation causes Python to look in `__dict__` instead of `self.properties`.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -318,6 +318,15 @@ class BaseAWSObject:
             "%s object does not support attribute %s" % (type_name, name)
         )
 
+    def __delattr__(self, name: str) -> None:
+        if name in self.__dict__:
+            dict.__delattr__(self, name)
+        elif name in self.properties:
+            del self.properties[name]
+        else:
+            raise AttributeError(
+                f"{self.__class__.__name__} object has no attribute {name}"
+            )
+
     def _raise_type(self, name: str, value: Any, expected_type: Any) -> NoReturn:
         raise TypeError(
```