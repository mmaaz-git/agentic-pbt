#!/usr/bin/env python3
"""Test the impact of the Unicode case handling bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')

from lml.plugin import PluginInfo, PluginManager

# Test with Turkish locale-specific characters
# In Turkish, 'i'.upper() = 'İ' (with dot) and 'ı'.upper() = 'I' (without dot)

class TestPlugin:
    """A simple test plugin"""
    pass

# Create a plugin manager
manager = PluginManager("test_type")

# Register a plugin with tag 'ıstanbul' (starts with dotless i)
plugin_info = PluginInfo("test_type", tags=['ıstanbul'])
plugin_info.cls = TestPlugin
manager.load_me_later(plugin_info)

print("Registered plugin with tag 'ıstanbul'")
print(f"Registry keys: {list(manager.registry.keys())}")
print()

# Try to retrieve it with the original tag
try:
    plugin = manager.load_me_now('ıstanbul')
    print(f"SUCCESS: Retrieved plugin with key 'ıstanbul'")
except Exception as e:
    print(f"FAILED: Could not retrieve plugin with key 'ıstanbul'")
    print(f"Error: {e}")
print()

# The plugin is actually stored under 'istanbul' (with regular i)
try:
    plugin = manager.load_me_now('istanbul')
    print(f"SUCCESS: Retrieved plugin with key 'istanbul' (different from original!)")
except Exception as e:
    print(f"FAILED: Could not retrieve plugin with key 'istanbul'")
    print(f"Error: {e}")