# Bug Report: lml.plugin AttributeError with None in tags list

**Target**: `lml.plugin.PluginManager`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

PluginManager crashes with AttributeError when a plugin's tags list contains None, attempting to call .lower() on NoneType.

## Property-Based Test

```python
def test_none_in_tags():
    """Test that None values in tags are handled gracefully"""
    manager = lml.plugin.PluginManager("test")
    
    plugin_info = lml.plugin.PluginInfo(
        "test",
        abs_class_path="test.module.Class",
        tags=["valid", None, "another"]
    )
    
    # Should not crash
    manager.load_me_later(plugin_info)
```

**Failing input**: `tags=["valid", None, "another"]`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')
import lml.plugin

manager = lml.plugin.PluginManager("test_type")

plugin_info = lml.plugin.PluginInfo(
    "test_type",
    abs_class_path="test.module.TestClass",
    tags=["valid_tag", None, "another_tag"]
)

manager.load_me_later(plugin_info)
# AttributeError: 'NoneType' object has no attribute 'lower'
```

## Why This Is A Bug

The code assumes all tags are strings and calls .lower() without checking for None. This violates the principle of defensive programming and can crash when tags are dynamically generated and may contain None values due to logic errors or optional tag scenarios.

## Fix

```diff
--- a/lml/plugin.py
+++ b/lml/plugin.py
@@ -330,9 +330,11 @@ class PluginManager(object):
     def _update_registry_and_expand_tag_groups(self, plugin_info):
         primary_tag = None
         for index, key in enumerate(plugin_info.tags()):
-            self.registry[key.lower()].append(plugin_info)
+            if key is not None:
+                lower_key = key.lower()
+                self.registry[lower_key].append(plugin_info)
-            if index == 0:
-                primary_tag = key.lower()
-            self.tag_groups[key.lower()] = primary_tag
+                if index == 0:
+                    primary_tag = lower_key
+                self.tag_groups[lower_key] = primary_tag
```