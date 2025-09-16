#!/usr/bin/env python3
"""Manual bug checking for isort.sorting - can be run to verify bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort import sorting
from isort.settings import Config

def check_bug_1():
    """Check if natural sorting handles numbers correctly."""
    print("=" * 60)
    print("BUG CHECK 1: Natural Sorting Numeric Ordering")
    print("=" * 60)
    
    # These should be sorted with numbers treated numerically
    test_cases = [
        (["file10", "file2", "file1"], ["file1", "file2", "file10"]),
        (["test100", "test20", "test3"], ["test3", "test20", "test100"]),
        (["a10b", "a2b", "a1b"], ["a1b", "a2b", "a10b"]),
        (["10", "2", "1"], ["1", "2", "10"]),
    ]
    
    bug_found = False
    for input_list, expected in test_cases:
        result = sorting.naturally(input_list)
        if result != expected:
            print(f"✗ BUG FOUND!")
            print(f"  Input:    {input_list}")
            print(f"  Expected: {expected}")
            print(f"  Got:      {result}")
            bug_found = True
        else:
            print(f"✓ Correct: {input_list} -> {result}")
    
    return bug_found

def check_bug_2():
    """Check if reverse parameter works correctly."""
    print("\n" + "=" * 60)
    print("BUG CHECK 2: Reverse Parameter")
    print("=" * 60)
    
    test = ["a1", "a10", "a2"]
    forward = sorting.naturally(test)
    backward = sorting.naturally(test, reverse=True)
    reversed_forward = list(reversed(forward))
    
    print(f"Input:            {test}")
    print(f"Forward sort:     {forward}")
    print(f"Backward sort:    {backward}")
    print(f"Reversed forward: {reversed_forward}")
    
    if backward != reversed_forward:
        print(f"✗ BUG FOUND! reverse=True doesn't match reversed forward sort")
        return True
    else:
        print(f"✓ Reverse parameter works correctly")
        return False

def check_bug_3():
    """Check _atoi with edge cases."""
    print("\n" + "=" * 60)
    print("BUG CHECK 3: _atoi Function")
    print("=" * 60)
    
    test_cases = [
        ("123", 123),
        ("0", 0),
        ("00123", 123),
        ("abc", "abc"),
        ("", ""),
        ("12a", "12a"),
    ]
    
    bug_found = False
    for input_str, expected in test_cases:
        result = sorting._atoi(input_str)
        if result != expected:
            print(f"✗ BUG FOUND!")
            print(f"  _atoi('{input_str}') = {result!r} (expected {expected!r})")
            bug_found = True
        else:
            print(f"✓ _atoi('{input_str}') = {result!r}")
    
    return bug_found

def check_bug_4():
    """Check empty list handling."""
    print("\n" + "=" * 60)
    print("BUG CHECK 4: Edge Cases")
    print("=" * 60)
    
    try:
        result = sorting.naturally([])
        print(f"✓ Empty list: [] -> {result}")
        
        result = sorting.naturally([""])
        print(f"✓ Single empty string: [''] -> {result}")
        
        result = sorting.naturally(["", "a", ""])
        print(f"✓ Mixed with empty: ['', 'a', ''] -> {result}")
        
        return False
    except Exception as e:
        print(f"✗ BUG FOUND! Exception on edge case: {e}")
        return True

def check_bug_5():
    """Check preservation of elements."""
    print("\n" + "=" * 60)
    print("BUG CHECK 5: Element Preservation")
    print("=" * 60)
    
    test_cases = [
        ["a", "b", "a", "c"],  # With duplicates
        ["x", "y", "z"],        # Simple case
        ["1", "1", "1"],        # All same
    ]
    
    bug_found = False
    for test in test_cases:
        result = sorting.naturally(test)
        if sorted(result) != sorted(test):
            print(f"✗ BUG FOUND! Elements not preserved")
            print(f"  Input:  {test}")
            print(f"  Output: {result}")
            bug_found = True
        else:
            print(f"✓ Elements preserved: {test} -> {result}")
    
    return bug_found

# Run all checks
if __name__ == "__main__":
    print("ISORT.SORTING BUG HUNT")
    print("=" * 60)
    
    bugs = []
    
    if check_bug_1():
        bugs.append("Natural sorting numeric ordering")
    if check_bug_2():
        bugs.append("Reverse parameter")
    if check_bug_3():
        bugs.append("_atoi function")
    if check_bug_4():
        bugs.append("Edge cases")
    if check_bug_5():
        bugs.append("Element preservation")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if bugs:
        print(f"Found {len(bugs)} potential bug(s):")
        for bug in bugs:
            print(f"  - {bug}")
    else:
        print("No bugs found in the tested properties.")
    
    print("\n" + "=" * 60)