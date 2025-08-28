#!/usr/bin/env python3
"""Minimal reproduction of the None in tags bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')

import lml.plugin

# Create a plugin manager
manager = lml.plugin.PluginManager("test_type")

# Create a plugin with None in the tags list
# This is a realistic scenario if tags are dynamically generated
# and one of them ends up being None due to a logic error
plugin_info = lml.plugin.PluginInfo(
    "test_type",
    abs_class_path="test.module.TestClass",
    tags=["valid_tag", None, "another_tag"]  # None in the middle
)

# Try to register it - this will crash
try:
    manager.load_me_later(plugin_info)
    print("No error - plugin registered successfully")
except AttributeError as e:
    print(f"Bug confirmed! Error: {e}")
    print("\nThis happens at line 333 in plugin.py:")
    print("    self.registry[key.lower()].append(plugin_info)")
    print("When key is None, calling .lower() raises AttributeError")
    
print("\n--- Testing workaround with filtered tags ---")
# Workaround: filter out None values
filtered_tags = [tag for tag in ["valid_tag", None, "another_tag"] if tag is not None]
plugin_info2 = lml.plugin.PluginInfo(
    "test_type",
    abs_class_path="test.module.TestClass",
    tags=filtered_tags
)
manager.load_me_later(plugin_info2)
print(f"Workaround successful. Registry keys: {list(manager.registry.keys())}")