#!/usr/bin/env python3
"""Minimal test to confirm the bugs"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.traversal as traversal
from hypothesis import given, strategies as st, settings, example

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

# Property-based test that discovered the bugs
@given(st.one_of(
    st.just('..'),
    st.just('.'),
    st.just(0),
    st.just(''),
    st.text().filter(lambda x: '..' in x)
))
@example('..')
@example(0)
@example('')
@settings(max_examples=50)
def test_round_trip_with_special_names(name):
    """Test that find_resource(root, resource_path_tuple(node)) returns node"""
    root = Resource(None)
    child = root.add_child(name, Resource(name))
    
    # Get the path tuple
    path_tuple = traversal.resource_path_tuple(child)
    
    # Round-trip should work
    found = traversal.find_resource(root, path_tuple)
    
    # This assertion fails for several inputs
    assert found is child, f"Round-trip failed for name={repr(name)}: expected child, got {found}"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])