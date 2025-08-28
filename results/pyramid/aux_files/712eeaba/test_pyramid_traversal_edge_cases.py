#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.traversal as traversal
from hypothesis import given, strategies as st, assume, settings, example
import string

# Edge case tests to try to find bugs

# Test 1: Empty strings and None values in resource names
@given(st.sampled_from([None, '', '   ', '\t', '\n']))
@settings(max_examples=50)
def test_edge_case_empty_resource_names(name):
    """Test resources with empty or whitespace names"""
    class Resource:
        def __init__(self, name, parent=None):
            self.__name__ = name
            self.__parent__ = parent
            self._children = {}
        
        def __getitem__(self, key):
            return self._children[key]
        
        def add_child(self, name, child):
            child.__name__ = name
            child.__parent__ = self
            self._children[name] = child
    
    root = Resource(None)  # Root should have None
    child = Resource(name, root)
    
    # Try to get paths
    root_path = traversal.resource_path(root)
    child_path = traversal.resource_path(child)
    
    # Try to get path tuples
    root_tuple = traversal.resource_path_tuple(root)
    child_tuple = traversal.resource_path_tuple(child)
    
    assert root_path == '/'
    assert root_tuple == ('',)


# Test 2: Unicode and special characters in paths
@given(st.text(alphabet="αβγδε中文العربية emoji:🎉🦄", min_size=1, max_size=10))
@settings(max_examples=100)
def test_unicode_in_resource_names(name):
    """Test that Unicode characters are handled correctly"""
    class Resource:
        def __init__(self, name, parent=None):
            self.__name__ = name
            self.__parent__ = parent
            self._children = {}
        
        def __getitem__(self, key):
            return self._children[key]
            
        def add_child(self, name, child):
            child.__name__ = name
            child.__parent__ = self
            self._children[name] = child
            return child
    
    root = Resource(None)
    child = root.add_child(name, Resource(name))
    
    # Get path and tuple
    path = traversal.resource_path(child)
    path_tuple = traversal.resource_path_tuple(child)
    
    # Try round-trip
    try:
        found = traversal.find_resource(root, path)
        assert found is child
    except KeyError:
        # Some unicode might not round-trip correctly
        pass
    
    # Tuple should preserve the original name
    assert path_tuple == ('', name)
    
    # Should work with tuple
    found2 = traversal.find_resource(root, path_tuple)
    assert found2 is child


# Test 3: Very long paths
@given(st.lists(st.text(string.ascii_letters, min_size=1, max_size=5), min_size=100, max_size=200))
@settings(max_examples=10, deadline=5000)
def test_very_long_paths(segments):
    """Test handling of very deep resource trees"""
    class Resource:
        def __init__(self, name, parent=None):
            self.__name__ = name
            self.__parent__ = parent
            self._children = {}
        
        def __getitem__(self, key):
            return self._children[key]
            
        def add_child(self, name, child):
            child.__name__ = name
            child.__parent__ = self
            self._children[name] = child
            return child
    
    # Build a very deep tree
    root = Resource(None)
    current = root
    for segment in segments:
        current = current.add_child(segment, Resource(segment))
    
    # Get the path
    path = traversal.resource_path(current)
    path_tuple = traversal.resource_path_tuple(current)
    
    # Verify the path is correct
    assert path.count('/') == len(segments)
    assert len(path_tuple) == len(segments) + 1  # +1 for the leading ''
    
    # Try round-trip
    found = traversal.find_resource(root, path)
    assert found is current


# Test 4: Path segments that look like special path components
@given(st.sampled_from(['..', '.', '...', '....', '.hidden', '..hidden', '../etc/passwd']))
@settings(max_examples=50)
def test_special_looking_segments(name):
    """Test resource names that look like special path components"""
    class Resource:
        def __init__(self, name, parent=None):
            self.__name__ = name
            self.__parent__ = parent
            self._children = {}
        
        def __getitem__(self, key):
            return self._children[key]
            
        def add_child(self, name, child):
            child.__name__ = name
            child.__parent__ = self
            self._children[name] = child
            return child
    
    root = Resource(None)
    child = root.add_child(name, Resource(name))
    
    path = traversal.resource_path(child)
    path_tuple = traversal.resource_path_tuple(child)
    
    # The tuple should contain the literal name
    assert path_tuple == ('', name)
    
    # Round-trip with tuple should work
    found = traversal.find_resource(root, path_tuple)
    assert found is child
    
    # String path might be escaped differently
    if name not in ['.', '..']:
        try:
            found2 = traversal.find_resource(root, path)
            # If it doesn't raise, it should find the right node
            assert found2 is child
        except KeyError:
            # '.' and '..' are special and might not round-trip
            pass


