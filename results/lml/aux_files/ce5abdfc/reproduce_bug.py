#!/usr/bin/env python3
"""Minimal reproduction of the split/join round-trip bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/worker_/14')

from lml_loader import DataLoader

def reproduce_bug():
    loader = DataLoader()
    
    # Test case 1: Empty list
    items = []
    delimiter = ','
    
    joined = loader.join_with_delimiter(items, delimiter)
    print(f"Original items: {items}")
    print(f"After join: '{joined}'")
    
    split = loader.split_by_delimiter(joined, delimiter)
    print(f"After split: {split}")
    print(f"Expected: {items}")
    print(f"Bug confirmed: {split != items}")
    print()
    
    # This demonstrates the issue: 
    # ''.split(',') returns [''] in Python, not []
    print("Python behavior:")
    print(f"''.split(',') = {''.split(',')}")
    print(f"Expected for round-trip: []")
    
    return split != items

if __name__ == "__main__":
    bug_found = reproduce_bug()
    if bug_found:
        print("\n✗ Bug reproduced: split/join round-trip fails for empty lists")
        sys.exit(1)
    else:
        print("\n✓ No bug found")
        sys.exit(0)