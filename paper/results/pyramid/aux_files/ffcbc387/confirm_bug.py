#!/usr/bin/env python3
"""Confirm the documentation bug in urlencode."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid import encode

# Test to confirm the documentation bug
def confirm_none_handling_bug():
    """
    According to the docstring (line 50-51 of encode.py):
    "In a key/value pair, if the value is ``None`` then it will be
    dropped from the resulting output."
    
    This would mean that {'key': None} should produce an empty string,
    and {'a': None, 'b': 'value'} should produce 'b=value'.
    
    But the actual implementation produces 'key=' and 'a=&b=value'.
    """
    
    print("=== DOCUMENTATION BUG IN pyramid.encode.urlencode ===\n")
    
    print("Docstring states (lines 50-51):")
    print('  "In a key/value pair, if the value is ``None`` then it will be')
    print('  dropped from the resulting output."')
    print()
    
    test_cases = [
        ({'key': None}, 'Empty string (key-value pair dropped)', ''),
        ({'a': None, 'b': 'value'}, 'Just "b=value" (a dropped)', 'b=value'),
        ({'a': 'value', 'b': None}, 'Just "a=value" (b dropped)', 'a=value'),
        ([('a', None), ('b', None)], 'Empty string (both dropped)', ''),
    ]
    
    for data, description, expected_per_docs in test_cases:
        actual = encode.urlencode(data)
        print(f"Input: {data}")
        print(f"Expected per docs ({description}): {expected_per_docs!r}")
        print(f"Actual output: {actual!r}")
        
        if actual != expected_per_docs:
            print("  ❌ MISMATCH - Documentation is incorrect!")
        else:
            print("  ✓ Match")
        print()
    
    print("CONCLUSION: The documentation is incorrect. None values are NOT dropped.")
    print("Instead, they produce 'key=' in the output (empty value, not dropped key).")
    print("\nThis is a CONTRACT violation between documentation and implementation.")

if __name__ == '__main__':
    confirm_none_handling_bug()