#!/usr/bin/env python3
"""Reproduce the newline consistency bug in isort.api."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort.api import check_code_string, sort_code_string

# Test case 1: Code without trailing newline
code = "import a\nimport b"
print(f"Original code (no trailing newline):")
print(repr(code))

# Check if it's already sorted
is_sorted = check_code_string(code)
print(f"\ncheck_code_string returns: {is_sorted}")

# Sort the code
sorted_code = sort_code_string(code)
print(f"\nSorted code:")
print(repr(sorted_code))

# The bug: check says it's sorted, but sort still changes it
if is_sorted and code != sorted_code:
    print("\nBUG: check_code_string claims the code is sorted,")
    print("     but sort_code_string still modifies it by adding a newline!")
    print(f"\nDifference: sort adds trailing newline")
    print(f"Original ends with: {repr(code[-5:] if len(code) >= 5 else code)}")
    print(f"Sorted ends with:   {repr(sorted_code[-5:] if len(sorted_code) >= 5 else sorted_code)}")