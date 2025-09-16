#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.traversal as traversal
from hypothesis import given, strategies as st, assume, settings
import string
import re

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
    
    def __repr__(self):
        return f"<Resource {self.__name__}>"
    
    def __eq__(self, other):
        return self is other


# Strategy for generating valid resource names (avoiding problematic characters)
# Based on the code, names should be strings that can be URL-encoded
resource_name_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "-_.~",
    min_size=1,
    max_size=20
).filter(lambda x: x not in [".", ".."])  # Exclude special path segments

# Strategy for building resource trees
@st.composite
def resource_tree(draw, max_depth=3):
    """Generate a resource tree with random structure"""
    root = MockResource(name=None)  # Root must have None or '' name
    
    # Build a tree with random depth and branches
    current_level = [root]
    for depth in range(draw(st.integers(1, max_depth))):
        next_level = []
        for parent in current_level:
            # Add 0-3 children to each node
            num_children = draw(st.integers(0, 3))
            for _ in range(num_children):
                name = draw(resource_name_strategy)
                # Ensure unique names at this level
                if name not in parent._children:
                    child = MockResource(name, parent)
                    parent.add_child(name, child)
                    next_level.append(child)
        if not next_level:
            break
        current_level = next_level
    
    # Return root and a random node from the tree
    all_nodes = []
    def collect_nodes(node):
        all_nodes.append(node)
        for child in node._children.values():
            collect_nodes(child)
    collect_nodes(root)
    
    selected_node = draw(st.sampled_from(all_nodes))
    return root, selected_node


# Test 1: Round-trip property for resource_path and find_resource
# Documented as "logical inverse" in lines 44-47 and 126-128
@given(resource_tree())
@settings(max_examples=200)
def test_resource_path_find_resource_roundtrip(tree_data):
    """Test that find_resource(root, resource_path(node)) returns the original node"""
    root, node = tree_data
    
    # Get the path of the node
    path = traversal.resource_path(node)
    
    # Find the resource using that path
    found = traversal.find_resource(root, path)
    
    # Should get back the same node
    assert found is node, f"Round-trip failed: expected {node}, got {found}"


# Test 2: Round-trip with resource_path_tuple
@given(resource_tree())
@settings(max_examples=200)
def test_resource_path_tuple_find_resource_roundtrip(tree_data):
    """Test that find_resource works with tuples from resource_path_tuple"""
    root, node = tree_data
    
    # Get the path tuple of the node
    path_tuple = traversal.resource_path_tuple(node)
    
    # Find the resource using that tuple
    found = traversal.find_resource(root, path_tuple)
    
    # Should get back the same node
    assert found is node, f"Round-trip with tuple failed: expected {node}, got {found}"


# Test 3: split_path_info normalization properties
# Based on documentation in lines 514-522
@given(st.lists(st.text(alphabet=string.printable, min_size=0, max_size=10), max_size=10))
@settings(max_examples=200)
def test_split_path_info_normalization(segments):
    """Test that split_path_info properly normalizes paths"""
    # Build a path with the segments
    path = '/'.join(segments)
    
    result = traversal.split_path_info(path)
    
    # Properties to check:
    # 1. Result should be a tuple
    assert isinstance(result, tuple)
    
    # 2. Empty segments and '.' should be removed
    for segment in result:
        assert segment != ''
        assert segment != '.'
    
    # 3. Leading/trailing slashes should be stripped
    assert traversal.split_path_info('/' + path + '/') == result
    
    # 4. Multiple consecutive slashes should be treated as one
    double_slash_path = path.replace('/', '//')
    assert traversal.split_path_info(double_slash_path) == result


# Test 4: '..' handling in split_path_info
@given(st.lists(resource_name_strategy, min_size=0, max_size=5))
@settings(max_examples=200)
def test_split_path_info_parent_navigation(segments):
    """Test that '..' properly removes the previous segment"""
    # Create a path with .. at the end
    if segments:
        path = '/'.join(segments) + '/..'
        result = traversal.split_path_info(path)
        
        # Should have one less segment (unless empty)
        expected_length = max(0, len(segments) - 1)
        assert len(result) == expected_length
        
        # The remaining segments should match
        if expected_length > 0:
            assert result == tuple(segments[:-1])


# Test 5: traversal_path_info consistency
@given(st.text(alphabet=string.ascii_letters + string.digits + "/-._~", min_size=0, max_size=50))
@settings(max_examples=200)  
def test_traversal_path_info_consistency(path):
    """Test that traversal_path_info handles various path formats consistently"""
    try:
        result = traversal.traversal_path_info(path)
        
        # Should return a tuple
        assert isinstance(result, tuple)
        
        # All elements should be strings
        for segment in result:
            assert isinstance(segment, str)
        
        # Test consistency: same path with extra slashes should give same result
        if path and not path.startswith('/'):
            # Make it absolute and test
            abs_result = traversal.traversal_path_info('/' + path)
            # Should potentially be the same after making it absolute
            assert isinstance(abs_result, tuple)
            
    except traversal.URLDecodeError:
        # Some paths may not be decodeable, which is fine
        pass


