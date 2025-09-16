#!/usr/bin/env python3
"""Minimal reproduction of the JSON representation issue"""

import sys
import json

# Add the lml_env site-packages to the path  
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')

import lml.plugin

# Test with special character
plugin_type = '\x1f'  # Unit separator character
plugin_info = lml.plugin.PluginInfo(
    plugin_type,
    abs_class_path=None
)

repr_str = repr(plugin_info)
print(f"Plugin type: {repr(plugin_type)}")
print(f"Repr output: {repr_str}")
print(f"Is original character in repr? {plugin_type in repr_str}")

# Check what standard JSON does
test_dict = {"plugin_type": plugin_type}
json_str = json.dumps(test_dict)
print(f"\nStandard JSON output: {json_str}")
print(f"Is original character in JSON? {plugin_type in json_str}")

# The issue: When plugin_type contains special characters, 
# the JSON representation escapes them, making the original
# character not present in the string representation.
# This could be confusing when debugging.

print("\n--- Testing with regular string ---")
plugin_type2 = "normal"
plugin_info2 = lml.plugin.PluginInfo(
    plugin_type2,
    abs_class_path=None
)

repr_str2 = repr(plugin_info2)
print(f"Plugin type: {repr(plugin_type2)}")
print(f"Repr output: {repr_str2}")
print(f"Is original string in repr? {plugin_type2 in repr_str2}")