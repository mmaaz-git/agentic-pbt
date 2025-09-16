#!/usr/bin/env python3
"""Demonstrate the requests.packages module aliasing bug"""

import sys

# Bug 1: Missing aliases for lazily-imported modules
print("Bug 1: Missing module aliases")
print("=" * 50)

# Import requests.packages which sets up aliases
import requests.packages

# Now import a module that wasn't imported when requests.packages ran
import urllib3.contrib.socks

# Check if it has an alias
alias_name = 'requests.packages.urllib3.contrib.socks'
if alias_name in sys.modules:
    print(f"✓ {alias_name} exists in sys.modules")
else:
    print(f"✗ BUG: {alias_name} NOT in sys.modules")
    print(f"  But urllib3.contrib.socks IS in sys.modules: {'urllib3.contrib.socks' in sys.modules}")

# Bug 2: requests.packages is not a real package
print("\nBug 2: Package structure inconsistency")
print("=" * 50)

# Check package attributes
print(f"requests.packages.__file__ = {requests.packages.__file__}")
print(f"Has __path__ attribute: {hasattr(requests.packages, '__path__')}")

# This causes issues with certain import mechanisms
import importlib.util

# Try to find spec for submodule
spec = importlib.util.find_spec('requests.packages.urllib3')
print(f"\nimportlib.util.find_spec('requests.packages.urllib3'):")
if spec:
    print(f"  Found spec: {spec}")
else:
    print(f"  ✗ BUG: Could not find spec (but module exists in sys.modules!)")
    print(f"  sys.modules has it: {'requests.packages.urllib3' in sys.modules}")

# Bug 3: Import order sensitivity
print("\nBug 3: Import order sensitivity")
print("=" * 50)

# Clear the aliased modules
for key in list(sys.modules.keys()):
    if 'requests.packages.urllib3' in key:
        del sys.modules[key]

print("Cleared requests.packages.urllib3.* from sys.modules")

# Now try to import a submodule directly
try:
    # This will fail because requests.packages is not a real package
    exec("import requests.packages.urllib3.exceptions")
    print("✓ Direct import succeeded")
except ImportError as e:
    print(f"✗ BUG: Direct import failed: {e}")
    print("  This works if urllib3 is imported first, showing order dependency")