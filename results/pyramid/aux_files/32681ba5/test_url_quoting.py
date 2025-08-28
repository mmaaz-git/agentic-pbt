#!/usr/bin/env python3
"""Test URL quoting behavior in pyramid for potential bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.traversal import quote_path_segment, _join_path_tuple
from pyramid.encode import url_quote
from pyramid.urldispatch import _compile_route
from urllib.parse import quote, unquote

print("Testing URL quoting behavior in pyramid")
print("="*60)

# Test 1: Special characters in path segments
print("\n1. Testing special characters in quote_path_segment...")

special_cases = [
    # (input, description)
    ("hello world", "space"),
    ("hello%20world", "already encoded space"),
    ("test/slash", "forward slash"),
    ("test%2Fslash", "encoded slash"),
    ("../parent", "parent reference"),
    ("test&param=value", "query-like string"),
    ("100%", "percent sign"),
    ("100%25", "encoded percent"),
    ("café", "unicode"),
    ("test\x00null", "null byte"),
    ("~test", "tilde"),
    ("test@host", "at sign"),
    ("test:port", "colon"),
    ("test[bracket]", "brackets"),
]

for input_str, desc in special_cases:
    try:
        result = quote_path_segment(input_str)
        # Check if result is properly quoted
        unquoted = unquote(result)
        
        print(f"  {desc:20} '{input_str}' -> '{result}'")
        
        # Check round-trip
        if unquoted != input_str:
            print(f"    WARNING: Round-trip failed: '{unquoted}' != '{input_str}'")
            
    except Exception as e:
        print(f"  {desc:20} '{input_str}' -> ERROR: {e}")

# Test 2: Path tuple joining with special characters
print("\n2. Testing _join_path_tuple with special characters...")

test_tuples = [
    (('', 'hello world'), "space in segment"),
    (('', 'hello/world'), "slash in segment"),
    (('', '../test'), "parent ref in segment"),
    (('', 'café'), "unicode in segment"),
    (('', ''), "empty segment"),
    (('', 'a', 'b', 'c'), "multiple segments"),
    (('', 'test%20space'), "pre-encoded segment"),
]

for path_tuple, desc in test_tuples:
    try:
        result = _join_path_tuple(path_tuple)
        print(f"  {desc:25} {path_tuple} -> '{result}'")
        
        # Check if slashes are preserved/escaped correctly
        if any('/' in seg for seg in path_tuple[1:]):
            if result.count('/') == len(path_tuple) - 1:
                print(f"    BUG: Slash in segment not escaped!")
                
    except Exception as e:
        print(f"  {desc:25} {path_tuple} -> ERROR: {e}")

# Test 3: Route generation with special characters
print("\n3. Testing route generation with special params...")

def test_route_with_special_params():
    pattern = "/test/{name}/{value}"
    match, generate = _compile_route(pattern)
    
    test_params = [
        {'name': 'hello', 'value': 'world'},
        {'name': 'hello world', 'value': 'test'},
        {'name': 'test/slash', 'value': 'value'},
        {'name': 'café', 'value': 'münchen'},
        {'name': '../parent', 'value': 'test'},
        {'name': 'test&foo=bar', 'value': 'value'},
    ]
    
    for params in test_params:
        try:
            generated = generate(params)
            print(f"  Params: {params}")
            print(f"    Generated: {generated}")
            
            # Try to match the generated URL
            match_result = match(generated)
            if match_result is None:
                print(f"    BUG: Generated URL doesn't match pattern!")
            else:
                # Check if params are preserved
                for key, value in params.items():
                    if key not in match_result:
                        print(f"    BUG: Key '{key}' missing from match")
                    elif match_result[key] != value:
                        print(f"    BUG: Value mismatch for '{key}': '{match_result[key]}' != '{value}'")
                        
        except Exception as e:
            print(f"  Params: {params} -> ERROR: {e}")

test_route_with_special_params()

# Test 4: Double encoding issues
print("\n4. Testing for double encoding issues...")

def test_double_encoding():
    """Check if already-encoded strings get double-encoded."""
    
    test_cases = [
        "hello%20world",  # Already has encoded space
        "test%2Fslash",   # Already has encoded slash
        "caf%C3%A9",      # Already encoded UTF-8
        "%2E%2E",         # Encoded ..
    ]
    
    for test_str in test_cases:
        # First encoding
        encoded1 = quote_path_segment(test_str)
        # Second encoding (should be same if cached)
        encoded2 = quote_path_segment(test_str)
        
        print(f"  Input: '{test_str}'")
        print(f"    First:  '{encoded1}'")
        print(f"    Second: '{encoded2}'")
        
        # Check if it got double-encoded
        if '%25' in encoded1 and '%' in test_str:
            print(f"    WARNING: Possible double encoding detected")
            
        # Check caching
        if encoded1 is not encoded2:
            print(f"    BUG: Caching not working, got different objects")

test_double_encoding()

# Test 5: Edge cases in URL quoting
print("\n5. Testing edge cases in pyramid.encode.url_quote...")

def test_url_quote_edges():
    """Test the url_quote function directly."""
    
    test_cases = [
        ("", "empty string"),
        (" ", "single space"),
        ("/", "forward slash"),
        ("//", "double slash"),
        ("~test", "tilde"),
        (":", "colon"),
        (";", "semicolon"),
        ("@", "at sign"),
        ("!", "exclamation"),
        ("$", "dollar"),
        ("&", "ampersand"),
        ("'", "apostrophe"),
        ("(", "parenthesis"),
        ("*", "asterisk"),
        ("+", "plus"),
        (",", "comma"),
        ("=", "equals"),
    ]
    
    for char, desc in test_cases:
        try:
            # Test with default safe characters
            result1 = url_quote(char)
            # Test with custom safe characters
            result2 = url_quote(char, safe='')
            
            print(f"  {desc:15} '{char}' -> default: '{result1}', no-safe: '{result2}'")
            
        except Exception as e:
            print(f"  {desc:15} '{char}' -> ERROR: {e}")

test_url_quote_edges()

# Test 6: Caching behavior verification
print("\n6. Verifying caching behavior...")

def test_cache_consistency():
    """Verify that the cache returns consistent results."""
    
    # Test with same string multiple times
    test_str = "test_string_for_cache"
    
    results = []
    for i in range(5):
        result = quote_path_segment(test_str)
        results.append(result)
        
    # All should be the same object
    if not all(r is results[0] for r in results):
        print(f"  BUG: Cache returning different objects for same input")
        for i, r in enumerate(results):
            print(f"    Call {i}: {id(r)}")
    else:
        print(f"  ✓ Cache returns same object consistently")
    
    # Test with equivalent but different objects
    str1 = "test"
    str2 = "te" + "st"
    
    result1 = quote_path_segment(str1)
    result2 = quote_path_segment(str2)
    
    if result1 is not result2:
        print(f"  Note: Cache distinguishes between equivalent strings")
        print(f"    '{str1}' (id={id(str1)}) -> id={id(result1)}")
        print(f"    '{str2}' (id={id(str2)}) -> id={id(result2)}")

test_cache_consistency()

print("\n" + "="*60)
print("URL quoting testing complete!")
print("="*60)