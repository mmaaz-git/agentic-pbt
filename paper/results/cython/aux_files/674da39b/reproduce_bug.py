"""
Minimal reproduction of the pyximport bug found by Hypothesis testing.
"""
import sys
import tempfile
import pyximport

# Save initial state
initial_meta_path_count = len(sys.meta_path)
print(f"Initial meta_path count: {initial_meta_path_count}")

# First install - install only pyximport
with tempfile.TemporaryDirectory() as build_dir1:
    py1, pyx1 = pyximport.install(
        pyximport=True,
        pyimport=False,
        build_dir=build_dir1
    )
    print(f"\nAfter first install (pyximport=True, pyimport=False):")
    print(f"  py1: {py1}")
    print(f"  pyx1: {pyx1}")
    print(f"  meta_path count: {len(sys.meta_path)}")

    # Second install - install only pyimport  
    with tempfile.TemporaryDirectory() as build_dir2:
        py2, pyx2 = pyximport.install(
            pyximport=False,
            pyimport=True,
            build_dir=build_dir2
        )
        print(f"\nAfter second install (pyximport=False, pyimport=True):")
        print(f"  py2: {py2}")
        print(f"  pyx2: {pyx2}")
        print(f"  meta_path count: {len(sys.meta_path)}")
        
        # Try to uninstall both
        print("\nAttempting to uninstall both...")
        pyximport.uninstall(py1, pyx1)
        print(f"After uninstall(py1={py1}, pyx1={pyx1}): meta_path count = {len(sys.meta_path)}")
        
        pyximport.uninstall(py2, pyx2)
        print(f"After uninstall(py2={py2}, pyx2={pyx2}): meta_path count = {len(sys.meta_path)}")
        
        # Check if any importers remain
        from pyximport import pyximport as pyx_module
        remaining = []
        for importer in sys.meta_path:
            if isinstance(importer, pyx_module.PyxImportMetaFinder):
                remaining.append(f"PyxImportMetaFinder: {importer}")
            if isinstance(importer, pyx_module.PyImportMetaFinder):
                remaining.append(f"PyImportMetaFinder: {importer}")
        
        if remaining:
            print("\n❌ BUG FOUND: Importers still remain in sys.meta_path after uninstall:")
            for r in remaining:
                print(f"  - {r}")
        else:
            print("\n✓ All importers successfully removed")

print(f"\nFinal meta_path count: {len(sys.meta_path)}")
print(f"Expected: {initial_meta_path_count}, Actual: {len(sys.meta_path)}")