#!/usr/bin/env python3
"""Direct Hypothesis testing without pytest."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume, Phase
from hypothesis.errors import Flaky
import traceback

# Import pyramid modules
from pyramid.traversal import traversal_path_info, quote_path_segment
from pyramid.urldispatch import _compile_route
from pyramid.request import CallbackMethodsMixin

print("Starting Hypothesis property-based tests for pyramid.router")
print("="*60)

# Test 1: Path traversal '..' handling
print("\n1. Testing path traversal '..' handling...")
@given(st.lists(st.sampled_from(['foo', 'bar', '..', 'baz', '..']), min_size=0, max_size=20))
@settings(max_examples=100)
def test_parent_refs(segments):
    path = '/' + '/'.join(segments)
    result = traversal_path_info(path)
    
    # Result should not contain '..'
    assert '..' not in result
    
    # Manually compute expected
    expected = []
    for seg in segments:
        if seg == '..':
            if expected:
                expected.pop()
        elif seg and seg != '.':
            expected.append(seg)
    
    assert result == tuple(expected), f"Path {path} gave {result}, expected {tuple(expected)}"

try:
    test_parent_refs()
    print("  ✓ PASSED - Parent reference handling works correctly")
except AssertionError as e:
    print(f"  ✗ FAILED - {e}")
    traceback.print_exc()

# Test 2: Callback ordering
print("\n2. Testing callback FIFO ordering...")
@given(st.lists(st.integers(), min_size=0, max_size=20))
@settings(max_examples=100)
def test_callback_order(values):
    class TestRequest(CallbackMethodsMixin):
        pass
    
    request = TestRequest()
    results = []
    
    for val in values:
        request.add_response_callback(
            lambda req, resp, v=val: results.append(v)
        )
    
    request._process_response_callbacks(None)
    
    assert results == list(values), f"Expected {values}, got {results}"

try:
    test_callback_order()
    print("  ✓ PASSED - Callbacks execute in FIFO order")
except AssertionError as e:
    print(f"  ✗ FAILED - {e}")
    traceback.print_exc()

# Test 3: Route pattern compilation
print("\n3. Testing route pattern compilation...")
@given(st.text(min_size=1, max_size=50).filter(
    lambda s: not any(c in s for c in ['{', '}', '*', ':', '\x00', '\n', '\r'])
))
@settings(max_examples=100)
def test_route_slash(pattern):
    # Without leading slash
    match1, _ = _compile_route(pattern)
    # With leading slash  
    match2, _ = _compile_route('/' + pattern)
    
    # Both should handle paths with leading slash
    test_path = '/' + pattern
    # At least one should match
    assert match1(test_path) is not None or match2(test_path) is not None

try:
    test_route_slash()
    print("  ✓ PASSED - Route compilation handles leading slash")
except Exception as e:
    print(f"  ✗ FAILED - {e}")
    traceback.print_exc()

# Test 4: Path segment caching
print("\n4. Testing path segment quote caching...")
@given(st.text(min_size=0, max_size=50))
@settings(max_examples=50)
def test_caching(text):
    result1 = quote_path_segment(text)
    result2 = quote_path_segment(text)
    # Should be same object due to caching
    assert result1 is result2, f"Not cached: {text}"

try:
    test_caching()
    print("  ✓ PASSED - Path segment quoting uses cache")
except AssertionError as e:
    print(f"  ✗ FAILED - {e}")
    traceback.print_exc()

# Test 5: Traversal idempotence
print("\n5. Testing traversal path idempotence...")
@given(st.lists(
    st.text(min_size=1, max_size=20).filter(
        lambda s: '/' not in s and '\x00' not in s and s not in ('.', '..')
    ),
    min_size=0,
    max_size=10
))
@settings(max_examples=100)
def test_idempotent(segments):
    path1 = '/' + '/'.join(segments)
    result1 = traversal_path_info(path1)
    
    path2 = '/' + '/'.join(result1) if result1 else '/'
    result2 = traversal_path_info(path2)
    
    assert result1 == result2, f"Not idempotent: {path1} -> {result1} -> {result2}"

try:
    test_idempotent()
    print("  ✓ PASSED - Traversal path parsing is idempotent")
except AssertionError as e:
    print(f"  ✗ FAILED - {e}")
    traceback.print_exc()

# Test 6: Edge case - excessive parent references
print("\n6. Testing excessive parent references...")
def test_excessive_parent_refs():
    """Test what happens with many '..' going beyond root."""
    test_cases = [
        ("/../foo", ('foo',)),
        ("/../../foo", ('foo',)),
        ("/../../../foo", ('foo',)),
        ("/a/../../../foo", ('foo',)),
        ("/a/b/../../..", ()),
        ("/a/b/c/../../..", ()),
    ]
    
    for path, expected in test_cases:
        result = traversal_path_info(path)
        assert result == expected, f"Path {path} gave {result}, expected {expected}"

try:
    test_excessive_parent_refs()
    print("  ✓ PASSED - Parent refs beyond root handled correctly")
except AssertionError as e:
    print(f"  ✗ FAILED - {e}")

print("\n" + "="*60)
print("Property-based testing complete!")
print("="*60)