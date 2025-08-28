# Bug Report: lml.plugin Unicode Case-Insensitive Lookup Failure

**Target**: `lml.plugin.PluginManager`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

PluginManager's case-insensitive tag lookup fails for Unicode characters with non-reversible case transformations, such as Turkish dotless i ('ı').

## Property-Based Test

```python
@given(
    plugin_type=python_identifier,
    base_key=st.text(alphabet=st.characters(whitelist_categories=('Ll',)), min_size=1, max_size=20)
)
def test_plugin_manager_case_insensitive_lookup(plugin_type, base_key):
    """Test that PluginManager registry uses case-insensitive keys"""
    key_lower = base_key.lower()
    key_upper = base_key.upper()
    
    manager = PluginManager(plugin_type)
    
    plugin_info = PluginInfo(plugin_type, 
                            abs_class_path="test.module.TestClass",
                            tags=[key_upper])
    
    manager.load_me_later(plugin_info)
    
    assert key_lower in manager.registry
```

**Failing input**: `base_key='ı'` (Latin Small Letter Dotless I, U+0131)

## Reproducing the Bug

```python
from lml.plugin import PluginInfo, PluginManager

base_key = 'ı'
key_upper = base_key.upper()

manager = PluginManager("test")
plugin_info = PluginInfo("test", 
                        abs_class_path="test.module.TestClass",
                        tags=[key_upper])

manager.load_me_later(plugin_info)

print(f"Registry keys: {list(manager.registry.keys())}")
print(f"Looking for 'ı': {'ı' in manager.registry}")
print(f"Looking for 'i': {'i' in manager.registry}")
```

## Why This Is A Bug

The PluginManager implements case-insensitive tag lookup by converting all tags to lowercase before storing them in the registry. However, for certain Unicode characters, the transformation `lower(upper(x))` does not equal `lower(x)`. 

For example:
- 'ı' (dotless i) uppercases to 'I'
- 'I' lowercases to 'i' (regular i) 
- Therefore: `lower(upper('ı')) = 'i' ≠ 'ı' = lower('ı')`

This violates the expected case-insensitive behavior where all case variations of a tag should map to the same registry entry. Users registering plugins with Turkish or Azerbaijani text containing dotless i will experience lookup failures.

## Fix

The issue occurs in the `_update_registry_and_expand_tag_groups` method which uses simple `.lower()` for normalization. A proper fix would use Unicode case folding:

```diff
--- a/lml/plugin.py
+++ b/lml/plugin.py
@@ -330,9 +330,9 @@ class PluginManager(object):
     def _update_registry_and_expand_tag_groups(self, plugin_info):
         primary_tag = None
         for index, key in enumerate(plugin_info.tags()):
-            self.registry[key.lower()].append(plugin_info)
+            self.registry[key.casefold()].append(plugin_info)
             if index == 0:
-                primary_tag = key.lower()
-            self.tag_groups[key.lower()] = primary_tag
+                primary_tag = key.casefold()
+            self.tag_groups[key.casefold()] = primary_tag
```

Similar changes would be needed in the `load_me_now` and `get_primary_key` methods to use `.casefold()` instead of `.lower()` for proper Unicode case-insensitive comparisons.