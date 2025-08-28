#!/usr/bin/env python3
"""Minimal reproduction of carriage return handling bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

from fixit.engine import LintRunner
from pathlib import Path

def test_carriage_return_preservation():
    """
    Test that carriage return (\r) is preserved when applying empty replacements.
    
    Expected: apply_replacements with empty list should preserve original content
    Actual: \r is converted to empty string
    """
    
    # Test case 1: Standalone carriage return
    cr_content = b'\r'
    runner = LintRunner(path=Path("test.py"), source=cr_content)
    result = runner.apply_replacements([])
    
    print(f"Input: {repr(cr_content.decode('utf-8'))}")
    print(f"Output: {repr(result.code)}")
    print(f"Expected: '\\r'")
    print(f"Bug: Input '\\r' becomes '' (empty string)")
    print()
    
    # Test case 2: Code with carriage return
    cr_code = b'x = 1\ry = 2'
    runner2 = LintRunner(path=Path("test.py"), source=cr_code)
    result2 = runner2.apply_replacements([])
    
    print(f"Input with code: {repr(cr_code.decode('utf-8'))}")
    print(f"Output: {repr(result2.code)}")
    print(f"Note: \\r in middle of code is lost")
    
    return result.code != '\r'  # Returns True if bug exists

if __name__ == "__main__":
    has_bug = test_carriage_return_preservation()
    if has_bug:
        print("\n✗ BUG CONFIRMED: Carriage return not preserved")
    else:
        print("\n✓ No bug found")