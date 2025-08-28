#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort.comments import parse as parse_comments

# Test case that demonstrates the bug
line = "import something#\r"
import_part, comment = parse_comments(line)

print(f"Input line: {repr(line)}")
print(f"Parsed import: {repr(import_part)}")
print(f"Parsed comment: {repr(comment)}")
print()

# Expected vs actual
expected_comment = "\r"
actual_comment = comment

print(f"Expected comment: {repr(expected_comment)}")
print(f"Actual comment: {repr(actual_comment)}")
print(f"Bug confirmed: {expected_comment != actual_comment}")
print()

# The issue is that parse_comments strips whitespace from comments
# This violates the round-trip property: we can't reconstruct the original line
if expected_comment != actual_comment:
    print("BUG: parse_comments strips whitespace from comments, losing information")