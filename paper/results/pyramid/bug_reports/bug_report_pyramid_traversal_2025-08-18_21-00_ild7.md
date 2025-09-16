# Bug Report: pyramid.traversal Round-Trip Property Violation

**Target**: `pyramid.traversal`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The documented round-trip property between `resource_path_tuple()` and `find_resource()` is violated when resources have certain special names like `'..'`, `0`, or empty string, causing `find_resource()` to return the wrong resource or fail entirely.

## Property-Based Test

```python
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

@given(st.one_of(
    st.just('..'),
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
    
    path_tuple = traversal.resource_path_tuple(child)
    found = traversal.find_resource(root, path_tuple)
    
    assert found is child, f"Round-trip failed for name={repr(name)}"
```

**Failing input**: Multiple failing cases: `'..'`, `0`, `''`, `'../etc/passwd'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')
import pyramid.traversal as traversal

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

# Bug 1: '..' as literal resource name
root = Resource(None)
child_dotdot = root.add_child('..', Resource('..'))
path_tuple = traversal.resource_path_tuple(child_dotdot)
found = traversal.find_resource(root, path_tuple)
print(f"'..' bug: Expected child, got {found is child_dotdot}")  # False

# Bug 2: Numeric name (0)
child_zero = Resource(0, root)
root._children['0'] = child_zero
child_zero.__parent__ = root
path = traversal.resource_path(child_zero)
print(f"Numeric bug: Path is '{path}' instead of '/0'")  # '/'

# Bug 3: Empty string name
child_empty = root.add_child('', Resource(''))
path_tuple = traversal.resource_path_tuple(child_empty)
found = traversal.find_resource(root, path_tuple)
print(f"Empty string bug: Expected child, got {found is child_empty}")  # False
```

## Why This Is A Bug

The documentation explicitly states that `find_resource` and `resource_path_tuple` are "logical inverses" (lines 44-47, 333-334). This invariant is violated in three ways:

1. **Falsy `__name__` values**: In `_resource_path_list` (line 366), the code uses `loc.__name__ or ''`, which converts falsy values like `0` to empty string.

2. **Special path components**: In `split_path_info` (lines 518-520), `'..'` is always treated as parent navigation, even when it's a literal resource name.

3. **Path normalization**: Empty segments are removed during path processing, preventing empty string from being a valid resource name.

## Fix

```diff
--- a/pyramid/traversal.py
+++ b/pyramid/traversal.py
@@ -363,7 +363,10 @@ model_path_tuple = resource_path_tuple  # b/w compat (forever)
 def _resource_path_list(resource, *elements):
     """Implementation detail shared by resource_path and
     resource_path_tuple"""
-    path = [loc.__name__ or '' for loc in lineage(resource)]
+    path = []
+    for loc in lineage(resource):
+        name = loc.__name__ if loc.__name__ is not None else ''
+        path.append(name)
     path.reverse()
     path.extend(elements)
     return path
```

Note: A complete fix would also require changes to `split_path_info` to handle literal `'..'` and `'.'` names when used with tuples, but this is more complex as it would need to distinguish between path navigation and literal names.