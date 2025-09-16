import sys
import importlib.machinery

# Check if importlib.machinery is a package or module
print(f"importlib.machinery.__name__ = {importlib.machinery.__name__}")
print(f"importlib.machinery.__file__ = {importlib.machinery.__file__}")
print(f"Is it a package? {hasattr(importlib.machinery, '__path__')}")

# Now test with pyramid's package_of function
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')
from pyramid.path import package_of, package_name

pkg_name = package_name(importlib.machinery)
print(f"\npackage_name(importlib.machinery) = {pkg_name}")

pkg = package_of(importlib.machinery)
print(f"package_of(importlib.machinery).__name__ = {pkg.__name__}")