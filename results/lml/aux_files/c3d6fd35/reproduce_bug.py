#!/usr/bin/env python3
"""Minimal reproduction of the Unicode case handling bug in lml"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')

from lml.plugin import PluginInfo, PluginManager

# Demonstrate the Unicode case conversion issue
char = 'ı'  # Latin Small Letter Dotless I
print(f"Original character: '{char}'")
print(f"Upper case: '{char.upper()}'")
print(f"Upper then lower: '{char.upper().lower()}'")
print(f"char != char.upper().lower(): {char != char.upper().lower()}")
print()

# Create a plugin manager
manager = PluginManager("test_plugin")

# Register a plugin with a tag containing the problematic character
tag = 'ı'  # This will be uppercased to 'I' in the tags
plugin_info = PluginInfo("test_plugin", 
                        abs_class_path="test.module.TestClass",
                        tags=[tag.upper()])  # This becomes 'I'

manager.load_me_later(plugin_info)

# The plugin is registered under 'i' (lowercase of 'I')
print(f"Registry keys: {list(manager.registry.keys())}")
print(f"Looking for 'ı': {'ı' in manager.registry}")
print(f"Looking for 'i': {'i' in manager.registry}")
print()
print("BUG: The plugin registered with tag 'I' (uppercase of 'ı') is stored under key 'i',")
print("but looking up with the original lowercase 'ı' fails.")