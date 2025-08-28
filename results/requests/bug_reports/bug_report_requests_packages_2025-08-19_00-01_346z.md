# Bug Report: requests.packages Module Aliasing Issues

**Target**: `requests.packages`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `requests.packages` module has incomplete aliasing logic that fails to alias lazily-loaded submodules and creates an inconsistent package structure that breaks certain import mechanisms.

## Property-Based Test

```python
@given(st.sampled_from(['urllib3', 'idna']))
def test_sys_modules_registration(package_name):
    """Property: All aliased modules are properly registered in sys.modules"""
    import requests.packages
    
    # Get all modules that start with the package name
    original_modules = [m for m in sys.modules if m == package_name or m.startswith(f"{package_name}.")]
    
    # For each original module, there should be a corresponding aliased module
    for orig_mod in original_modules:
        aliased_name = f"requests.packages.{orig_mod}"
        assert aliased_name in sys.modules, f"Module {aliased_name} not in sys.modules"
        
        # They should be the same object
        assert sys.modules[orig_mod] is sys.modules[aliased_name]
```

**Failing input**: `package_name='urllib3'` after importing `urllib3.contrib`

## Reproducing the Bug

```python
import sys
import requests.packages

# Import a module that wasn't loaded when requests.packages ran
import urllib3.contrib.socks

# Check if it has an alias
alias_name = 'requests.packages.urllib3.contrib.socks'
print(f"{alias_name} in sys.modules: {alias_name in sys.modules}")
print(f"urllib3.contrib.socks in sys.modules: {'urllib3.contrib.socks' in sys.modules}")

# Clear aliased modules to demonstrate import order issue
for key in list(sys.modules.keys()):
    if 'requests.packages.urllib3' in key:
        del sys.modules[key]

# This will fail
try:
    import requests.packages.urllib3.exceptions
except ImportError as e:
    print(f"Import failed: {e}")
```

## Why This Is A Bug

The requests.packages module creates aliases for backwards compatibility, but:

1. **Incomplete aliasing**: Only modules already imported when requests.packages runs get aliased. Lazily-loaded modules like urllib3.contrib are missed.

2. **Not a real package**: requests.packages is a module (.py file) not a package (directory), lacking the `__path__` attribute. This breaks import mechanisms that expect package structure.

3. **Import order sensitivity**: Direct imports of submodules fail unless the parent is imported first, violating Python's normal import behavior.

## Fix

The aliasing logic should be made dynamic to catch lazily-loaded modules:

```diff
--- a/requests/packages.py
+++ b/requests/packages.py
@@ -1,5 +1,20 @@
 import sys
+import importlib.abc
+import importlib.machinery
 
+class AliasMetaFinder(importlib.abc.MetaPathFinder):
+    def find_spec(self, fullname, path, target=None):
+        if fullname.startswith('requests.packages.'):
+            real_name = fullname.replace('requests.packages.', '', 1)
+            for package in ('urllib3', 'idna', 'chardet', 'charset_normalizer'):
+                if real_name == package or real_name.startswith(f'{package}.'):
+                    try:
+                        return importlib.util.find_spec(real_name)
+                    except ImportError:
+                        pass
+        return None
+
+sys.meta_path.insert(0, AliasMetaFinder())
 from .compat import chardet
 
 # This code exists for backwards compatibility reasons.
```