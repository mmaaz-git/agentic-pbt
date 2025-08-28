import sys
import pyximport.pyximport as pyx
from pyximport.pyximport import PyxImportMetaFinder, PyImportMetaFinder

# Check inheritance
print("Checking class inheritance:")
print(f"PyImportMetaFinder.__bases__ = {PyImportMetaFinder.__bases__}")
print(f"PyxImportMetaFinder.__bases__ = {PyxImportMetaFinder.__bases__}")
print(f"Is PyImportMetaFinder a subclass of PyxImportMetaFinder? {issubclass(PyImportMetaFinder, PyxImportMetaFinder)}")
print()

# Create instances to test isinstance
py_imp = PyImportMetaFinder()
pyx_imp = PyxImportMetaFinder()

print("Testing isinstance checks from _have_importers logic:")
print(f"isinstance(py_imp, PyxImportMetaFinder) = {isinstance(py_imp, PyxImportMetaFinder)}")
print(f"isinstance(py_imp, PyImportMetaFinder) = {isinstance(py_imp, PyImportMetaFinder)}")
print(f"isinstance(pyx_imp, PyxImportMetaFinder) = {isinstance(pyx_imp, PyxImportMetaFinder)}")
print(f"isinstance(pyx_imp, PyImportMetaFinder) = {isinstance(pyx_imp, PyImportMetaFinder)}")
print()

# This reproduces the bug in _have_importers
print("Simulating _have_importers logic:")
test_meta_path = [py_imp, pyx_imp]
has_py_importer = False
has_pyx_importer = False

for importer in test_meta_path:
    if isinstance(importer, PyxImportMetaFinder):
        if isinstance(importer, PyImportMetaFinder):
            has_py_importer = True
            print(f"  Found PyImportMetaFinder: {importer}")
        else:
            has_pyx_importer = True
            print(f"  Found PyxImportMetaFinder: {importer}")

print(f"\nResult: has_py_importer={has_py_importer}, has_pyx_importer={has_pyx_importer}")
print("\nBUG: PyImportMetaFinder is never detected because it's not a subclass of PyxImportMetaFinder!")