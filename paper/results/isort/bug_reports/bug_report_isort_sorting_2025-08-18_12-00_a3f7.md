# Bug Report: isort.sorting Length Sort Lexicographic Comparison Bug

**Target**: `isort.sorting.module_key` and `isort.sorting.section_key`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `module_key` and `section_key` functions incorrectly handle length-based sorting by prepending unpadded numeric lengths as strings, causing lexicographic instead of numeric comparison.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from isort import sorting
from isort.settings import Config

@given(
    lengths=st.lists(st.integers(min_value=1, max_value=200), min_size=2, unique=True)
)
def test_module_key_length_sort(lengths):
    """module_key with length_sort should sort by numeric length, not lexicographically."""
    config = Config(length_sort=True)
    
    # Create module names with specified lengths
    modules = ["m" * length for length in lengths]
    
    # Sort using module_key
    sorted_modules = sorted(modules, key=lambda m: sorting.module_key(m, config))
    sorted_lengths = [len(m) for m in sorted_modules]
    
    # Should be sorted by length numerically
    assert sorted_lengths == sorted(lengths), f"Length sort failed: {sorted_lengths} != {sorted(lengths)}"
```

**Failing input**: `lengths=[9, 10]`

## Reproducing the Bug

```python
from isort import sorting
from isort.settings import Config

config = Config(length_sort=True)

modules = ["m" * 9, "n" * 10]
keys = [sorting.module_key(m, config) for m in modules]

print(f"Module of length 9:  key = '{keys[0]}'")
print(f"Module of length 10: key = '{keys[1]}'")

sorted_modules = sorted(modules, key=lambda m: sorting.module_key(m, config))
sorted_lengths = [len(m) for m in sorted_modules]

print(f"\nExpected order: [9, 10]")
print(f"Actual order:   {sorted_lengths}")

assert sorted_lengths == [9, 10], "Bug: Modules not sorted correctly by length"
```

## Why This Is A Bug

The functions prepend the length as an unpadded string (e.g., "9:" and "10:"). During lexicographic comparison, "9:" > "10:" because the character '9' > '1', causing modules of length 9 to incorrectly sort after modules of length 10. This violates the expected behavior of length-based sorting.

## Fix

```diff
--- a/isort/sorting.py
+++ b/isort/sorting.py
@@ -50,7 +50,7 @@ def module_key(
         or (config.length_sort_straight and straight_import)
         or str(section_name).lower() in config.length_sort_sections
     )
-    _length_sort_maybe = (str(len(module_name)) + ":" + module_name) if length_sort else module_name
+    _length_sort_maybe = (f"{len(module_name):09d}:{module_name}") if length_sort else module_name
     return f"{(module_name in config.force_to_top and 'A') or 'B'}{prefix}{_length_sort_maybe}"
 
 
@@ -96,5 +96,5 @@ def section_key(line: str, config: Config) -> str:
     elif not config.order_by_type:
         line = line.lower()
 
-    return f"{section}{len(line) if config.length_sort else ''}{line}"
+    return f"{section}{f'{len(line):09d}' if config.length_sort else ''}{line}"
```