#!/bin/bash
# Run inline Python tests for isort.sorting

/root/hypothesis-llm/envs/isort_env/bin/python3 -c '
import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")

from isort import sorting

# Test natural sorting
print("Testing natural sorting...")
test = ["file10", "file2", "file1"]
result = sorting.naturally(test)
print(f"Input: {test}")
print(f"Result: {result}")
print(f"Expected: [\"file1\", \"file2\", \"file10\"]")

# Check if it matches expected
expected = ["file1", "file2", "file10"]
if result == expected:
    print("✓ Natural sorting works correctly")
else:
    print("✗ BUG FOUND: Natural sorting incorrect!")
    print(f"  Got: {result}")
    print(f"  Expected: {expected}")
'