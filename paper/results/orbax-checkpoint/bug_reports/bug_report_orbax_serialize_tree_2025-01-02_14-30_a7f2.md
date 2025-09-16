# Bug Report: orbax.checkpoint.tree.serialize_tree Empty Container Handling

**Target**: `orbax.checkpoint.tree.serialize_tree`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-01-02

## Summary

The `serialize_tree` function crashes with AssertionError or ValueError when serializing PyTrees containing empty containers within lists, particularly when empty containers appear before non-empty elements.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import orbax.checkpoint.tree as tree_module

@st.composite
def pytrees_with_sequences(draw, max_depth=3):
    if max_depth == 0:
        return draw(st.one_of(
            st.integers(-100, 100),
            st.lists(st.integers(-10, 10), min_size=0, max_size=3)
        ))
    
    container_type = draw(st.sampled_from(['dict', 'list']))
    
    if container_type == 'dict':
        keys = draw(st.lists(st.text(alphabet='abcde', min_size=1, max_size=3), 
                             min_size=1, max_size=3, unique=True))
        result = {}
        for key in keys:
            result[key] = draw(pytrees_with_sequences(max_depth - 1))
        return result
    else:
        size = draw(st.integers(1, 3))
        return [draw(pytrees_with_sequences(max_depth - 1)) for _ in range(size)]

@given(pytrees_with_sequences(max_depth=2))
@settings(max_examples=200)
def test_serialize_tree_with_empty_containers(tree):
    serialized = tree_module.serialize_tree(tree)
    assert serialized is not None
```

**Failing input**: `[[[], 0]]`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/orbax-checkpoint_env/lib/python3.13/site-packages')
import orbax.checkpoint.tree as tree_module

# Bug Case 1: List with empty list followed by value
tree1 = [[[], 0]]
result = tree_module.serialize_tree(tree1)  # AssertionError

# Bug Case 2: Nested empty lists
tree2 = [[[]]]
result = tree_module.serialize_tree(tree2)  # ValueError: Unable to uniquely reconstruct tree

# Bug Case 3: Dict with empty dict value
tree3 = {'a': {}}
result = tree_module.serialize_tree(tree3, keep_empty_nodes=False)  # ValueError
```

## Why This Is A Bug

The `serialize_tree` function is documented to "transform a PyTree to a serializable format" but fails on valid PyTree structures containing empty containers. Empty lists and dicts are legitimate Python data structures that should be serializable. The function handles some empty container cases (like `[[1], []]`) but fails on others (like `[[], [1]]`), showing inconsistent behavior.

## Fix

```diff
--- a/orbax/checkpoint/_src/tree/utils.py
+++ b/orbax/checkpoint/_src/tree/utils.py
@@ -116,10 +116,14 @@
 
 def _extend_list(ls, idx, nextvalue):
-  assert idx <= len(ls)
-  if idx == len(ls):
-    ls.append(nextvalue)
-  return ls
+  # Handle sparse indices by filling gaps with None
+  while len(ls) <= idx:
+    ls.append(None)
+  ls[idx] = nextvalue
+  return ls
```

The issue occurs because the current implementation assumes list indices will be consecutive, but when empty containers are filtered out during flattening, indices can become non-consecutive. The fix ensures the list is extended to accommodate any valid index.