#!/usr/bin/env python3
"""Property-based tests for pyramid.router and related modules."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from collections import deque
from urllib.parse import quote, unquote

# Import pyramid modules
from pyramid.traversal import (
    traversal_path_info,
    quote_path_segment,
    split_path_info,
    ResourceTreeTraverser,
    resource_path_tuple,
    find_resource,
    _join_path_tuple
)
from pyramid.urldispatch import _compile_route, RoutesMapper
from pyramid.request import CallbackMethodsMixin


# Strategy for generating path segments
path_segment = st.text(min_size=1, max_size=100).filter(
    lambda s: '/' not in s and '\x00' not in s and s not in ('.', '..')
)

# Strategy for generating paths
path_strategy = st.lists(path_segment, min_size=0, max_size=10)


class TestPathTraversalNormalization:
    """Test path traversal normalization properties."""
    
    @given(st.lists(st.sampled_from(['', '.', '..', 'foo', 'bar', 'baz']), min_size=0, max_size=20))
    def test_traversal_path_info_removes_dots(self, segments):
        """traversal_path_info should ignore '.' segments."""
        path = '/' + '/'.join(segments)
        result = traversal_path_info(path)
        
        # '.' segments should not appear in result
        assert '.' not in result
        
    @given(st.lists(st.sampled_from(['foo', 'bar', '..', 'baz', '..']), min_size=0, max_size=20))
    def test_traversal_path_info_handles_parent_refs(self, segments):
        """traversal_path_info should handle '..' by removing previous segment."""
        path = '/' + '/'.join(segments)
        result = traversal_path_info(path)
        
        # Result should not contain '..'
        assert '..' not in result
        
        # Manually compute expected result
        expected = []
        for seg in segments:
            if seg == '..':
                if expected:
                    expected.pop()
            elif seg and seg != '.':
                expected.append(seg)
        
        assert result == tuple(expected)
    
    @given(st.text(min_size=0, max_size=100))
    def test_traversal_path_info_handles_unicode(self, text):
        """traversal_path_info should handle Unicode text properly."""
        # Filter out problematic characters
        assume(not any(c in text for c in ['\x00', '/', '\r', '\n']))
        
        path = '/' + text
        try:
            # Should encode to ASCII for the initial check
            path.encode('ascii')
            result = traversal_path_info(path)
            # Result should be a tuple
            assert isinstance(result, tuple)
        except (UnicodeEncodeError, UnicodeDecodeError):
            # Expected for non-ASCII characters
            pass
    
    @given(path_strategy)
    def test_traversal_path_info_idempotent(self, segments):
        """Applying traversal_path_info twice should be idempotent."""
        path1 = '/' + '/'.join(segments)
        result1 = traversal_path_info(path1)
        
        # Convert back to path and parse again
        path2 = '/' + '/'.join(result1) if result1 else '/'
        result2 = traversal_path_info(path2)
        
        assert result1 == result2


class TestRoutePatternCompilation:
    """Test route pattern compilation properties."""
    
    @given(st.text(min_size=1, max_size=50).filter(
        lambda s: not any(c in s for c in ['{', '}', '*', ':', '\x00'])
    ))
    def test_route_compilation_adds_leading_slash(self, pattern):
        """Route compilation should ensure patterns start with '/'."""
        # Test without leading slash
        match, generate = _compile_route(pattern)
        
        # Test with leading slash
        match2, generate2 = _compile_route('/' + pattern)
        
        # Both should work on paths with leading slash
        test_path = '/' + pattern
        assert match(test_path) is not None or match2(test_path) is not None
    
    @given(st.text(min_size=1, max_size=30).filter(
        lambda s: s.replace('_', '').replace('-', '').isalnum()
    ))
    def test_old_style_pattern_conversion(self, name):
        """Old style :name patterns should be converted to {name}."""
        old_pattern = f'/test/:{name}'
        new_pattern = f'/test/{{{name}}}'
        
        match_old, gen_old = _compile_route(old_pattern)
        match_new, gen_new = _compile_route(new_pattern)
        
        # Both should match the same paths
        test_path = '/test/value123'
        result_old = match_old(test_path)
        result_new = match_new(test_path)
        
        if result_old and result_new:
            assert name in result_old
            assert name in result_new
            assert result_old[name] == result_new[name]
    
    @given(st.lists(
        st.text(min_size=1, max_size=20).filter(
            lambda s: '/' not in s and not any(c in s for c in ['{', '}', '*', ':', '\x00'])
        ),
        min_size=1,
        max_size=5
    ))
    def test_static_route_matching(self, segments):
        """Static routes should match exactly."""
        pattern = '/' + '/'.join(segments)
        match, generate = _compile_route(pattern)
        
        # Should match the exact pattern
        assert match(pattern) is not None
        
        # Should not match with extra segments
        assert match(pattern + '/extra') is None
        
        # Should not match with missing segments
        if len(segments) > 1:
            partial = '/' + '/'.join(segments[:-1])
            assert match(partial) is None


class TestCallbackOrdering:
    """Test callback ordering properties."""
    
    @given(st.lists(st.integers(), min_size=0, max_size=20))
    def test_response_callbacks_fifo_order(self, values):
        """Response callbacks should execute in FIFO order."""
        
        class TestRequest(CallbackMethodsMixin):
            pass
        
        request = TestRequest()
        results = []
        
        # Add callbacks that append their value to results
        for val in values:
            request.add_response_callback(
                lambda req, resp, v=val: results.append(v)
            )
        
        # Process callbacks
        class DummyResponse:
            pass
        
        request._process_response_callbacks(DummyResponse())
        
        # Results should match the order values were added
        assert results == list(values)
    
    @given(st.integers(min_value=0, max_value=100))
    def test_response_callbacks_count(self, count):
        """All added callbacks should be executed exactly once."""
        
        class TestRequest(CallbackMethodsMixin):
            pass
        
        request = TestRequest()
        executed = []
        
        for i in range(count):
            request.add_response_callback(
                lambda req, resp, idx=i: executed.append(idx)
            )
        
        request._process_response_callbacks(None)
        
        # All callbacks should have executed
        assert len(executed) == count
        assert set(executed) == set(range(count))
    
    @given(st.integers(min_value=1, max_value=50))
    def test_callbacks_cleared_after_processing(self, count):
        """Callbacks should be cleared after processing."""
        
        class TestRequest(CallbackMethodsMixin):
            pass
        
        request = TestRequest()
        
        for i in range(count):
            request.add_response_callback(lambda req, resp: None)
        
        # Process callbacks
        request._process_response_callbacks(None)
        
        # Callbacks deque should be empty
        assert len(request.response_callbacks) == 0


class TestPathQuoting:
    """Test path segment quoting properties."""
    
    @given(st.text(min_size=0, max_size=100).filter(
        lambda s: not any(ord(c) > 127 for c in s)  # ASCII only
    ))
    def test_quote_path_segment_deterministic(self, text):
        """quote_path_segment should be deterministic."""
        result1 = quote_path_segment(text)
        result2 = quote_path_segment(text)
        
        assert result1 == result2
    
    @given(st.text(min_size=0, max_size=50))
    def test_quote_path_segment_caching(self, text):
        """quote_path_segment caches results."""
        # First call populates cache
        result1 = quote_path_segment(text)
        
        # Second call should return cached value
        result2 = quote_path_segment(text)
        
        # Should be the exact same object due to caching
        assert result1 is result2
    
    @given(st.lists(
        st.text(min_size=1, max_size=20).filter(
            lambda s: '/' not in s and '\x00' not in s
        ),
        min_size=0,
        max_size=10
    ))
    def test_join_path_tuple_preserves_structure(self, segments):
        """_join_path_tuple should preserve path structure."""
        # Create a tuple with empty string prefix (absolute path)
        path_tuple = ('',) + tuple(segments)
        
        result = _join_path_tuple(path_tuple)
        
        # Result should start with /
        assert result.startswith('/')
        
        # Should be able to split it back (approximately)
        if segments:
            # Each segment should appear in the result
            for seg in segments:
                # URL-encoded version should be in result
                quoted = quote_path_segment(seg)
                assert quoted in result or seg == ''


class TestResourceTreeTraverser:
    """Test ResourceTreeTraverser properties."""
    
    @given(st.lists(
        st.text(min_size=1, max_size=20).filter(
            lambda s: not any(c in s for c in ['/', '@@', '\x00'])
        ),
        min_size=0,
        max_size=5
    ))
    def test_traverser_view_selector_detection(self, segments):
        """Traverser should detect @@view segments."""
        
        class DummyRequest:
            def __init__(self, path):
                self.environ = {}
                self.matchdict = None
                self.path_info = path
        
        class DummyRoot:
            def __getitem__(self, name):
                if name in segments:
                    return DummyRoot()
                raise KeyError(name)
        
        traverser = ResourceTreeTraverser(DummyRoot())
        
        # Test with @@view at different positions
        for i in range(len(segments) + 1):
            path_parts = list(segments[:i]) + ['@@myview'] + list(segments[i:])
            path = '/' + '/'.join(path_parts)
            
            request = DummyRequest(path)
            result = traverser(request)
            
            # Should detect view name
            assert result['view_name'] == 'myview'
            # Subpath should be the remaining segments
            assert result['subpath'] == tuple(segments[i:])
    
    @given(st.lists(
        st.text(min_size=1, max_size=20).filter(
            lambda s: not any(c in s for c in ['/', '@@', '\x00'])
        ),
        min_size=1,
        max_size=5
    ))
    def test_traverser_context_finding(self, segments):
        """Traverser should find the deepest accessible context."""
        
        class DummyRequest:
            def __init__(self, path):
                self.environ = {}
                self.matchdict = None
                self.path_info = path
        
        # Root only contains first segment
        class LimitedRoot:
            def __getitem__(self, name):
                if name == segments[0]:
                    return LimitedContext()
                raise KeyError(name)
        
        class LimitedContext:
            pass  # No __getitem__, so traversal stops here
        
        traverser = ResourceTreeTraverser(LimitedRoot())
        path = '/' + '/'.join(segments)
        request = DummyRequest(path)
        
        result = traverser(request)
        
        # Should have traversed only the first segment
        assert result['traversed'] == (segments[0],)
        # View name should be the second segment if exists
        if len(segments) > 1:
            assert result['view_name'] == segments[1]
            # Subpath should be remaining segments
            assert result['subpath'] == tuple(segments[2:])
        else:
            assert result['view_name'] == ''


class TestRoutesMapper:
    """Test RoutesMapper properties."""
    
    @given(st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'),  # name
            st.text(min_size=1, max_size=30).filter(
                lambda s: not any(c in s for c in ['{', '}', '*', ':', '\x00'])
            )  # pattern
        ),
        min_size=0,
        max_size=10,
        unique_by=lambda x: x[0]  # unique names
    ))
    def test_routes_mapper_ordering(self, routes):
        """Routes should be matched in the order they were added."""
        mapper = RoutesMapper()
        
        # Add all routes
        for name, pattern in routes:
            mapper.connect(name, '/' + pattern)
        
        # Routes should be in order
        route_names = [r.name for r in mapper.routelist]
        expected_names = [name for name, _ in routes]
        assert route_names == expected_names
    
    @given(
        st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'),
        st.text(min_size=1, max_size=30).filter(
            lambda s: not any(c in s for c in ['{', '}', '*', ':', '\x00'])
        )
    )
    def test_routes_mapper_replacement(self, name, pattern):
        """Connecting a route with existing name should replace it."""
        mapper = RoutesMapper()
        
        # Add initial route
        route1 = mapper.connect(name, '/first')
        assert mapper.get_route(name) == route1
        
        # Replace with new route
        route2 = mapper.connect(name, '/' + pattern)
        assert mapper.get_route(name) == route2
        assert route1 not in mapper.routelist
        assert route2 in mapper.routelist