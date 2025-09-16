#!/usr/bin/env python3
"""Focused bug hunting in pyramid.router."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import traceback
from urllib.parse import quote, unquote

from pyramid.traversal import (
    traversal_path_info,
    traversal_path,
    split_path_info,
    decode_path_info,
    _join_path_tuple,
    quote_path_segment,
    unquote_bytes_to_wsgi
)
from pyramid.encode import url_quote
from pyramid.urldispatch import _compile_route

print("Bug hunting in pyramid.router")
print("="*60)

# Bug Hunt 1: Unicode handling in path functions
print("\n1. Looking for Unicode bugs in path handling...")

@given(st.text(min_size=1, max_size=50))
@settings(max_examples=200)
def test_unicode_path_roundtrip(text):
    """Test if Unicode paths can round-trip properly."""
    assume('\x00' not in text)  # Null bytes not allowed
    assume('/' not in text)  # Testing single segments
    
    try:
        # Quote the segment
        quoted = quote_path_segment(text)
        
        # Build a path tuple and join it
        path_tuple = ('', quoted)
        joined = _join_path_tuple(path_tuple)
        
        # The joined path should contain the quoted version
        assert quoted in joined, f"Quoted '{quoted}' not in joined '{joined}'"
        
    except Exception as e:
        print(f"\n  BUG FOUND with input '{text}':")
        print(f"    Error: {e}")
        traceback.print_exc()
        return

try:
    test_unicode_path_roundtrip()
    print("  ✓ No bugs found in Unicode path handling")
except Exception as e:
    print(f"  ✗ Bug found: {e}")

# Bug Hunt 2: Route pattern edge cases
print("\n2. Looking for bugs in route pattern compilation...")

@given(st.text(min_size=0, max_size=100))
@settings(max_examples=200)
def test_route_pattern_bugs(pattern):
    """Look for crashes or incorrect behavior in route compilation."""
    try:
        # Try to compile any pattern
        match, generate = _compile_route(pattern)
        
        # Try to match against itself (with leading slash)
        if not pattern.startswith('/'):
            test_path = '/' + pattern
        else:
            test_path = pattern
            
        # Remove any regex/placeholder stuff for basic test
        if '{' not in test_path and ':' not in test_path and '*' not in test_path:
            result = match(test_path)
            # Static patterns should match themselves
            if all(c.isalnum() or c in '/_-.' for c in test_path):
                if result is None:
                    print(f"\n  POTENTIAL BUG: Pattern '{pattern}' doesn't match '{test_path}'")
                    
    except UnicodeDecodeError as e:
        print(f"\n  BUG FOUND - UnicodeDecodeError with pattern '{pattern}':")
        print(f"    {e}")
        return
    except ValueError as e:
        # This is expected for some invalid patterns
        if "must be either a Unicode string" not in str(e):
            print(f"\n  Unexpected ValueError with pattern '{pattern}': {e}")
    except Exception as e:
        print(f"\n  BUG FOUND with pattern '{pattern}':")
        print(f"    {type(e).__name__}: {e}")
        return

try:
    test_route_pattern_bugs()
    print("  ✓ No bugs found in route pattern compilation")
except Exception as e:
    print(f"  ✗ Bug found: {e}")

# Bug Hunt 3: Path traversal beyond root
print("\n3. Testing path traversal beyond root edge cases...")

def test_beyond_root():
    """Test what happens when we go beyond root with '..'"""
    
    # These should all normalize to the same thing
    paths = [
        "/../foo",
        "/../../foo", 
        "/../../../foo",
        "/../../../../foo",
        "/../../../../../../../../../foo",
    ]
    
    results = []
    for path in paths:
        result = traversal_path_info(path)
        results.append(result)
        
    # All should give the same result
    if not all(r == results[0] for r in results):
        print(f"  BUG: Inconsistent results for parent refs beyond root:")
        for path, result in zip(paths, results):
            print(f"    {path} -> {result}")
        return False
    
    # Should be ('foo',)
    if results[0] != ('foo',):
        print(f"  BUG: Expected ('foo',) but got {results[0]}")
        return False
        
    return True

if test_beyond_root():
    print("  ✓ Parent refs beyond root handled consistently")
else:
    print("  ✗ Bug found in parent ref handling")

# Bug Hunt 4: Empty path segments
print("\n4. Testing empty path segment handling...")

def test_empty_segments():
    """Test handling of multiple consecutive slashes."""
    
    test_cases = [
        ("//", ()),
        ("///", ()),
        ("////", ()),
        ("/foo//bar", ('foo', 'bar')),
        ("/foo///bar", ('foo', 'bar')),
        ("//foo//bar//", ('foo', 'bar')),
    ]
    
    for path, expected in test_cases:
        result = traversal_path_info(path)
        if result != expected:
            print(f"  BUG: Path '{path}' gave {result}, expected {expected}")
            return False
            
    return True

if test_empty_segments():
    print("  ✓ Empty segments handled correctly")
else:
    print("  ✗ Bug found in empty segment handling")

# Bug Hunt 5: Mixed special segments
print("\n5. Testing mixed special segments...")

def test_mixed_special():
    """Test paths with mixed '.', '..', and regular segments."""
    
    test_cases = [
        ("/./foo", ('foo',)),
        ("/foo/.", ('foo',)),
        ("/foo/./bar", ('foo', 'bar')),
        ("/foo/../bar", ('bar',)),
        ("/foo/./../bar", ('bar',)),
        ("/./foo/../bar/.", ('bar',)),
        ("/foo/bar/../../baz", ('baz',)),
    ]
    
    for path, expected in test_cases:
        result = traversal_path_info(path)
        if result != expected:
            print(f"  BUG: Path '{path}' gave {result}, expected {expected}")
            return False
            
    return True

if test_mixed_special():
    print("  ✓ Mixed special segments handled correctly")
else:
    print("  ✗ Bug found in special segment handling")

# Bug Hunt 6: Testing decode_path_info
print("\n6. Testing decode_path_info with encoded characters...")

def test_decode_path():
    """Test decode_path_info with various encodings."""
    
    test_cases = [
        "/hello%20world",  # Space
        "/caf%C3%A9",  # café in UTF-8
        "/%2E%2E/foo",  # Encoded ../foo
        "/test%2Fslash",  # Encoded slash
        "/%00null",  # Null byte (might fail)
    ]
    
    for path in test_cases:
        try:
            # First encode as bytes (Latin-1 as per WSGI)
            path_bytes = path.encode('latin-1')
            result = decode_path_info(path_bytes)
            print(f"  {path} -> '{result}'")
        except Exception as e:
            print(f"  {path} -> ERROR: {type(e).__name__}: {e}")

test_decode_path()

# Bug Hunt 7: Route generation issues
print("\n7. Testing route generation...")

@given(st.dictionaries(
    st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnop'),
    st.text(min_size=1, max_size=20),
    min_size=1,
    max_size=5
))
@settings(max_examples=100)
def test_route_generation(params):
    """Test route pattern generation with parameters."""
    
    # Build a pattern with placeholders
    pattern_parts = ['/base']
    for key in params.keys():
        pattern_parts.append(f'/{{{key}}}')
    pattern = ''.join(pattern_parts)
    
    try:
        match, generate = _compile_route(pattern)
        
        # Generate URL with parameters
        generated = generate(params)
        
        # The generated URL should match the pattern
        match_result = match(generated)
        
        if match_result is None:
            print(f"\n  BUG: Generated URL doesn't match its own pattern")
            print(f"    Pattern: {pattern}")
            print(f"    Params: {params}")
            print(f"    Generated: {generated}")
            return
            
        # Check all params are preserved
        for key, value in params.items():
            if key not in match_result or match_result[key] != value:
                print(f"\n  BUG: Parameter {key}={value} not preserved")
                print(f"    Got: {match_result}")
                return
                
    except Exception as e:
        print(f"\n  BUG in route generation:")
        print(f"    Pattern: {pattern}")
        print(f"    Params: {params}")
        print(f"    Error: {e}")
        return

try:
    test_route_generation()
    print("  ✓ Route generation works correctly")
except Exception as e:
    print(f"  ✗ Bug found: {e}")

print("\n" + "="*60)
print("Bug hunting complete!")
print("="*60)