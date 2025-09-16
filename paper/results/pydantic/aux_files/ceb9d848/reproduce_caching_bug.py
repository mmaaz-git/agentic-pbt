#!/usr/bin/env python3
"""Minimal reproduction of get_plugins caching bug."""

import os
import pydantic.plugin._loader as loader

# Reset global state
loader._plugins = None
loader._loading_plugins = False

# Disable all plugins
os.environ['PYDANTIC_DISABLE_PLUGINS'] = '__all__'

# First call to get_plugins
plugins = list(loader.get_plugins())
print(f"Plugins returned: {plugins}")
print(f"_plugins cache after call: {loader._plugins}")

# The bug: When PYDANTIC_DISABLE_PLUGINS is set to '__all__', '1', or 'true',
# get_plugins returns () immediately without setting _plugins cache.
# This means _plugins remains None instead of being set to an empty dict.

# Expected: _plugins should be {} (empty dict) after the call
# Actual: _plugins is None

if loader._plugins is None:
    print("\nBUG FOUND: _plugins is None instead of being cached as an empty dict")
    print("This violates the caching property - subsequent calls will not use cache")
else:
    print("\nNo bug: _plugins is properly cached")