#!/usr/bin/env python3
"""Investigate the bugs found in isort.api."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, example
from io import StringIO
import isort.api
from isort.api import check_code_string, sort_code_string, find_imports_in_code

print("Investigating bugs in isort.api...")
print("=" * 60)

# Bug 1: Check-sort consistency issue
print("\n1. CHECK-SORT CONSISTENCY BUG")
print("-" * 40)

def test_check_sort_empty():
    code = ""
    sorted_code = sort_code_string(code)
    is_already_sorted = check_code_string(code)
    
    print(f"Original code: {repr(code)}")
    print(f"Sorted code: {repr(sorted_code)}")
    print(f"check_code_string(original): {is_already_sorted}")
    print(f"Are they equal? {code == sorted_code}")
    
    if is_already_sorted and code != sorted_code:
        print("BUG CONFIRMED: check returns True but sort changes the code!")
        return False
    return True

test_check_sort_empty()

# Let's try with simple imports
print("\n" + "-" * 40)
code = "import a\nimport b"
sorted_code = sort_code_string(code)
is_sorted = check_code_string(code)
print(f"Code: {repr(code)}")
print(f"Sorted: {repr(sorted_code)}")
print(f"check_code_string: {is_sorted}")
print(f"Equal? {code == sorted_code}")

# Bug 2: Import preservation - duplicate imports
print("\n2. IMPORT PRESERVATION BUG")
print("-" * 40)

code_with_duplicates = "import a\nimport a"
print(f"Original code:\n{code_with_duplicates}")

imports_before = list(find_imports_in_code(code_with_duplicates))
print(f"Imports before sorting: {[imp.statement() for imp in imports_before]}")

sorted_code = sort_code_string(code_with_duplicates)
print(f"\nSorted code:\n{sorted_code}")

imports_after = list(find_imports_in_code(sorted_code))
print(f"Imports after sorting: {[imp.statement() for imp in imports_after]}")

if len(imports_before) != len(imports_after):
    print("BUG CONFIRMED: Duplicate imports are removed during sorting!")

# Bug 3: Show diff consistency
print("\n3. SHOW_DIFF CONSISTENCY BUG")
print("-" * 40)

test_code = ""
sorted_normal = sort_code_string(test_code)
diff_output = StringIO()
sorted_with_diff = sort_code_string(test_code, show_diff=diff_output)

print(f"Code: {repr(test_code)}")
print(f"Sorted normal: {repr(sorted_normal)}")
print(f"Sorted with diff: {repr(sorted_with_diff)}")
print(f"Diff output content: {repr(diff_output.getvalue())}")

if sorted_normal != sorted_with_diff:
    print("BUG CONFIRMED: show_diff parameter changes the sorting result!")

# Test with actual imports
test_code2 = "import b\nimport a"
sorted_normal2 = sort_code_string(test_code2)
diff_output2 = StringIO()
sorted_with_diff2 = sort_code_string(test_code2, show_diff=diff_output2)

print(f"\nCode with imports: {repr(test_code2)}")
print(f"Sorted normal: {repr(sorted_normal2)}")
print(f"Sorted with diff: {repr(sorted_with_diff2)}")
print(f"Equal? {sorted_normal2 == sorted_with_diff2}")

print("\n" + "=" * 60)