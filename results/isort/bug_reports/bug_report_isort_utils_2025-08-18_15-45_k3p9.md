# Bug Report: isort.utils.Trie Overwrites Configs in Same Directory

**Target**: `isort.utils.Trie`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The Trie class in isort.utils incorrectly handles multiple configuration files in the same directory, keeping only the last inserted config and discarding previous ones.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import isort.utils
from pathlib import Path

path_component = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters="/\\:*?\"<>|"),
    min_size=1, 
    max_size=20
).filter(lambda s: s not in (".", "..", "~"))

def path_strategy():
    return st.lists(path_component, min_size=1, max_size=5).map(lambda parts: "/" + "/".join(parts))

config_data_strategy = st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.one_of(st.text(), st.integers(), st.booleans()),
    min_size=0,
    max_size=5
)

@given(
    configs=st.lists(
        st.tuples(path_strategy(), config_data_strategy),
        min_size=2,
        max_size=5,
        unique_by=lambda x: x[0]
    )
)
def test_trie_multiple_configs_hierarchy(configs):
    trie = isort.utils.Trie()
    
    for config_file, config_data in configs:
        trie.insert(config_file, config_data)
    
    for config_file, config_data in configs:
        search_path = str(Path(config_file).parent / "test.py")
        found_file, found_data = trie.search(search_path)
        
        matching_configs = []
        search_parts = Path(search_path).resolve().parts
        
        for cf, cd in configs:
            config_parts = Path(cf).parent.resolve().parts
            if len(config_parts) <= len(search_parts):
                if all(cp == sp for cp, sp in zip(config_parts, search_parts[:len(config_parts)])):
                    matching_configs.append((cf, cd, len(config_parts)))
        
        if matching_configs:
            expected = max(matching_configs, key=lambda x: x[2])
            assert found_file == expected[0]
            assert found_data == expected[1]
```

**Failing input**: `configs=[('/0', {}), ('/00', {})],`

## Reproducing the Bug

```python
import isort.utils

trie = isort.utils.Trie()

trie.insert('/0', {'config': 'first'})
trie.insert('/00', {'config': 'second'})

found_file, found_data = trie.search('/test.py')

print(f"Found: {found_file}")
print(f"Data: {found_data}")
```

## Why This Is A Bug

The Trie is designed to store configuration files and find the nearest config for any given file path. When multiple config files exist in the same directory (e.g., `.isort.cfg` and `setup.cfg` both in the root), the Trie should either:
1. Store all configs and have a deterministic way to choose between them, or
2. Document that only one config per directory is supported

Currently, it silently overwrites previous configs, which violates the expected behavior of a data structure meant to track multiple configuration files.

## Fix

The issue is in the `insert` method which unconditionally overwrites `config_info` at line 37:

```diff
def insert(self, config_file: str, config_data: Dict[str, Any]) -> None:
    resolved_config_path_as_tuple = Path(config_file).parent.resolve().parts
    
    temp = self.root
    
    for path in resolved_config_path_as_tuple:
        if path not in temp.nodes:
            temp.nodes[path] = TrieNode()
        
        temp = temp.nodes[path]
    
-   temp.config_info = (config_file, config_data)
+   # Store multiple configs per directory
+   if not hasattr(temp, 'configs'):
+       temp.configs = []
+   temp.configs.append((config_file, config_data))
+   # Keep the last one as default for backward compatibility
+   temp.config_info = (config_file, config_data)
```

This would require corresponding changes to the `search` method to handle multiple configs per node.