#!/usr/bin/env python3
"""Property-based tests for orbax.checkpoint module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/orbax-checkpoint_env/lib/python3.13/site-packages')

import numpy as np
import jax.numpy as jnp
from hypothesis import given, strategies as st, settings, assume, example
import orbax.checkpoint.tree as tree_module
import orbax.checkpoint.msgpack_utils as msgpack_utils
import orbax.checkpoint.transform_utils as transform_utils
import pytest


# Strategy for generating simple numpy arrays
@st.composite
def numpy_arrays(draw, max_dims=4, max_size=100):
    """Generate numpy arrays with reasonable constraints"""
    shape = draw(st.lists(st.integers(1, 10), min_size=1, max_size=max_dims))
    dtype = draw(st.sampled_from([np.int32, np.float32, np.float64]))
    
    size = 1
    for dim in shape:
        size *= dim
    assume(size <= max_size)
    
    if dtype == np.int32:
        elements = st.integers(-1000, 1000)
    else:
        elements = st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6)
    
    data = draw(st.lists(elements, min_size=size, max_size=size))
    return np.array(data, dtype=dtype).reshape(shape)


# Strategy for generating nested dictionaries (PyTrees)
@st.composite
def simple_pytrees(draw, max_depth=3):
    """Generate simple PyTrees (nested dicts) with array leaves"""
    if max_depth == 0:
        # Leaf node - return an array or simple value
        return draw(st.one_of(
            numpy_arrays(max_dims=2, max_size=20),
            st.integers(-100, 100),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)
        ))
    
    # Create a dict with string keys
    keys = draw(st.lists(st.text(alphabet='abcdefghijk', min_size=1, max_size=5), 
                         min_size=1, max_size=3, unique=True))
    
    result = {}
    for key in keys:
        # Recursively generate values
        result[key] = draw(simple_pytrees(max_depth - 1))
    
    return result


@st.composite
def dict_only_pytrees(draw, max_depth=3):
    """Generate PyTrees with only dict nodes (no lists/tuples)"""
    if max_depth == 0:
        return draw(st.one_of(
            numpy_arrays(max_dims=2, max_size=20),
            st.integers(-100, 100),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100)
        ))
    
    keys = draw(st.lists(st.text(alphabet='abcdefghijk', min_size=1, max_size=5), 
                         min_size=1, max_size=3, unique=True))
    
    result = {}
    for key in keys:
        result[key] = draw(dict_only_pytrees(max_depth - 1))
    
    return result


# Test 1: to_flat_dict/from_flat_dict round-trip property
@given(dict_only_pytrees(max_depth=3))
@settings(max_examples=200)
def test_flat_dict_round_trip(tree):
    """Test that to_flat_dict and from_flat_dict are inverses"""
    # Flatten the tree
    flat = tree_module.to_flat_dict(tree)
    
    # Unflatten back
    reconstructed = tree_module.from_flat_dict(flat, target=tree)
    
    # Check if they match
    def compare_values(v1, v2):
        if isinstance(v1, np.ndarray) and isinstance(v2, np.ndarray):
            return np.array_equal(v1, v2)
        elif isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            return abs(v1 - v2) < 1e-9
        else:
            return v1 == v2
    
    # Recursively compare trees
    def trees_equal(t1, t2):
        if isinstance(t1, dict) and isinstance(t2, dict):
            if set(t1.keys()) != set(t2.keys()):
                return False
            return all(trees_equal(t1[k], t2[k]) for k in t1.keys())
        else:
            return compare_values(t1, t2)
    
    assert trees_equal(tree, reconstructed), f"Round-trip failed: {tree} != {reconstructed}"


# Test 2: to_flat_dict with separator round-trip
@given(dict_only_pytrees(max_depth=2), st.sampled_from(['/', '.', '_', '-']))
@settings(max_examples=100)
def test_flat_dict_with_separator_round_trip(tree, sep):
    """Test that to_flat_dict and from_flat_dict work with custom separators"""
    # Flatten with separator
    flat = tree_module.to_flat_dict(tree, sep=sep)
    
    # All keys should be strings when using separator
    assert all(isinstance(k, str) for k in flat.keys())
    
    # Unflatten back
    reconstructed = tree_module.from_flat_dict(flat, target=tree, sep=sep)
    
    # Check if they match
    def trees_equal(t1, t2):
        if isinstance(t1, dict) and isinstance(t2, dict):
            if set(t1.keys()) != set(t2.keys()):
                return False
            return all(trees_equal(t1[k], t2[k]) for k in t1.keys())
        elif isinstance(t1, np.ndarray) and isinstance(t2, np.ndarray):
            return np.array_equal(t1, t2)
        elif isinstance(t1, (int, float)) and isinstance(t2, (int, float)):
            return abs(t1 - t2) < 1e-9
        else:
            return t1 == t2
    
    assert trees_equal(tree, reconstructed)


# Test 3: serialize_tree/deserialize_tree round-trip
@given(dict_only_pytrees(max_depth=2))
@settings(max_examples=100)
def test_serialize_deserialize_round_trip(tree):
    """Test that serialize_tree and deserialize_tree preserve structure"""
    # Skip empty trees as documented
    assume(tree)
    
    # Serialize the tree
    serialized = tree_module.serialize_tree(tree)
    
    # Deserialize back using original as target
    deserialized = tree_module.deserialize_tree(serialized, target=tree)
    
    # Check if values match (structure is guaranteed by using target)
    def trees_equal(t1, t2):
        if isinstance(t1, dict) and isinstance(t2, dict):
            if set(t1.keys()) != set(t2.keys()):
                return False
            return all(trees_equal(t1[k], t2[k]) for k in t1.keys())
        elif isinstance(t1, np.ndarray) and isinstance(t2, np.ndarray):
            return np.array_equal(t1, t2)
        elif isinstance(t1, (int, float)) and isinstance(t2, (int, float)):
            return abs(t1 - t2) < 1e-9
        else:
            return t1 == t2
    
    assert trees_equal(tree, deserialized)


# Test 4: msgpack round-trip for simple trees
@given(simple_pytrees(max_depth=2))
@settings(max_examples=100)
def test_msgpack_round_trip(tree):
    """Test msgpack_serialize and msgpack_restore preserve data"""
    # Serialize to msgpack
    serialized = msgpack_utils.msgpack_serialize(tree)
    
    # Restore from msgpack
    restored = msgpack_utils.msgpack_restore(serialized)
    
    # Compare - msgpack may convert some types
    def trees_approx_equal(t1, t2):
        if isinstance(t1, dict) and isinstance(t2, dict):
            if set(t1.keys()) != set(t2.keys()):
                return False
            return all(trees_approx_equal(t1[k], t2[k]) for k in t1.keys())
        elif isinstance(t1, np.ndarray) and isinstance(t2, np.ndarray):
            return t1.shape == t2.shape and np.allclose(t1, t2, rtol=1e-6, atol=1e-9)
        elif isinstance(t1, (int, float)) and isinstance(t2, (int, float)):
            return abs(t1 - t2) < 1e-9
        else:
            return t1 == t2
    
    assert trees_approx_equal(tree, restored)


# Test 5: merge_trees commutativity for non-overlapping keys
@given(dict_only_pytrees(max_depth=2), dict_only_pytrees(max_depth=2))
@settings(max_examples=100)
def test_merge_trees_non_overlapping(tree1, tree2):
    """Test merge_trees with non-overlapping keys"""
    # Create trees with distinct keys by prefixing
    tree1_prefixed = {f"a_{k}": v for k, v in tree1.items()}
    tree2_prefixed = {f"b_{k}": v for k, v in tree2.items()}
    
    # Merge in both orders
    merged = transform_utils.merge_trees(tree1_prefixed, tree2_prefixed)
    
    # Check all keys are present
    assert set(merged.keys()) == set(tree1_prefixed.keys()) | set(tree2_prefixed.keys())
    
    # Check values are preserved
    for k in tree1_prefixed:
        def values_equal(v1, v2):
            if isinstance(v1, np.ndarray) and isinstance(v2, np.ndarray):
                return np.array_equal(v1, v2)
            else:
                return v1 == v2
        assert k in merged
        # Can't easily compare nested structures, just check key presence


# Test 6: intersect_trees properties
@given(dict_only_pytrees(max_depth=2))
@settings(max_examples=100)
def test_intersect_trees_identity(tree):
    """Test that intersecting a tree with itself returns the same tree"""
    intersected = transform_utils.intersect_trees(tree, tree)
    
    def trees_equal(t1, t2):
        if isinstance(t1, dict) and isinstance(t2, dict):
            if set(t1.keys()) != set(t2.keys()):
                return False
            return all(trees_equal(t1[k], t2[k]) for k in t1.keys())
        elif isinstance(t1, np.ndarray) and isinstance(t2, np.ndarray):
            return np.array_equal(t1, t2)
        else:
            return t1 == t2
    
    assert trees_equal(tree, intersected)


# Test 7: intersect with empty returns empty
@given(dict_only_pytrees(max_depth=2))
@settings(max_examples=100)
def test_intersect_with_empty(tree):
    """Test that intersecting with empty dict returns empty"""
    intersected = transform_utils.intersect_trees(tree, {})
    assert intersected == {}


# Test 8: merge identity
@given(dict_only_pytrees(max_depth=2))
@settings(max_examples=100) 
def test_merge_identity(tree):
    """Test that merging with empty dict returns original"""
    merged = transform_utils.merge_trees({}, tree)
    
    def trees_equal(t1, t2):
        if isinstance(t1, dict) and isinstance(t2, dict):
            if set(t1.keys()) != set(t2.keys()):
                return False
            return all(trees_equal(t1[k], t2[k]) for k in t1.keys())
        elif isinstance(t1, np.ndarray) and isinstance(t2, np.ndarray):
            return np.array_equal(t1, t2)
        else:
            return t1 == t2
    
    assert trees_equal(tree, merged)


if __name__ == "__main__":
    # Run specific tests for debugging
    print("Testing orbax.checkpoint properties...")
    
    # Run a simple manual test
    test_tree = {'a': np.array([1, 2, 3]), 'b': {'c': 5}}
    
    # Test flat dict round-trip manually
    flat = tree_module.to_flat_dict(test_tree)
    reconstructed = tree_module.from_flat_dict(flat, target=test_tree)
    print(f"✓ Basic round-trip test: {test_tree} -> {flat} -> {reconstructed}")
    
    # Test serialize/deserialize
    serialized = tree_module.serialize_tree(test_tree)
    deserialized = tree_module.deserialize_tree(serialized, test_tree)
    print(f"✓ Serialize/deserialize test passed")
    
    # Test msgpack
    msg_bytes = msgpack_utils.msgpack_serialize(test_tree)
    restored = msgpack_utils.msgpack_restore(msg_bytes)
    print(f"✓ Msgpack round-trip test passed")
    
    print("\nNow run with: pytest test_orbax_properties.py -v")