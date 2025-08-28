#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.traversal as traversal
from hypothesis import given, strategies as st, assume, settings
import string
import urllib.parse

# Test 1: split_path_info idempotence property
@given(st.lists(st.text(alphabet=string.ascii_letters + string.digits + "-_", min_size=0, max_size=20), min_size=0, max_size=10))
@settings(max_examples=500)
def test_split_path_info_idempotence(segments):
    """split_path_info should be idempotent - applying it twice gives same result"""
    # Create a path from segments
    path = '/' + '/'.join(segments)
    
    # First application
    result1 = traversal.split_path_info(path)
    
    # Join and apply again
    if result1:
        rejoined_path = '/' + '/'.join(result1)
    else:
        rejoined_path = '/'
    result2 = traversal.split_path_info(rejoined_path)
    
    # Should be idempotent
    assert result1 == result2, f"Not idempotent: {result1} != {result2} for path {path}"


# Test 2: traversal_path handling of percent encoding
@given(st.text(alphabet=string.ascii_letters + string.digits + "%", min_size=1, max_size=30))
@settings(max_examples=500)  
def test_traversal_path_percent_encoding(text):
    """traversal_path should handle percent encoding correctly"""
    # Create a path with the text
    path = '/' + text
    
    try:
        result = traversal.traversal_path(path)
        
        # If it succeeds, check that it's consistent
        assert isinstance(result, tuple)
        
        # Check for malformed percent encoding that should have failed
        import re
        # Look for incomplete percent encoding patterns
        if '%' in text:
            # Find all % followed by less than 2 hex digits
            bad_patterns = re.findall(r'%(?![0-9A-Fa-f]{2})', text)
            if bad_patterns:
                # These should have raised URLDecodeError but didn't
                # This is a potential bug - invalid encoding should fail
                pass
                
    except traversal.URLDecodeError:
        # This is expected for invalid encodings
        pass
    except UnicodeEncodeError:
        # Expected for non-ASCII strings
        pass


# Helper class for creating location-aware resources
class MockResource:
    """A simple resource class that is location-aware for testing"""
    def __init__(self, name=None, parent=None):
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


# Test 3: traverse function output dictionary invariants
@given(st.text(alphabet=string.ascii_letters + string.digits + "/-", min_size=0, max_size=50))
@settings(max_examples=500)
def test_traverse_output_invariants(path):
    """traverse should always return dict with required keys"""
    
    # Create a simple resource tree
    root = MockResource(name=None)
    foo = MockResource('foo', root)
    root.add_child('foo', foo)
    bar = MockResource('bar', foo)
    foo.add_child('bar', bar)
    
    result = traversal.traverse(root, path)
    
    # Check required keys are present (documented in docstring)
    required_keys = {'context', 'root', 'view_name', 'subpath', 'traversed', 'virtual_root', 'virtual_root_path'}
    assert required_keys.issubset(result.keys()), f"Missing keys: {required_keys - result.keys()}"
    
    # Check invariants
    assert result['root'] is root, "Root should always be the root resource"
    assert isinstance(result['subpath'], tuple), "Subpath should be a tuple"
    assert isinstance(result['traversed'], tuple), "Traversed should be a tuple"
    assert isinstance(result['view_name'], str), "View name should be a string"


# Test 4: quote_path_segment special character handling
@given(st.text(min_size=0, max_size=50))
@settings(max_examples=500)
def test_quote_path_segment_special_chars(segment):
    """quote_path_segment should properly encode special characters"""
    try:
        quoted = traversal.quote_path_segment(segment)
        
        # Result should be a string
        assert isinstance(quoted, str)
        
        # Check that dangerous characters are encoded
        if '/' in segment:
            assert '%2F' in quoted or '%2f' in quoted, f"Forward slash not encoded in {quoted}"
        
        # Empty segments should remain empty
        if segment == '':
            assert quoted == ''
        
        # Dots should be preserved (based on our observation)
        if segment == '.':
            assert quoted == '.'
        if segment == '..':
            assert quoted == '..'
        
        # Check URL decoding round-trip for ASCII segments
        if all(ord(c) < 128 for c in segment):
            # Should be able to decode what we encoded
            decoded = urllib.parse.unquote(quoted, errors='strict')
            assert decoded == segment, f"Round-trip failed: {segment} -> {quoted} -> {decoded}"
            
    except (TypeError, AttributeError) as e:
        # Segment might not be a valid type
        pass


# Test 5: Path traversal security - ".." should not escape root
@given(st.integers(min_value=0, max_value=10))
@settings(max_examples=500)
def test_split_path_info_parent_traversal_safety(num_parent_refs):
    """split_path_info should prevent traversing above root with .."""
    # Create a path that tries to go up beyond root
    path = '/' + '/'.join(['..'] * num_parent_refs) + '/target'
    result = traversal.split_path_info(path)
    
    # Should never have more .. than necessary
    # After normalization, we should just have 'target' or be empty
    assert '..' not in result, f"Parent references leaked through: {result}"
    
    # Should end with 'target' if anything
    if result:
        assert result[-1] == 'target' or len(result) == 0


# Test 6: split_path_info consistency with various separators
@given(st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20),
       st.integers(min_value=1, max_value=5))
@settings(max_examples=500)
def test_split_path_info_separator_normalization(segment, num_slashes):
    """Multiple slashes should be treated as single separator"""
    # Create paths with different numbers of slashes
    sep = '/' * num_slashes
    path1 = sep + segment
    path2 = '/' + segment
    
    result1 = traversal.split_path_info(path1)
    result2 = traversal.split_path_info(path2)
    
    # Should normalize to same result
    assert result1 == result2, f"Different results for {num_slashes} slashes: {result1} != {result2}"


# Test 7: URL decode edge cases
@given(st.text(alphabet='%0123456789ABCDEFabcdef', min_size=1, max_size=20))
@settings(max_examples=500)
def test_traversal_path_malformed_encoding(text):
    """Test how traversal_path handles malformed percent encoding"""
    path = '/' + text
    
    try:
        result = traversal.traversal_path(path)
        
        # Check if this should have been valid
        try:
            # Try to decode it with standard URL decoding
            decoded = urllib.parse.unquote(text, errors='strict')
            # If standard decoding works, pyramid should have decoded it too
            
        except Exception:
            # Standard URL decoding failed, but pyramid succeeded
            # This might indicate inconsistent behavior
            # Let's check what pyramid did with invalid sequences
            if text.count('%') > 0:
                # Look for invalid patterns like %XY where X or Y aren't hex
                import re
                invalid = re.findall(r'%(?![0-9A-Fa-f]{2})', text)
                if invalid:
                    # Pyramid accepted invalid encoding - potential bug
                    print(f"WARNING: Invalid encoding accepted: {text} -> {result}")
                    
    except (traversal.URLDecodeError, UnicodeEncodeError):
        # Expected for invalid input
        pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])