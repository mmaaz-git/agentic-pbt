#!/usr/bin/env python3
"""Test edge cases in pyramid router."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.traversal import (
    traversal_path_info,
    split_path_info,
    ResourceTreeTraverser,
    DefaultRootFactory,
    quote_path_segment,
    _join_path_tuple
)
from pyramid.urldispatch import _compile_route, RoutesMapper
from collections import deque

print("Testing pyramid.router edge cases")
print("="*60)

# Test 1: split_path_info with Unicode
print("\n1. Testing split_path_info with special characters...")
def test_split_path():
    # Test with various Unicode characters
    test_cases = [
        "/café/München",
        "/hello world/foo bar",
        "/test%20space",
        "/emoji/😀/test",
        "/",
        "//",
        "///",
    ]
    
    for path in test_cases:
        try:
            result = split_path_info(path)
            print(f"  {path} -> {result}")
        except Exception as e:
            print(f"  {path} -> ERROR: {e}")

test_split_path()

# Test 2: ResourceTreeTraverser with view selectors
print("\n2. Testing ResourceTreeTraverser with @@view...")
class DummyRequest:
    def __init__(self, path):
        self.environ = {}
        self.matchdict = None
        self.path_info = path

class DummyRoot:
    def __getitem__(self, name):
        if name == 'existing':
            return DummyContext()
        raise KeyError(name)

class DummyContext:
    pass

traverser = ResourceTreeTraverser(DummyRoot())

test_paths = [
    "/@@view",
    "/existing/@@view",
    "/nonexisting/@@view",
    "/@@",
    "/existing/@@",
    "/@@view/subpath",
]

for path in test_paths:
    request = DummyRequest(path)
    result = traverser(request)
    print(f"  Path: {path}")
    print(f"    View: '{result['view_name']}', Subpath: {result['subpath']}")

# Test 3: RoutesMapper with duplicate names
print("\n3. Testing RoutesMapper route replacement...")
mapper = RoutesMapper()

# Add first route
route1 = mapper.connect('test', '/first')
print(f"  Added route 'test' -> '/first'")
print(f"    Route in list: {route1 in mapper.routelist}")

# Replace with second route
route2 = mapper.connect('test', '/second')
print(f"  Replaced with 'test' -> '/second'")
print(f"    Old route in list: {route1 in mapper.routelist}")
print(f"    New route in list: {route2 in mapper.routelist}")
print(f"    get_route('test') returns: {mapper.get_route('test') is route2}")

# Test 4: Pattern compilation edge cases
print("\n4. Testing route pattern compilation edge cases...")
edge_patterns = [
    "",  # Empty pattern
    "no-slash",  # No leading slash
    "//double",  # Double slash
    "/test/*rest",  # Star pattern
    "/test/{id}",  # Placeholder
    "/test/{id:[0-9]+}",  # Regex placeholder
    "/test/:old_style",  # Old style placeholder
]

for pattern in edge_patterns:
    try:
        match, generate = _compile_route(pattern)
        # Test matching
        test_path = "/" + pattern.lstrip('/')
        result = match(test_path)
        print(f"  Pattern: '{pattern}'")
        print(f"    Match '{test_path}': {result is not None}")
    except Exception as e:
        print(f"  Pattern: '{pattern}' -> ERROR: {e}")

# Test 5: Quote path segment with special chars
print("\n5. Testing quote_path_segment with special characters...")
special_chars = [
    "",
    " ",
    "hello world",
    "café",
    "../",
    "test&param=value",
    "100%",
    "a/b",
    "a//b",
    None,  # Test None handling
]

for char in special_chars:
    try:
        if char is None:
            result = quote_path_segment(None)
        else:
            result = quote_path_segment(char)
        print(f"  '{char}' -> '{result}'")
    except Exception as e:
        print(f"  '{char}' -> ERROR: {type(e).__name__}: {e}")

# Test 6: Path tuple joining
print("\n6. Testing _join_path_tuple edge cases...")
path_tuples = [
    (),  # Empty tuple
    ('',),  # Just root
    ('', 'foo'),  # Simple path
    ('', 'foo', 'bar'),  # Multiple segments
    ('', 'hello world'),  # Space in segment
    ('', '..'),  # Parent ref
    ('', 'café'),  # Unicode
    ('', ''),  # Empty segment
    ('', 'a/b'),  # Slash in segment
]

for path_tuple in path_tuples:
    try:
        result = _join_path_tuple(path_tuple)
        print(f"  {path_tuple} -> '{result}'")
    except Exception as e:
        print(f"  {path_tuple} -> ERROR: {e}")

# Test 7: Traversal with virtual root
print("\n7. Testing traversal with virtual root...")
class VirtualRootRequest:
    def __init__(self, path, vroot):
        self.environ = {'HTTP_X_VHM_ROOT': vroot} if vroot else {}
        self.matchdict = None
        self.path_info = path

test_cases = [
    ("/foo/bar", "/vroot"),
    ("/foo/bar", "/"),
    ("/foo/bar", ""),
    ("/foo/bar", None),
]

for path, vroot in test_cases:
    request = VirtualRootRequest(path, vroot)
    traverser = ResourceTreeTraverser(DummyRoot())
    try:
        result = traverser(request)
        print(f"  Path: {path}, VRoot: {vroot}")
        print(f"    Virtual root path: {result['virtual_root_path']}")
    except Exception as e:
        print(f"  Path: {path}, VRoot: {vroot} -> ERROR: {e}")

print("\n" + "="*60)
print("Edge case testing complete!")
print("="*60)