# Test 6: quote_path_segment encoding and caching
@given(st.text(alphabet=string.printable, min_size=0, max_size=30))
@settings(max_examples=200)
def test_quote_path_segment_properties(segment):
    """Test quote_path_segment encoding properties"""
    # First call
    result1 = traversal.quote_path_segment(segment)
    
    # Second call (should use cache)
    result2 = traversal.quote_path_segment(segment)
    
    # Should be identical (same object due to caching)
    assert result1 == result2
    assert result1 is result2  # Cache returns same object
    
    # Result should be a string
    assert isinstance(result1, str)
    
    # Special characters should be encoded
    if ' ' in segment:
        assert '%20' in result1
    if '/' in segment:
        assert '%2F' in result1
    if '%' in segment:
        # % should be encoded as %25
        assert '%25' in result1


# Test 7: find_root always returns root with no parent
@given(resource_tree())
@settings(max_examples=200)
def test_find_root_properties(tree_data):
    """Test that find_root always returns a resource with __parent__ = None"""
    root, node = tree_data
    
    found_root = traversal.find_root(node)
    
    # Should have no parent
    assert found_root.__parent__ is None
    
    # Should be the actual root
    assert found_root is root


# Test 8: resource_path_tuple structure invariants
@given(resource_tree())
@settings(max_examples=200)
def test_resource_path_tuple_structure(tree_data):
    """Test invariants of resource_path_tuple output"""
    root, node = tree_data
    
    path_tuple = traversal.resource_path_tuple(node)
    
    # Should be a tuple
    assert isinstance(path_tuple, tuple)
    
    # Should start with empty string (absolute path marker)
    assert len(path_tuple) >= 1
    assert path_tuple[0] == ''
    
    # All other elements should be the __name__ attributes going up the tree
    if node is not root:
        # Verify the path matches the lineage
        from pyramid.location import lineage
        names = [loc.__name__ or '' for loc in lineage(node)]
        names.reverse()
        assert path_tuple == tuple(names)


# Test 9: Relative vs absolute path handling in find_resource
@given(resource_tree(), st.booleans())
@settings(max_examples=200)
def test_find_resource_relative_absolute(tree_data, use_absolute):
    """Test that find_resource handles relative and absolute paths correctly"""
    root, node = tree_data
    
    if node is root:
        return  # Skip root as it has no path segments
    
    # Get the full path
    full_path = traversal.resource_path(node)
    
    if use_absolute:
        # Absolute path from root
        found = traversal.find_resource(root, full_path)
        assert found is node
    else:
        # Relative path from parent
        if node.__parent__ and node.__name__:
            found = traversal.find_resource(node.__parent__, node.__name__)
            assert found is node


# Test 10: traversal_path and traversal_path_info relationship
@given(st.text(alphabet=string.ascii_letters + string.digits + "/-", min_size=1, max_size=30))
@settings(max_examples=200)
def test_traversal_path_and_path_info_consistency(path):
    """Test that traversal_path properly delegates to traversal_path_info"""
    # Ensure path is ASCII-encodable
    try:
        path.encode('ascii')
    except UnicodeEncodeError:
        return
    
    try:
        # traversal_path should handle URL-encoded paths
        result1 = traversal.traversal_path(path)
        
        # traversal_path_info should handle already-decoded paths  
        result2 = traversal.traversal_path_info(path)
        
        # Both should return tuples
        assert isinstance(result1, tuple)
        assert isinstance(result2, tuple)
        
        # For simple ASCII paths without encoding, results should be similar
        if not any(c in path for c in "%"):
            assert result1 == result2
            
    except (traversal.URLDecodeError, UnicodeDecodeError):
        # Some inputs may not be valid, which is acceptable
        pass


# Test 11: URL encoding/decoding in paths
@given(resource_name_strategy)
@settings(max_examples=200)
def test_special_characters_in_resource_names(name):
    """Test that resources with special characters in names work correctly"""
    # Create a simple tree with the special name
    root = MockResource(name=None)
    child = MockResource(name, root)
    root.add_child(name, child)
    
    # Get the path (should be URL-encoded)
    path = traversal.resource_path(child)
    
    # Should be able to find it again
    found = traversal.find_resource(root, path)
    assert found is child
    
    # Path tuple should preserve the original name
    path_tuple = traversal.resource_path_tuple(child)
    assert path_tuple == ('', name)
    
    # Should also work with the tuple
    found2 = traversal.find_resource(root, path_tuple)
    assert found2 is child


if __name__ == "__main__":
    # Run tests with pytest
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])