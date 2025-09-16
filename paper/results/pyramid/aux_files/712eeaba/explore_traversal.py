#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

# Create a mock resource tree for testing
class MockResource:
    """A simple resource class that is location-aware"""
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

# Create a simple resource tree
root = MockResource(name=None)  # Root has None or '' as name per docs
foo = MockResource('foo', root)
root.add_child('foo', foo)
bar = MockResource('bar', foo)
foo.add_child('bar', bar)
baz = MockResource('baz', bar)
bar.add_child('baz', baz)

# Also create a node with special characters
special = MockResource('hello world', foo)  # Space in name
foo.add_child('hello world', special)

# Test basic functions
import pyramid.traversal as traversal

print("=== Testing Basic Functions ===\n")

# Test find_root
print(f"find_root(baz) = {traversal.find_root(baz)}")
print(f"find_root(root) = {traversal.find_root(root)}")

# Test resource_path
print(f"\nresource_path(root) = '{traversal.resource_path(root)}'")
print(f"resource_path(foo) = '{traversal.resource_path(foo)}'")
print(f"resource_path(bar) = '{traversal.resource_path(bar)}'")
print(f"resource_path(baz) = '{traversal.resource_path(baz)}'")
print(f"resource_path(special) = '{traversal.resource_path(special)}'")

# Test resource_path_tuple
print(f"\nresource_path_tuple(root) = {traversal.resource_path_tuple(root)}")
print(f"resource_path_tuple(foo) = {traversal.resource_path_tuple(foo)}")
print(f"resource_path_tuple(bar) = {traversal.resource_path_tuple(bar)}")
print(f"resource_path_tuple(baz) = {traversal.resource_path_tuple(baz)}")

# Test find_resource
print(f"\nfind_resource(root, '/foo') = {traversal.find_resource(root, '/foo')}")
print(f"find_resource(root, '/foo/bar') = {traversal.find_resource(root, '/foo/bar')}")
print(f"find_resource(foo, 'bar') = {traversal.find_resource(foo, 'bar')}")  # relative path

# Test path parsing functions
print("\n=== Testing Path Parsing Functions ===\n")
print(f"traversal_path_info('/') = {traversal.traversal_path_info('/')}")
print(f"traversal_path_info('/foo/bar') = {traversal.traversal_path_info('/foo/bar')}")
print(f"traversal_path_info('/foo//bar') = {traversal.traversal_path_info('/foo//bar')}")
print(f"traversal_path_info('/foo/./bar') = {traversal.traversal_path_info('/foo/./bar')}")
print(f"traversal_path_info('/foo/../bar') = {traversal.traversal_path_info('/foo/../bar')}")
print(f"traversal_path_info('/foo/bar/..') = {traversal.traversal_path_info('/foo/bar/..')}")

print(f"\nsplit_path_info('/foo/bar/baz') = {traversal.split_path_info('/foo/bar/baz')}")
print(f"split_path_info('foo/bar/baz') = {traversal.split_path_info('foo/bar/baz')}")

# Test quote_path_segment
print(f"\nquote_path_segment('hello world') = '{traversal.quote_path_segment('hello world')}'")
print(f"quote_path_segment('foo/bar') = '{traversal.quote_path_segment('foo/bar')}'")
print(f"quote_path_segment('100%') = '{traversal.quote_path_segment('100%')}'")