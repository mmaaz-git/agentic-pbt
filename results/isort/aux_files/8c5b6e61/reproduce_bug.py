#!/usr/bin/env python3
"""Minimal reproduction of the isort check-sort inconsistency bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')
import isort


def demonstrate_bug():
    """Demonstrate the check-sort inconsistency bug in isort."""
    
    # Minimal test case: code without trailing newline
    code_without_newline = "import a"
    
    print("Bug Reproduction: check_code says True but sort_code still modifies")
    print("=" * 60)
    print(f"Original code: {repr(code_without_newline)}")
    print(f"Length: {len(code_without_newline)} characters")
    
    # Check if code is already sorted
    is_sorted = isort.check_code(code_without_newline)
    print(f"\nisort.check_code() returns: {is_sorted}")
    print("This means isort claims the code is already properly sorted.")
    
    # Apply sorting
    sorted_code = isort.code(code_without_newline)
    print(f"\nAfter isort.code(): {repr(sorted_code)}")
    print(f"Length: {len(sorted_code)} characters")
    
    # Compare
    print(f"\nAre they equal? {code_without_newline == sorted_code}")
    
    if is_sorted and code_without_newline != sorted_code:
        print("\n🐛 BUG CONFIRMED!")
        print("check_code() returns True (claiming code is sorted)")
        print("but sort_code() still modifies the code!")
        print(f"Difference: sort_code() added a trailing newline")
        
        return True
    
    return False


def test_multiple_cases():
    """Test multiple cases to understand the pattern."""
    print("\n\nTesting multiple cases:")
    print("=" * 60)
    
    test_cases = [
        ("import a", "Single import without newline"),
        ("import a\n", "Single import with newline"),
        ("import a\nimport b", "Multiple imports without trailing newline"),
        ("import a\nimport b\n", "Multiple imports with trailing newline"),
        ("from x import y", "From import without newline"),
        ("import a  # comment", "Import with comment, no newline"),
    ]
    
    bugs_found = []
    
    for code, description in test_cases:
        print(f"\nCase: {description}")
        print(f"Code: {repr(code)}")
        
        is_sorted = isort.check_code(code)
        sorted_code = isort.code(code)
        
        if is_sorted and code != sorted_code:
            print(f"❌ BUG: check=True but code changed")
            print(f"  From: {repr(code)}")
            print(f"  To:   {repr(sorted_code)}")
            bugs_found.append((code, sorted_code, description))
        elif is_sorted and code == sorted_code:
            print(f"✓ OK: check=True and code unchanged")
        else:
            print(f"✓ OK: check=False (needs sorting)")
    
    return bugs_found


def main():
    print("isort Check-Sort Inconsistency Bug")
    print("=" * 60)
    
    # First demonstrate the basic bug
    bug_exists = demonstrate_bug()
    
    # Then test multiple cases
    bugs = test_multiple_cases()
    
    if bug_exists or bugs:
        print("\n\n" + "=" * 60)
        print("SUMMARY: Bug confirmed in isort")
        print("=" * 60)
        print("The bug: isort.check_code() can return True (indicating code is")
        print("properly sorted) while isort.code() still modifies the code by")
        print("adding a trailing newline. This violates the expected contract.")
        print("\nAffected cases:")
        for code, _, desc in bugs:
            print(f"  - {desc}: {repr(code)}")


if __name__ == "__main__":
    main()