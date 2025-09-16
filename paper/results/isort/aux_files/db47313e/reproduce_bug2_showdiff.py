#!/usr/bin/env python3
"""Reproduce the show_diff bug in isort.api."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from io import StringIO
from isort.api import sort_code_string

# Code that needs sorting
code = "import b\nimport a"
print(f"Original code:")
print(code)

# Sort normally
sorted_normal = sort_code_string(code)
print(f"\nSorted normally:")
print(sorted_normal)

# Sort with show_diff=True
diff_output = StringIO()
sorted_with_diff = sort_code_string(code, show_diff=diff_output)
print(f"\nSorted with show_diff=True:")
print(repr(sorted_with_diff))

print(f"\nDiff output:")
print(diff_output.getvalue())

# The bug
if sorted_normal != sorted_with_diff:
    print("\nBUG: sort_code_string returns different results")
    print(f"     Normal sorting: {repr(sorted_normal)}")
    print(f"     With show_diff: {repr(sorted_with_diff)}")
    print("\nWhen show_diff is enabled, the function returns an empty string!")