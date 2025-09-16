# Bug Report: TreeBuilderRegistry.lookup() Returns Wrong Builder When Feature Not Found

**Target**: `bs4.builder.TreeBuilderRegistry.lookup()`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

`TreeBuilderRegistry.lookup()` incorrectly returns builders that don't have all requested features when some features are not present in any registered builder.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from bs4.builder import TreeBuilder, TreeBuilderRegistry
import string

@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=10, alphabet=string.ascii_letters),
            st.lists(st.text(min_size=1, max_size=10, alphabet=string.ascii_letters), min_size=1)
        ),
        min_size=1,
        max_size=10
    ),
    st.lists(st.text(min_size=1, max_size=10, alphabet=string.ascii_letters), min_size=0, max_size=5)
)
def test_registry_lookup_feature_intersection(builders_with_features, query_features):
    registry = TreeBuilderRegistry()
    
    created_builders = []
    for i, (name, builder_features) in enumerate(builders_with_features):
        class MockBuilder(TreeBuilder):
            NAME = f"MockBuilder_{name}_{i}"
            features = builder_features
        created_builders.append(MockBuilder)
        registry.register(MockBuilder)
    
    result = registry.lookup(*query_features)
    
    if result is not None:
        for feature in query_features:
            assert feature in result.features, f"Returned builder missing feature: {feature}"
```

**Failing input**: `builders_with_features=[('A', ['A'])], query_features=['A', 'AA']`

## Reproducing the Bug

```python
from bs4.builder import TreeBuilder, TreeBuilderRegistry

registry = TreeBuilderRegistry()

class BuilderA(TreeBuilder):
    features = ['A']

registry.register(BuilderA)

result = registry.lookup('A', 'AA')
print(f"Result: {result}")
print(f"Result features: {result.features if result else None}")
```

## Why This Is A Bug

The docstring for `lookup()` states: "A TreeBuilder subclass, or None if there's no registered subclass with all the requested features." When requesting features ['A', 'AA'], the method should return None since no builder has both features. Instead, it returns BuilderA which only has feature 'A'.

## Fix

```diff
--- a/bs4/builder/__init__.py
+++ b/bs4/builder/__init__.py
@@ -133,6 +133,9 @@ class TreeBuilderRegistry(object):
             feature = feature_list.pop()
             we_have_the_feature = self.builders_for_feature.get(feature, [])
             if len(we_have_the_feature) > 0:
                 if candidates is None:
                     candidates = we_have_the_feature
                     candidate_set = set(candidates)
                 else:
                     # Eliminate any candidates that don't have this feature.
                     candidate_set = candidate_set.intersection(set(we_have_the_feature))
+            else:
+                # No builders have this feature, so no builder can have all features
+                return None
```