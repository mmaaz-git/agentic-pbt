# Proposed Properties for orbax.checkpoint

Based on the code analysis, here are evidence-based properties:

## 1. Tree Serialization Round-trip Properties
**Evidence**: `serialize_tree` and `deserialize_tree` functions in utils.py
- Property: `deserialize_tree(serialize_tree(tree), tree) == tree`
- The code explicitly provides these functions for serialization/deserialization

## 2. Flat Dict Conversion Round-trip
**Evidence**: `to_flat_dict` and `from_flat_dict` functions in utils.py  
- Property: `from_flat_dict(to_flat_dict(tree), tree) == tree`
- These functions are designed to convert between nested and flat representations

## 3. merge_trees Properties
**Evidence**: `merge_trees` function in transform_utils.py (line 295-313)
- Property 1: `merge_trees(a) == a` (idempotence with single tree)
- Property 2: `merge_trees(a, {}) == a` (identity with empty dict)
- Property 3: Last tree takes precedence for overlapping keys

## 4. intersect_trees Properties  
**Evidence**: `intersect_trees` function in transform_utils.py (line 316-336)
- Property: Only keys present in all trees are kept
- Property: Result contains subset of keys from each input tree

## 5. Tree Path Utilities
**Evidence**: `tuple_path_from_keypath` and related functions
- Property: Path conversion functions maintain structure

## 6. Empty Node Handling
**Evidence**: Multiple functions handle `keep_empty_nodes` parameter
- Property: Empty nodes are consistently handled based on the flag

## Priority Properties to Test:
1. serialize_tree/deserialize_tree round-trip (HIGH - core functionality)
2. to_flat_dict/from_flat_dict round-trip (HIGH - core functionality) 
3. merge_trees properties (MEDIUM - common operation)
4. intersect_trees properties (MEDIUM - common operation)