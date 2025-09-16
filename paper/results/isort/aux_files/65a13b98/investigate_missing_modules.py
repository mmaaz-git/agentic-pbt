import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.stdlibs as stdlibs

# Find modules that are in py312 but not in py313
removed_modules = stdlibs.py312.stdlib - stdlibs.py313.stdlib
added_modules = stdlibs.py313.stdlib - stdlibs.py312.stdlib

print(f"Modules in Python 3.12 but not in Python 3.13: {len(removed_modules)}")
print("Removed modules:", sorted(removed_modules))
print()
print(f"Modules in Python 3.13 but not in Python 3.12: {len(added_modules)}")
print("Added modules:", sorted(added_modules))
print()
print(f"Python 3.12 has {len(stdlibs.py312.stdlib)} modules")
print(f"Python 3.13 has {len(stdlibs.py313.stdlib)} modules")
print(f"Common modules: {len(stdlibs.py312.stdlib & stdlibs.py313.stdlib)}")
print(f"Percentage retained: {100 * len(stdlibs.py312.stdlib & stdlibs.py313.stdlib) / len(stdlibs.py312.stdlib):.1f}%")