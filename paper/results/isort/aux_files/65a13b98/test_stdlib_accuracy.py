import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.stdlibs as stdlibs
import sys

# Try to import some of the supposedly removed modules to verify they're really gone
removed_modules = ['aifc', 'audioop', 'cgi', 'cgitb', 'chunk', 'crypt', 'imghdr', 
                  'lib2to3', 'mailcap', 'msilib', 'nis', 'nntplib', 'ossaudiodev', 
                  'pipes', 'sndhdr', 'spwd', 'sunau', 'telnetlib', 'uu', 'xdrlib']

print(f"Testing on Python {sys.version}")
print("-" * 50)

actually_missing = []
still_present = []

for module_name in removed_modules[:10]:  # Test first 10 to avoid too much output
    try:
        __import__(module_name)
        still_present.append(module_name)
        print(f"✗ {module_name}: Still importable (should be removed according to stdlibs)")
    except ModuleNotFoundError:
        actually_missing.append(module_name)
        print(f"✓ {module_name}: Not found (correctly marked as removed)")
    except Exception as e:
        print(f"? {module_name}: Import failed with {type(e).__name__}: {e}")

print("\nSummary:")
print(f"Correctly identified as removed: {len(actually_missing)}/{len(removed_modules[:10])}")
if still_present:
    print(f"ERROR: Modules marked as removed but still present: {still_present}")
    
# Test some modules that should still be present
core_modules = ['os', 'sys', 'math', 'json', 're']
print("\nTesting core modules that should be present:")
for module_name in core_modules:
    assert module_name in stdlibs.py313.stdlib, f"{module_name} missing from py313.stdlib"
    try:
        __import__(module_name)
        print(f"✓ {module_name}: Present and importable")
    except:
        print(f"✗ {module_name}: In stdlib list but not importable!")