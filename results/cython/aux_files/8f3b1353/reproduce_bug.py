import sys
import pyximport.pyximport as pyx

# Save initial state
initial_meta_path = sys.meta_path.copy()
print(f"Initial meta_path count: {len(initial_meta_path)}")

# First install with pyimport=True
print("\nFirst install(pyimport=True)...")
py_imp1, pyx_imp1 = pyx.install(pyximport=False, pyimport=True)
print(f"Returned py_importer: {py_imp1}")

# Count PyImportMetaFinder instances
py_count1 = sum(1 for imp in sys.meta_path if type(imp).__name__ == 'PyImportMetaFinder')
print(f"PyImportMetaFinder count after first install: {py_count1}")

# Second install with same parameters
print("\nSecond install(pyimport=True)...")
py_imp2, pyx_imp2 = pyx.install(pyximport=False, pyimport=True)
print(f"Returned py_importer: {py_imp2}")

# Count PyImportMetaFinder instances again
py_count2 = sum(1 for imp in sys.meta_path if type(imp).__name__ == 'PyImportMetaFinder')
print(f"PyImportMetaFinder count after second install: {py_count2}")

# Show the problem
print(f"\nBUG: Expected 1 PyImportMetaFinder, but got {py_count2}")
print("The second install should have returned None and not added a duplicate!")

# Show all PyImportMetaFinder instances
print("\nAll PyImportMetaFinder instances in sys.meta_path:")
for i, imp in enumerate(sys.meta_path):
    if type(imp).__name__ == 'PyImportMetaFinder':
        print(f"  Index {i}: {imp}")