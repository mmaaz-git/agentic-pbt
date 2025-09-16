#!/usr/bin/env python3
"""Investigate the issues found in property-based testing."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')
import isort


def test_check_sort_consistency():
    """Investigate the check-sort consistency issue."""
    code1 = """import a

# Some code
print('hello')"""
    
    print("Test 1: Check-Sort Consistency")
    print(f"Original code:\n{repr(code1)}")
    is_sorted = isort.check_code(code1)
    print(f"check_code result: {is_sorted}")
    
    sorted_code = isort.code(code1)
    print(f"Sorted code:\n{repr(sorted_code)}")
    print(f"Are they equal? {code1 == sorted_code}")
    print(f"Difference in bytes: {code1.encode() != sorted_code.encode()}")
    
    # Check byte-by-byte difference
    if code1 != sorted_code:
        for i, (c1, c2) in enumerate(zip(code1, sorted_code)):
            if c1 != c2:
                print(f"First difference at position {i}: {repr(c1)} vs {repr(c2)}")
                break
        if len(code1) != len(sorted_code):
            print(f"Length difference: {len(code1)} vs {len(sorted_code)}")
    
    print("\n" + "="*50 + "\n")


def test_import_order_change():
    """Test the import order preservation issue."""
    code2 = """from a import b, a

# Some code
print('hello')"""
    
    print("Test 2: Import Order Change")
    print(f"Original code:\n{code2}")
    
    sorted_code = isort.code(code2)
    print(f"Sorted code:\n{sorted_code}")
    
    # This is actually correct behavior - isort alphabetizes imports
    # But my test was incorrectly flagging this as losing imports
    print("\nNote: isort correctly alphabetizes imports within the same line")
    print("from a import b, a -> from a import a, b")
    
    print("\n" + "="*50 + "\n")


def test_edge_case_imports():
    """Test some edge cases with imports."""
    
    test_cases = [
        # Duplicate imports
        "from a import b\nfrom a import b",
        # Import with trailing comma
        "from a import b,",
        # Star imports
        "from a import *",
        # Relative imports
        "from . import a",
        "from .. import b",
        # Mixed absolute and relative
        "import a\nfrom . import b",
    ]
    
    print("Test 3: Edge Cases")
    for i, code in enumerate(test_cases, 1):
        print(f"\nCase {i}:")
        print(f"Original:\n{code}")
        try:
            sorted_code = isort.code(code)
            print(f"Sorted:\n{sorted_code}")
            if code != sorted_code:
                print("^ Changed!")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "="*50 + "\n")


def test_whitespace_sensitivity():
    """Test whitespace handling in check vs sort."""
    codes = [
        "import a\n\n# Comment",
        "import a\n# Comment",  
        "import a  # inline comment",
        "import   a",  # Multiple spaces
        "import a\n",  # Trailing newline
        "import a",  # No trailing newline
    ]
    
    print("Test 4: Whitespace Sensitivity")
    for code in codes:
        print(f"\nCode: {repr(code)}")
        is_sorted = isort.check_code(code)
        sorted_code = isort.code(code)
        if is_sorted and code != sorted_code:
            print(f"BUG: check_code=True but code changed!")
            print(f"Original: {repr(code)}")
            print(f"Sorted:   {repr(sorted_code)}")
    
    print("\n" + "="*50 + "\n")


def test_minimal_reproduction():
    """Find minimal reproduction case for check-sort inconsistency."""
    print("Test 5: Minimal Reproduction")
    
    # Simplest case
    code = "import a"
    print(f"Testing: {repr(code)}")
    is_sorted = isort.check_code(code)
    sorted_code = isort.code(code)
    print(f"check_code: {is_sorted}")
    print(f"Original: {repr(code)}")
    print(f"Sorted:   {repr(sorted_code)}")
    print(f"Equal? {code == sorted_code}")
    
    if not code == sorted_code and is_sorted:
        print("FOUND BUG: Minimal case where check_code=True but sort changes code")


if __name__ == "__main__":
    test_check_sort_consistency()
    test_import_order_change()
    test_edge_case_imports()
    test_whitespace_sensitivity()
    test_minimal_reproduction()