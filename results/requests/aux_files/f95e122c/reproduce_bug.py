#!/usr/bin/env python3
"""Minimal reproduction of requests.packages bug"""

import sys
import importlib

# Step 1: Fresh Python state
print("Step 1: Clear any cached modules")
modules_to_clear = [m for m in list(sys.modules.keys()) if 'requests' in m]
for mod in modules_to_clear:
    del sys.modules[mod]

# Step 2: Import requests.packages
print("\nStep 2: Import requests.packages")
import requests.packages
print("Success: requests.packages imported")

# Step 3: Check if it's a proper package
print("\nStep 3: Check package attributes")
has_path = hasattr(requests.packages, '__path__')
print(f"Has __path__ attribute (required for packages): {has_path}")

# Step 4: Try to import submodule using importlib
print("\nStep 4: Try importing submodule with importlib.import_module")
try:
    # First ensure urllib3 is in sys.modules via aliasing
    import urllib3
    print(f"urllib3 imported, now in sys.modules: {'urllib3' in sys.modules}")
    print(f"requests.packages.urllib3 in sys.modules: {'requests.packages.urllib3' in sys.modules}")
    
    # Now try importlib.import_module on a fresh interpreter
    import subprocess
    result = subprocess.run([
        sys.executable, '-c', 
        "import importlib; import requests.packages; importlib.import_module('requests.packages.urllib3')"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("FAILED with fresh interpreter:")
        print(result.stderr)
    else:
        print("SUCCESS with fresh interpreter")
        
except Exception as e:
    print(f"Error: {e}")

# Step 5: Demonstrate the inconsistency
print("\nStep 5: Demonstrate the inconsistency")
print("Regular import syntax works:")
try:
    import requests.packages.urllib3
    print(f"  import requests.packages.urllib3: SUCCESS")
except ImportError as e:
    print(f"  import requests.packages.urllib3: FAILED - {e}")

print("\nBut requests.packages is not a real package:")
print(f"  isinstance(requests.packages.__file__, str): {isinstance(requests.packages.__file__, str)}")
print(f"  requests.packages.__file__.endswith('.py'): {requests.packages.__file__.endswith('.py')}")
print(f"  Real packages have __path__, this doesn't: {not hasattr(requests.packages, '__path__')}")