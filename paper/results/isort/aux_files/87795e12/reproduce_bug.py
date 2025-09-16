#!/usr/bin/env python3
"""Minimal reproduction of the length_sort bug in isort.sorting.module_key"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort import sorting
from isort.settings import Config

# Create config with length_sort enabled
config = Config(length_sort=True)

# Create module names of different lengths
# Lengths 9 and 10 will demonstrate the bug
modules = [
    "m" * 9,   # 9 characters
    "n" * 10,  # 10 characters
]

# Get the sort keys
keys = [sorting.module_key(m, config) for m in modules]

print("Module lengths:", [len(m) for m in modules])
print("Generated keys:", keys)

# Sort using the keys
sorted_modules = sorted(modules, key=lambda m: sorting.module_key(m, config))
sorted_lengths = [len(m) for m in sorted_modules]

print("Sorted order (by length):", sorted_lengths)

# Check if sorted correctly by length
if sorted_lengths != [9, 10]:
    print("\nBUG: Modules are not sorted correctly by length!")
    print(f"Expected: [9, 10]")
    print(f"Got:      {sorted_lengths}")
    print("\nReason: The module_key function prepends length as a string (e.g., '9:' and '10:'),")
    print("        causing lexicographic comparison where '9:' > '10:'")
else:
    print("\nNo bug found")