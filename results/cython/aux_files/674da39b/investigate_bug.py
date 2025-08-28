"""
Investigate the root cause of the bug in pyximport.install()
"""
import sys
import tempfile
import pyximport
from pyximport import pyximport as pyx_module

# Let's trace through what _have_importers() is doing
print("Initial sys.meta_path:")
for i, imp in enumerate(sys.meta_path):
    print(f"  [{i}] {type(imp).__name__}: {imp}")

print("\n_have_importers() before any install:")
has_py, has_pyx = pyx_module._have_importers()
print(f"  has_py_importer: {has_py}")
print(f"  has_pyx_importer: {has_pyx}")

with tempfile.TemporaryDirectory() as build_dir1:
    # First install
    print("\nFirst install(pyimport=True)...")
    py1, pyx1 = pyximport.install(pyximport=False, pyimport=True, build_dir=build_dir1)
    
    print("\nsys.meta_path after first install:")
    for i, imp in enumerate(sys.meta_path):
        print(f"  [{i}] {type(imp).__name__}: {imp}")
    
    print("\n_have_importers() after first install:")
    has_py, has_pyx = pyx_module._have_importers()
    print(f"  has_py_importer: {has_py}")
    print(f"  has_pyx_importer: {has_pyx}")
    
    # Check the type checking in _have_importers
    print("\nAnalyzing _have_importers logic:")
    for importer in sys.meta_path:
        if isinstance(importer, pyx_module.PyxImportMetaFinder):
            print(f"  Found PyxImportMetaFinder: {importer}")
            if isinstance(importer, pyx_module.PyImportMetaFinder):
                print(f"    - This is ALSO a PyImportMetaFinder!")
            else:
                print(f"    - This is NOT a PyImportMetaFinder")
    
    # Second install
    print("\nSecond install(pyimport=True)...")
    py2, pyx2 = pyximport.install(pyximport=False, pyimport=True, build_dir=build_dir1)
    
    print(f"\nResult of second install:")
    print(f"  py2: {py2} (should be None)")
    print(f"  pyx2: {pyx2}")
    
    # Clean up
    pyximport.uninstall(py1, pyx1)
    pyximport.uninstall(py2, pyx2)