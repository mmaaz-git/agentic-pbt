#!/usr/bin/env python3
"""Exact reproduction of the bug found by Hypothesis"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')

from lml.plugin import PluginInfo, PluginManager

# The exact failing case from Hypothesis
base_key = 'ı'  # Latin Small Letter Dotless I
key_upper = base_key.upper()  # This becomes 'I'

print(f"Original lowercase key: '{base_key}'")
print(f"Uppercase version: '{key_upper}'")
print(f"Uppercase then lowercase: '{key_upper.lower()}'")
print()

# Create manager and register plugin with uppercase tag
manager = PluginManager("test")
plugin_info = PluginInfo("test", 
                        abs_class_path="test.module.TestClass",
                        tags=[key_upper])  # Register with 'I'

manager.load_me_later(plugin_info)

print(f"Registered plugin with tag: '{key_upper}'")
print(f"Registry contains keys: {list(manager.registry.keys())}")
print()

# The issue: we register with 'I', which gets lowercased to 'i' in the registry
# But the original lowercase was 'ı', not 'i'
print(f"Can we find it with original lowercase 'ı'? {base_key in manager.registry}")
print(f"Can we find it with 'i'? {'i' in manager.registry}")
print()

# This demonstrates the bug: if a user has a tag that when uppercased
# and then lowercased doesn't equal the original, lookups will fail
print("BUG DEMONSTRATED:")
print("1. User has tag 'ı' (dotless i)")
print("2. They uppercase it to 'I' for registration")
print("3. Plugin manager stores it under 'i' (regular i)")
print("4. Looking up with original 'ı' fails!")
print()
print("This violates the expected case-insensitive lookup behavior")