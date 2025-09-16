"""
Check the class inheritance hierarchy to understand the bug.
"""
import pyximport
from pyximport import pyximport as pyx_module

print("Class hierarchy:")
print(f"PyImportMetaFinder bases: {pyx_module.PyImportMetaFinder.__bases__}")
print(f"PyxImportMetaFinder bases: {pyx_module.PyxImportMetaFinder.__bases__}")

print("\nInheritance checks:")
print(f"PyImportMetaFinder is subclass of PyxImportMetaFinder: {issubclass(pyx_module.PyImportMetaFinder, pyx_module.PyxImportMetaFinder)}")
print(f"PyxImportMetaFinder is subclass of PyImportMetaFinder: {issubclass(pyx_module.PyxImportMetaFinder, pyx_module.PyImportMetaFinder)}")

# Create instances to test isinstance
import tempfile
with tempfile.TemporaryDirectory() as td:
    py_finder = pyx_module.PyImportMetaFinder(pyxbuild_dir=td)
    pyx_finder = pyx_module.PyxImportMetaFinder(pyxbuild_dir=td)
    
    print("\nInstance checks:")
    print(f"py_finder isinstance PyImportMetaFinder: {isinstance(py_finder, pyx_module.PyImportMetaFinder)}")
    print(f"py_finder isinstance PyxImportMetaFinder: {isinstance(py_finder, pyx_module.PyxImportMetaFinder)}")
    print(f"pyx_finder isinstance PyImportMetaFinder: {isinstance(pyx_finder, pyx_module.PyImportMetaFinder)}")
    print(f"pyx_finder isinstance PyxImportMetaFinder: {isinstance(pyx_finder, pyx_module.PyxImportMetaFinder)}")

print("\n_have_importers() function code check:")
print("The issue is in lines 359-363 of pyximport.py:")
print("    if isinstance(importer, PyxImportMetaFinder):")
print("        if isinstance(importer, PyImportMetaFinder):")  
print("            has_py_importer = True")
print("        else:")
print("            has_pyx_importer = True")
print("\nThe logic is WRONG! It checks if PyImportMetaFinder is also a PyxImportMetaFinder")
print("But PyImportMetaFinder is NOT a subclass of PyxImportMetaFinder!")
print("So PyImportMetaFinder instances will never match the outer if condition.")