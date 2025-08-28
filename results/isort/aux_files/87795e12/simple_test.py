#!/usr/bin/env python3
"""Simple test runner for isort.sorting bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort import sorting
from isort.settings import Config

# Test 1: Check natural sorting with specific examples
print("Test 1: Natural sorting numeric ordering")
test_cases = [
    ["file10", "file2", "file1"],
    ["item100", "item20", "item3"],
    ["test9", "test10", "test11", "test1", "test2"],
    ["a10b", "a2b", "a1b"],
]

for test in test_cases:
    result = sorting.naturally(test)
    print(f"  Input:  {test}")
    print(f"  Output: {result}")
    
    # Check if numeric parts are sorted correctly
    # For file10, file2, file1 -> should be file1, file2, file10
    # But standard sort would give file1, file10, file2
    
# Test 2: Check reverse parameter
print("\nTest 2: Reverse parameter")
test = ["a1", "a10", "a2", "a20", "a3"]
forward = sorting.naturally(test)
backward = sorting.naturally(test, reverse=True)
print(f"  Forward:  {forward}")
print(f"  Backward: {backward}")
print(f"  Reversed forward: {list(reversed(forward))}")
print(f"  Match: {list(reversed(forward)) == backward}")

# Test 3: Check _atoi
print("\nTest 3: _atoi function")
test_inputs = ["123", "abc", "12a", "", "0", "00123"]
for inp in test_inputs:
    result = sorting._atoi(inp)
    expected = int(inp) if inp.isdigit() else inp
    match = result == expected
    print(f"  _atoi('{inp}') = {result!r} (expected {expected!r}) {'✓' if match else '✗'}")

# Test 4: Check _natural_keys
print("\nTest 4: _natural_keys function")
test_inputs = ["abc123def456", "test", "123", "a1b2c3", ""]
for inp in test_inputs:
    result = sorting._natural_keys(inp)
    print(f"  _natural_keys('{inp}') = {result}")

# Test 5: Check module_key with case sensitivity
print("\nTest 5: module_key case sensitivity")
config_case_sensitive = Config(case_sensitive=True)
config_case_insensitive = Config(case_sensitive=False)

test_modules = ["MyModule", "mymodule", "MYMODULE"]
print("  With case_sensitive=True:")
for mod in test_modules:
    key = sorting.module_key(mod, config_case_sensitive, ignore_case=False)
    print(f"    module_key('{mod}') = '{key}'")

print("  With case_sensitive=False (and ignore_case=True):")
for mod in test_modules:
    key = sorting.module_key(mod, config_case_insensitive, ignore_case=True)
    print(f"    module_key('{mod}') = '{key}'")

# Test 6: Edge cases
print("\nTest 6: Edge cases")
edge_cases = [
    [],
    [""],
    ["", "a", ""],
    ["1", "2", "10", "20"],
]

for test in edge_cases:
    try:
        result = sorting.naturally(test)
        print(f"  naturally({test!r}) = {result!r}")
    except Exception as e:
        print(f"  naturally({test!r}) raised {type(e).__name__}: {e}")

print("\n" + "="*50)
print("Manual testing complete - reviewing for potential bugs...")