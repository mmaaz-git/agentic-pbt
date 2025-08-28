"""Demonstrate potential bugs in isort.sorting module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort import sorting
from isort.settings import Config

print("=" * 60)
print("POTENTIAL BUG IN module_key WITH LENGTH SORTING")
print("=" * 60)

# Create a config with length_sort enabled
config = Config(length_sort=True, force_to_top=[], case_sensitive=True)

# Test module names with different lengths
# If we have modules of length 9 and 10+, the sorting will be wrong
# because "9:" > "10:" lexicographically

module_names = [
    "a" * 9,   # Length 9: "aaaaaaaaa"
    "b" * 10,  # Length 10: "bbbbbbbbbb"  
    "c" * 8,   # Length 8: "cccccccc"
    "d" * 11,  # Length 11: "ddddddddddd"
    "e" * 100, # Length 100: "eee..." (100 e's)
]

print("\nModule names and their lengths:")
for name in module_names:
    print(f"  '{name[:20]}{'...' if len(name) > 20 else ''}' (length {len(name)})")

print("\nGenerated sort keys:")
keys = []
for name in module_names:
    key = sorting.module_key(name, config)
    keys.append(key)
    print(f"  module_key('{name[:20]}{'...' if len(name) > 20 else ''}') = '{key[:30]}{'...' if len(key) > 30 else ''}'")

print("\nSorting by these keys:")
sorted_indices = sorted(range(len(module_names)), key=lambda i: keys[i])
sorted_names = [module_names[i] for i in sorted_indices]

print("\nResult after sorting:")
for i, name in enumerate(sorted_names):
    print(f"  {i+1}. '{name[:20]}{'...' if len(name) > 20 else ''}' (length {len(name)})")

print("\nExpected order by length:")
expected = sorted(module_names, key=len)
for i, name in enumerate(expected):
    print(f"  {i+1}. '{name[:20]}{'...' if len(name) > 20 else ''}' (length {len(name)})")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("=" * 60)

# Check if the order matches
if sorted_names != expected:
    print("✗ BUG CONFIRMED!")
    print("  The length-based sorting is incorrect!")
    print("  Problem: String comparison of lengths fails for different digit counts")
    print("  Example: '9:' > '10:' lexicographically, but 9 < 10 numerically")
    print("\n  This happens because the length is converted to string and prepended,")
    print("  causing lexicographic comparison instead of numeric comparison.")
else:
    print("✓ No bug found in this test case")

# Additional check - more clear demonstration
print("\n" + "=" * 60)
print("CLEARER DEMONSTRATION OF THE BUG:")
print("=" * 60)

# Create modules that clearly show the issue
test_modules = ["x" * i for i in [9, 10, 99, 100]]
print("\nTest modules by length: 9, 10, 99, 100")

test_keys = [sorting.module_key(m, config) for m in test_modules]
sorted_test = sorted(test_modules, key=lambda m: sorting.module_key(m, config))

print("\nGenerated keys:")
for m, k in zip(test_modules, test_keys):
    print(f"  Length {len(m):3}: key = '{k}'")

print("\nAfter sorting:")
for i, m in enumerate(sorted_test):
    print(f"  Position {i}: length {len(m)}")

correct_order = [9, 10, 99, 100]
actual_order = [len(m) for m in sorted_test]

if actual_order != correct_order:
    print(f"\n✗ BUG CONFIRMED!")
    print(f"  Expected order: {correct_order}")
    print(f"  Actual order:   {actual_order}")
    print(f"\n  The bug occurs because lengths are compared as strings:")
    print(f"    '9:...' > '10:...' (string comparison)")
    print(f"    '99:...' > '100:...' (string comparison)")
else:
    print("\n✓ Modules sorted correctly by length")