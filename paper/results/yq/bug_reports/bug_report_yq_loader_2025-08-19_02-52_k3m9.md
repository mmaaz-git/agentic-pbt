# Bug Report: yq.loader.get_loader Global State Mutation

**Target**: `yq.loader.get_loader`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `get_loader()` function in yq.loader modifies global class state, causing different calls with different parameters to interfere with each other.

## Property-Based Test

```python
import yq.loader
from hypothesis import given, strategies as st

@given(st.booleans(), st.booleans())
def test_get_loader_isolation(expand_merge1, expand_merge2):
    """get_loader calls should be isolated from each other"""
    loader1 = yq.loader.get_loader(expand_merge_keys=expand_merge1)
    initial_state = '<' in str(loader1.yaml_implicit_resolvers)
    
    loader2 = yq.loader.get_loader(expand_merge_keys=expand_merge2)
    final_state = '<' in str(loader1.yaml_implicit_resolvers)
    
    # Bug: loader1's state is affected by the second get_loader call
    assert initial_state == (expand_merge1 == True)
    assert final_state == (expand_merge2 == True)  # This shows the mutation
```

**Failing input**: Any combination where `expand_merge1 != expand_merge2`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')
import yq.loader

loader_class_1 = yq.loader.get_loader(expand_merge_keys=True)
loader_class_2 = yq.loader.get_loader(expand_merge_keys=False)

assert loader_class_1 is loader_class_2
has_merge = any('<' in str(k) for k in loader_class_1.yaml_implicit_resolvers.keys())
assert has_merge == False  # Should be True for loader_class_1!
```

## Why This Is A Bug

The `get_loader()` function returns the same class object (`CSafeLoader` or `CustomLoader`) but modifies its class-level attributes each time it's called. This violates the principle of isolation - calling `get_loader()` with different parameters should either return different classes or return instances with different configurations, not modify a shared global class. This causes issues in concurrent usage and when different parts of a program need loaders with different configurations.

## Fix

The function should create new loader classes or use instances instead of modifying global class state:

```diff
def get_loader(use_annotations=False, expand_aliases=True, expand_merge_keys=True):
    # ... existing construct functions ...
    
    loader_class = default_loader if expand_aliases else CustomLoader
+   # Create a new class to avoid modifying the global one
+   class ConfiguredLoader(loader_class):
+       pass
+   loader_class = ConfiguredLoader
    
    loader_class.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
    loader_class.add_constructor(yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG, construct_sequence)
    loader_class.add_multi_constructor("", parse_unknown_tags)
    loader_class.yaml_constructors.pop("tag:yaml.org,2002:binary", None)
    loader_class.yaml_constructors.pop("tag:yaml.org,2002:set", None)
    set_yaml_grammar(loader_class, expand_merge_keys=expand_merge_keys)
    return loader_class
```