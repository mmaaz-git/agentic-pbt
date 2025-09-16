#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

import inspect
import sphinxcontrib.jsmath
from sphinxcontrib.jsmath import version

# Explore the module
print("Module functions and classes:")
for name, obj in inspect.getmembers(sphinxcontrib.jsmath):
    if not name.startswith('_'):
        print(f"  {name}: {type(obj)}")

print("\nVersion info:")
print(f"  __version__ = {version.__version__}")
print(f"  __version_info__ = {version.__version_info__}")

# Check if we can test version parsing
print("\nTest version parsing logic:")
test_version = "2.3.4"
test_info = tuple(map(int, test_version.split('.')))
print(f"  '{test_version}' -> {test_info}")