# Test 5: split_path_info with pathological inputs
@given(st.text(alphabet="/.?&=", min_size=0, max_size=100))
@settings(max_examples=200)
def test_split_path_info_pathological(path):
    """Test split_path_info with paths containing only special characters"""
    result = traversal.split_path_info(path)
    
    # Should always return a tuple
    assert isinstance(result, tuple)
    
    # Should not contain empty strings or dots
    for segment in result:
        assert segment not in ['', '.']
    
    # Multiple slashes should collapse
    collapsed = path
    while '//' in collapsed:
        collapsed = collapsed.replace('//', '/')
    
    result2 = traversal.split_path_info(collapsed)
    assert result == result2


# Test 6: traversal_path_info with malformed percent encoding
@given(st.text(alphabet=string.ascii_letters + string.digits + "%", min_size=1, max_size=30))
@settings(max_examples=200)
def test_traversal_path_malformed_encoding(path):
    """Test traversal_path with malformed percent-encoded sequences"""
    # Add some malformed encodings
    if '%' in path and not path.endswith('%'):
        path = path.replace('%', '%X')  # Invalid hex
    
    try:
        result = traversal.traversal_path(path)
        # If it succeeds, should return a tuple
        assert isinstance(result, tuple)
    except (traversal.URLDecodeError, UnicodeDecodeError, ValueError):
        # Expected for malformed input
        pass


# Test 7: Caching behavior of quote_path_segment
@given(st.lists(st.text(string.printable, min_size=1, max_size=10), min_size=1000, max_size=1000))
@settings(max_examples=1, deadline=10000)
def test_quote_path_segment_cache_behavior(segments):
    """Test that the cache in quote_path_segment doesn't break with many unique values"""
    # The cache is module-level and unlimited, let's test with many values
    results = []
    for segment in segments:
        result = traversal.quote_path_segment(segment)
        results.append(result)
        assert isinstance(result, str)
    
    # Re-quote all segments, should use cache
    for i, segment in enumerate(segments):
        cached_result = traversal.quote_path_segment(segment)
        assert cached_result == results[i]
        # Should be the same object (from cache)
        assert cached_result is results[i]


# Test 8: Non-string types as resource names
@given(st.one_of(st.integers(), st.floats(allow_nan=False), st.booleans(), 
                  st.lists(st.integers(), max_size=3)))
@settings(max_examples=100)
def test_nonstring_resource_names(name):
    """Test resources with non-string names (should be converted)"""
    class Resource:
        def __init__(self, name, parent=None):
            self.__name__ = name
            self.__parent__ = parent
            self._children = {}
        
        def __getitem__(self, key):
            return self._children.get(str(key), self._children.get(key))
            
        def add_child(self, name, child):
            child.__name__ = name
            child.__parent__ = self
            self._children[str(name)] = child
            return child
    
    root = Resource(None)
    child = root.add_child(name, Resource(name))
    
    # quote_path_segment should handle conversion
    try:
        path = traversal.resource_path(child)
        # Should contain string representation
        assert str(name) in path or traversal.quote_path_segment(str(name)) in path
    except (TypeError, AttributeError) as e:
        # Some types might not be convertible
        if isinstance(name, list):
            pass  # Lists as names will fail
        else:
            raise


# Test 9: Mixed string/tuple paths in find_resource
class TestResource:
    def __init__(self, name, parent=None):
        self.__name__ = name
        self.__parent__ = parent
        self._children = {}
    
    def __getitem__(self, key):
        return self._children[key]
        
    def add_child(self, name, child):
        child.__name__ = name
        child.__parent__ = self
        self._children[name] = child
        return child

@given(st.lists(st.text(string.ascii_letters, min_size=1, max_size=5), min_size=1, max_size=5))
@settings(max_examples=100)
def test_find_resource_string_tuple_equivalence(segments):
    """Test that string and tuple paths to find_resource are equivalent"""
    # Build a tree
    root = TestResource(None)
    current = root
    for segment in segments:
        current = current.add_child(segment, TestResource(segment))
    
    # Create string path
    string_path = '/' + '/'.join(segments)
    
    # Create tuple path  
    tuple_path = ('',) + tuple(segments)
    
    # Both should find the same resource
    found_string = traversal.find_resource(root, string_path)
    found_tuple = traversal.find_resource(root, tuple_path)
    
    assert found_string is found_tuple
    assert found_string is current


# Test 10: traversal with circular references (shouldn't happen but let's test)
def test_circular_reference_handling():
    """Test handling of circular parent references"""
    class Resource:
        def __init__(self, name):
            self.__name__ = name
            self.__parent__ = None
            self._children = {}
        
        def __getitem__(self, key):
            return self._children[key]
    
    # Create circular reference
    a = Resource('a')
    b = Resource('b')
    a.__parent__ = b
    b.__parent__ = a
    
    # This should not infinite loop
    try:
        # find_root should handle this gracefully (or fail)
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Infinite loop detected")
        
        # Set a timeout
        signal.signal(signal.SIGALRM, timeout_handler) 
        signal.alarm(1)  # 1 second timeout
        
        try:
            root = traversal.find_root(a)
            # If it returns, check what it returned
            assert root is a or root is b
        finally:
            signal.alarm(0)  # Cancel the alarm
            
    except (RecursionError, TimeoutError):
        # Expected if there's no protection against cycles
        pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])