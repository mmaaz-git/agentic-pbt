#!/usr/bin/env python3
"""Minimal reproduction of LazyDict deletion bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier._types import LazyDict

# Create a LazyDict with a lazy value
lazy_dict = LazyDict({'key': lambda: 'value'})

# Try to delete the key without accessing it first
# This should work but causes KeyError
try:
    del lazy_dict['key']
    print("Deletion succeeded")
except KeyError as e:
    print(f"BUG: KeyError when deleting uncomputed key: {e}")

# Also test: delete after accessing
lazy_dict2 = LazyDict({'key': lambda: 'value'})
_ = lazy_dict2['key']  # Access to compute
del lazy_dict2['key']  # This works
print("Deletion after access succeeded")

# Test edge case: delete non-existent key should raise KeyError
lazy_dict3 = LazyDict({'key': lambda: 'value'})
try:
    del lazy_dict3['nonexistent']
    print("BUG: Should have raised KeyError for non-existent key")
except KeyError:
    print("Correctly raised KeyError for non-existent key")