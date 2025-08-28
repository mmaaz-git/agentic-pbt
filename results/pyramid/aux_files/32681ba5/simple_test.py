#!/usr/bin/env python3
"""Simple direct test of pyramid.router properties."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.traversal import traversal_path_info
from pyramid.urldispatch import _compile_route

# Test 1: traversal_path_info handles '..' correctly
print("Test 1: Path normalization with '..'")
path = "/foo/bar/../baz"
result = traversal_path_info(path)
print(f"  Input:  {path}")
print(f"  Result: {result}")
print(f"  Expected: ('foo', 'baz')")
assert result == ('foo', 'baz'), f"Failed: got {result}"
print("  ✓ PASSED")

# Test 2: traversal_path_info handles empty segments
print("\nTest 2: Path with empty segments")
path = "/foo//bar///baz"
result = traversal_path_info(path)
print(f"  Input:  {path}")
print(f"  Result: {result}")
print(f"  Expected: ('foo', 'bar', 'baz')")
assert result == ('foo', 'bar', 'baz'), f"Failed: got {result}"
print("  ✓ PASSED")

# Test 3: Route compilation adds leading slash
print("\nTest 3: Route compilation without leading slash")
pattern = "test/route"
match, generate = _compile_route(pattern)
test_path = "/test/route"
result = match(test_path)
print(f"  Pattern: {pattern}")
print(f"  Test path: {test_path}")
print(f"  Match result: {result}")
assert result is not None, "Failed to match"
print("  ✓ PASSED")

# Test 4: Old style pattern conversion
print("\nTest 4: Old style :name pattern")
old_pattern = "/test/:id"
match, generate = _compile_route(old_pattern)
test_path = "/test/123"
result = match(test_path)
print(f"  Pattern: {old_pattern}")
print(f"  Test path: {test_path}")
print(f"  Match result: {result}")
assert result is not None and 'id' in result, f"Failed: got {result}"
assert result['id'] == '123', f"Failed: id={result['id']}"
print("  ✓ PASSED")

# Test 5: Edge case - many parent references
print("\nTest 5: Many parent references '../'")
path = "/a/b/c/../../.."
result = traversal_path_info(path)
print(f"  Input:  {path}")
print(f"  Result: {result}")
print(f"  Expected: ()")
assert result == (), f"Failed: got {result}"
print("  ✓ PASSED")

# Test 6: Going beyond root with '..'
print("\nTest 6: Parent references beyond root")
path = "/../../../foo"
result = traversal_path_info(path)
print(f"  Input:  {path}")
print(f"  Result: {result}")
print(f"  Expected: ('foo',)")
assert result == ('foo',), f"Failed: got {result}"
print("  ✓ PASSED")

print("\n" + "="*50)
print("All simple tests passed!")
print("="*50)