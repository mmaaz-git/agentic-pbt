"""
Testing the second failure case found by Hypothesis: 
Installing pyimport twice should not add it twice.
"""
import sys
import tempfile
import pyximport
from pyximport import pyximport as pyx_module

# Count initial PyImportMetaFinder instances
initial_count = sum(1 for imp in sys.meta_path if isinstance(imp, pyx_module.PyImportMetaFinder))
print(f"Initial PyImportMetaFinder count: {initial_count}")

with tempfile.TemporaryDirectory() as build_dir1:
    # First install - pyimport only
    print("\nFirst install(pyximport=False, pyimport=True)...")
    py1, pyx1 = pyximport.install(
        pyximport=False,
        pyimport=True,
        build_dir=build_dir1
    )
    
    count_after_first = sum(1 for imp in sys.meta_path if isinstance(imp, pyx_module.PyImportMetaFinder))
    print(f"  py1: {py1}")
    print(f"  pyx1: {pyx1}")
    print(f"  PyImportMetaFinder count: {count_after_first}")
    
    with tempfile.TemporaryDirectory() as build_dir2:
        # Second install - pyimport again
        print("\nSecond install(pyximport=False, pyimport=True)...")
        py2, pyx2 = pyximport.install(
            pyximport=False,
            pyimport=True,
            build_dir=build_dir2
        )
        
        count_after_second = sum(1 for imp in sys.meta_path if isinstance(imp, pyx_module.PyImportMetaFinder))
        print(f"  py2: {py2}")
        print(f"  pyx2: {pyx2}")
        print(f"  PyImportMetaFinder count: {count_after_second}")
        
        if py2 is not None:
            print("\n❌ BUG FOUND: Second install of pyimport returned a new importer instead of None!")
            print("  According to _have_importers() check, it should return None if already installed")
        
        # Check if duplicate importers were added
        if count_after_second > 1:
            print(f"\n❌ BUG FOUND: Multiple PyImportMetaFinder instances in sys.meta_path: {count_after_second}")
            print("  Expected: max 1 instance")
        
        # Try to uninstall
        print("\nAttempting uninstall...")
        pyximport.uninstall(py1, pyx1)
        pyximport.uninstall(py2, pyx2)
        
        final_count = sum(1 for imp in sys.meta_path if isinstance(imp, pyx_module.PyImportMetaFinder))
        print(f"Final PyImportMetaFinder count after uninstall: {final_count}")
        
        if final_count > 0:
            print(f"\n❌ BUG FOUND: {final_count} PyImportMetaFinder instances remain after uninstall!")
            # Show which ones remain
            for i, imp in enumerate(sys.meta_path):
                if isinstance(imp, pyx_module.PyImportMetaFinder):
                    print(f"  - Position {i}: {imp}")