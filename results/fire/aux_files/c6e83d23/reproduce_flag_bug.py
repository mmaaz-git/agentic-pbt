#!/usr/bin/env python3
"""Minimal reproduction of the _IsFlag bug in fire.core"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire import core

# Test cases showing the bug
test_cases = [
    ('', 'empty string'),
    ('hello', 'regular word'),
    ('-a', 'single char flag'),
    ('--flag', 'multi char flag'),
    ('-', 'single hyphen'),
    ('123', 'number'),
]

print("Demonstrating inconsistent return types from _IsFlag functions:")
print("=" * 60)

for arg, description in test_cases:
    single_result = core._IsSingleCharFlag(arg)
    multi_result = core._IsMultiCharFlag(arg)
    flag_result = core._IsFlag(arg)
    
    print(f"\nInput: {arg!r} ({description})")
    print(f"  _IsSingleCharFlag: {single_result!r} (type: {type(single_result).__name__})")
    print(f"  _IsMultiCharFlag:  {multi_result!r} (type: {type(multi_result).__name__})")
    print(f"  _IsFlag:           {flag_result!r} (type: {type(flag_result).__name__})")
    
    # Show the problem with boolean comparisons
    if flag_result is not None and not isinstance(flag_result, bool):
        print(f"  PROBLEM: Returns {type(flag_result).__name__} instead of bool!")

print("\n" + "=" * 60)
print("Issue: Functions documented to determine if argument is a flag")
print("should return boolean, but return None or Match objects instead.")
print("\nThis violates the principle of least surprise and can cause")
print("subtle bugs in code that expects boolean return values.")