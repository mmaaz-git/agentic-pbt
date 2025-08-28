#!/usr/bin/env python3
"""Test demonstrating inconsistency in PurePath.with_name() validation."""

from pathlib import PurePath
import pytest


def test_with_name_special_directory_inconsistency():
    """Demonstrate that with_name treats '.' and '..' inconsistently."""
    base = PurePath("dir/file.txt")
    
    # '.' is rejected (correct behavior)
    with pytest.raises(ValueError, match="Invalid name"):
        base.with_name(".")
    
    # '..' should also be rejected but isn't (BUG)
    # This should raise ValueError but doesn't
    result = base.with_name("..")
    assert result == PurePath("dir/..")
    
    # This creates semantic confusion:
    # - 'dir/..' means "parent of dir" in filesystem terms
    # - But with_name("..") suggests "replace filename with .."
    # - Since '.' is rejected for being special, '..' should be too


def test_with_name_validation_patterns():
    """Show the validation pattern and where it breaks."""
    base = PurePath("folder/document.pdf")
    
    test_cases = [
        ("", ValueError),           # Empty - rejected
        (".", ValueError),          # Current dir - rejected  
        ("..", None),              # Parent dir - NOT rejected (inconsistent!)
        ("/", ValueError),          # Path separator - rejected
        ("//", ValueError),         # Double separator - rejected
        ("a/b", ValueError),        # Contains separator - rejected
        ("...", None),             # Three dots - accepted (OK, not special)
        (".hidden", None),         # Hidden file - accepted (OK)
        ("regular", None),         # Regular name - accepted (OK)
    ]
    
    for name, expected in test_cases:
        if expected is ValueError:
            with pytest.raises(ValueError):
                base.with_name(name)
        else:
            result = base.with_name(name)
            assert result.name == name


if __name__ == "__main__":
    # Run the tests
    test_with_name_special_directory_inconsistency()
    print("✓ Confirmed: '..' is inconsistently accepted by with_name()")
    
    test_with_name_validation_patterns()
    print("✓ Validation pattern confirmed")
    
    print("\nBUG SUMMARY:")
    print("PurePath.with_name() rejects '.' but accepts '..'")
    print("Both are special directory names and should be treated consistently")