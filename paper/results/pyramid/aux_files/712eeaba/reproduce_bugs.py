#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.traversal as traversal

print("=== Bug 1: '..' as literal resource name ===")
print("When a resource is named '..' (literally), find_resource with tuple path fails\n")

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
    
    def __repr__(self):
        return f"<Resource '{self.__name__}'>"

# Create resources with '..' as name
root = Resource(None)
child = root.add_child('..', Resource('..'))

print(f"Root: {root}")
print(f"Child named '..': {child}")
print(f"root._children: {root._children}")

# Get path tuple
path_tuple = traversal.resource_path_tuple(child)
print(f"\nresource_path_tuple(child) = {path_tuple}")

# Try to find it
found = traversal.find_resource(root, path_tuple)
print(f"find_resource(root, {path_tuple}) = {found}")

print(f"Expected: {child}")
print(f"Got: {found}")
print(f"Bug confirmed: {found is not child}")

print("\n" + "="*60)
print("=== Bug 2: Path traversal sequences in resource names ===")
print("When a resource name contains '../', find_resource fails\n")

root2 = Resource(None)
child2 = root2.add_child('../etc/passwd', Resource('../etc/passwd'))

print(f"Root: {root2}")
print(f"Child named '../etc/passwd': {child2}")

path_tuple2 = traversal.resource_path_tuple(child2)
print(f"\nresource_path_tuple(child) = {path_tuple2}")

try:
    found2 = traversal.find_resource(root2, path_tuple2)
    print(f"find_resource succeeded: {found2}")
except KeyError as e:
    print(f"find_resource failed with KeyError: {e}")
    print("Bug confirmed: KeyError raised instead of finding the resource")

print("\n" + "="*60)
print("=== Bug 3: Numeric resource names ===")
print("When a resource has a numeric name, resource_path may not handle it correctly\n")

root3 = Resource(None)
# Test with integer 0
child3 = Resource(0, root3)
root3._children['0'] = child3  # Store with string key
child3.__parent__ = root3

print(f"Root: {root3}")
print(f"Child with numeric name 0: {child3}")
print(f"Child.__name__ = {child3.__name__} (type: {type(child3.__name__)})")

# Try to get path
path3 = traversal.resource_path(child3)
print(f"\nresource_path(child) = '{path3}'")
print(f"Expected: '/0' or similar")
print(f"Bug confirmed: {path3 == '/'}")

# Also test path tuple
path_tuple3 = traversal.resource_path_tuple(child3)
print(f"\nresource_path_tuple(child) = {path_tuple3}")
print(f"Expected: ('', '0') or ('', 0)")

# Let's trace the issue
print("\n--- Tracing the issue ---")
from pyramid.location import lineage
for loc in lineage(child3):
    print(f"lineage node: {loc}, __name__={loc.__name__}")

print("\n" + "="*60)
print("=== Bug 4: Empty string as resource name ===")
print("Testing empty string '' as a literal resource name\n")

root4 = Resource(None)
child4 = root4.add_child('', Resource(''))

print(f"Root: {root4}")  
print(f"Child named '': {child4}")

path4 = traversal.resource_path(child4)
path_tuple4 = traversal.resource_path_tuple(child4)

print(f"\nresource_path(child) = '{path4}'")
print(f"resource_path_tuple(child) = {path_tuple4}")
print(f"Expected path to have the empty string child, but got: '{path4}'")

# Try round-trip
if path_tuple4 != ('',):  # If it's not just root
    try:
        found4 = traversal.find_resource(root4, path_tuple4)
        print(f"find_resource with tuple: {found4}")
        print(f"Is it the child? {found4 is child4}")
    except KeyError as e:
        print(f"find_resource failed: {e}")