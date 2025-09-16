#!/usr/bin/env python3
"""Focused test to investigate potential bug in urlencode."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid import encode

# Test the specific case where None value might cause prefix bug
def test_urlencode_none_first():
    """Test urlencode with None as first value."""
    data = [('a', None), ('b', 'value')]
    result = encode.urlencode(data)
    print(f"Test 1 - [('a', None), ('b', 'value')]: {result!r}")
    # Expected: 'a=&b=value' 
    # Potential bug: 'a=b=value' (missing &)
    
def test_urlencode_none_middle():
    """Test urlencode with None in middle."""
    data = [('a', 'val1'), ('b', None), ('c', 'val2')]
    result = encode.urlencode(data)
    print(f"Test 2 - [('a', 'val1'), ('b', None), ('c', 'val2')]: {result!r}")
    # Expected: 'a=val1&b=&c=val2'
    # Potential bug: 'a=val1&b=c=val2' (missing & after b=)
    
def test_urlencode_only_none():
    """Test urlencode with only None values."""
    data = [('a', None), ('b', None)]
    result = encode.urlencode(data)
    print(f"Test 3 - [('a', None), ('b', None)]: {result!r}")
    # Expected: 'a=&b='
    # Potential bug: 'a=b=' (missing &)

def test_urlencode_none_with_list():
    """Test urlencode with None followed by list value."""
    data = [('a', None), ('b', ['x', 'y'])]
    result = encode.urlencode(data)
    print(f"Test 4 - [('a', None), ('b', ['x', 'y'])]: {result!r}")
    # Expected: 'a=&b=x&b=y'
    # Potential bug: 'a=b=x&b=y' (missing & after a=)

def test_urlencode_none_empty_string():
    """Compare None vs empty string behavior."""
    data_none = [('a', None)]
    data_empty = [('a', '')]
    result_none = encode.urlencode(data_none)
    result_empty = encode.urlencode(data_empty)
    print(f"Test 5 - None value: {result_none!r}")
    print(f"Test 5 - Empty string: {result_empty!r}")
    # None should produce 'a=' 
    # Empty string should produce 'a='
    # They should be the same!

if __name__ == '__main__':
    test_urlencode_none_first()
    test_urlencode_none_middle()
    test_urlencode_only_none()
    test_urlencode_none_with_list()
    test_urlencode_none_empty_string()
    
    # Let's also trace through the logic manually
    print("\n--- Manual trace of the bug ---")
    data = [('a', None), ('b', 'value')]
    print(f"Input: {data}")
    print("Expected output: 'a=&b=value'")
    
    result = encode.urlencode(data)
    print(f"Actual output: {result!r}")
    
    if result == 'a=b=value':
        print("BUG CONFIRMED: Missing '&' after None value!")