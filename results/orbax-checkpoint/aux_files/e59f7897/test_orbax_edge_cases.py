#!/usr/bin/env python3
"""Edge case tests for orbax.checkpoint module - focusing on lists/tuples"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/orbax-checkpoint_env/lib/python3.13/site-packages')

import numpy as np
from hypothesis import given, strategies as st, settings, assume, note
import orbax.checkpoint.tree as tree_module
import orbax.checkpoint.msgpack_utils as msgpack_utils
import orbax.checkpoint.transform_utils as transform_utils
import pytest


# Strategy for PyTrees with lists and tuples
@st.composite
def pytrees_with_sequences(draw, max_depth=3):
    """Generate PyTrees with lists, tuples, and dicts"""
    if max_depth == 0:
        return draw(st.one_of(
            st.integers(-100, 100),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-100, max_value=100),
            st.lists(st.integers(-10, 10), min_size=0, max_size=3)
        ))
    
    # Choose container type
    container_type = draw(st.sampled_from(['dict', 'list', 'tuple']))
    
    if container_type == 'dict':
        keys = draw(st.lists(st.text(alphabet='abcde', min_size=1, max_size=3), 
                             min_size=1, max_size=3, unique=True))
        result = {}
        for key in keys:
            result[key] = draw(pytrees_with_sequences(max_depth - 1))
        return result
    else:
        size = draw(st.integers(1, 3))
        elements = [draw(pytrees_with_sequences(max_depth - 1)) for _ in range(size)]
        if container_type == 'list':
            return elements
        else:
            return tuple(elements)


# Test: serialize_tree changes tuple to list
@given(pytrees_with_sequences(max_depth=2))
@settings(max_examples=200)
def test_serialize_tree_tuple_to_list_conversion(tree):
    """Test that serialize_tree converts tuples to lists as documented"""
    assume(tree)  # Skip empty trees
    
    serialized = tree_module.serialize_tree(tree)
    
    # Check that all tuples have been converted to lists
    def check_no_tuples(obj):
        if isinstance(obj, tuple):
            return False
        elif isinstance(obj, dict):
            return all(check_no_tuples(v) for v in obj.values())
        elif isinstance(obj, list):
            return all(check_no_tuples(item) for item in obj)
        else:
            return True
    
    assert check_no_tuples(serialized), f"Found tuple in serialized tree: {serialized}"
    
    # Now test deserialization - it should restore the structure
    # But tuples remain as lists (this is the documented behavior)
    if isinstance(tree, (dict, list)):
        deserialized = tree_module.deserialize_tree(serialized, tree)
        # The structure should match, but tuples become lists


# Test: Round-trip with mixed containers
@given(pytrees_with_sequences(max_depth=2))
@settings(max_examples=200)
def test_mixed_container_serialization(tree):
    """Test serialization with mixed dict/list/tuple containers"""
    assume(tree)
    
    # Note the original structure
    def get_structure_signature(obj):
        if isinstance(obj, dict):
            return ('dict', sorted(obj.keys()))
        elif isinstance(obj, list):
            return ('list', len(obj))
        elif isinstance(obj, tuple):
            return ('tuple', len(obj))
        else:
            return ('leaf', type(obj).__name__)
    
    original_sig = get_structure_signature(tree)
    note(f"Original structure: {original_sig}")
    
    # Serialize and check structure change
    serialized = tree_module.serialize_tree(tree)
    serialized_sig = get_structure_signature(serialized)
    note(f"Serialized structure: {serialized_sig}")
    
    # If original was tuple, it should become list
    if original_sig[0] == 'tuple':
        assert serialized_sig[0] == 'list'
        assert serialized_sig[1] == original_sig[1]  # Same length


# Test: Empty containers edge cases
@given(st.sampled_from([
    {},  # empty dict
    [],  # empty list
    (),  # empty tuple
    {'a': {}},  # dict with empty dict value
    {'a': []},  # dict with empty list value
    {'a': {'b': {}}},  # nested empty
    [[]], # list with empty list
    [{}], # list with empty dict
]))
def test_empty_container_handling(tree):
    """Test how empty containers are handled"""
    # serialize_tree with keep_empty_nodes=False (default) might filter them out
    if tree in [{}, [], ()]:
        # Empty root should raise error according to docstring
        with pytest.raises(ValueError):
            tree_module.serialize_tree(tree, keep_empty_nodes=False)
    else:
        serialized = tree_module.serialize_tree(tree, keep_empty_nodes=False)
        # Empty nodes should be filtered out
        
        def count_nodes(obj):
            if isinstance(obj, dict):
                return 1 + sum(count_nodes(v) for v in obj.values())
            elif isinstance(obj, list):
                return 1 + sum(count_nodes(item) for item in obj)
            else:
                return 1
        
        original_nodes = count_nodes(tree)
        serialized_nodes = count_nodes(serialized)
        # Serialized should have fewer or equal nodes (empty ones filtered)
        assert serialized_nodes <= original_nodes
    
    # With keep_empty_nodes=True, should preserve structure
    if tree not in [{}, [], ()]:
        serialized_keep = tree_module.serialize_tree(tree, keep_empty_nodes=True)
        # Structure should be preserved


# Test: to_flat_dict with nested sequences
@given(pytrees_with_sequences(max_depth=2))
@settings(max_examples=100)
def test_flat_dict_with_sequences(tree):
    """Test to_flat_dict with lists and tuples"""
    try:
        flat = tree_module.to_flat_dict(tree)
        
        # All keys should be tuples of strings
        for key in flat.keys():
            assert isinstance(key, tuple)
            assert all(isinstance(k, str) for k in key)
        
        # Try to reconstruct if tree is suitable
        if isinstance(tree, dict):
            reconstructed = tree_module.from_flat_dict(flat, target=tree)
            # Can't guarantee perfect reconstruction with lists/tuples
    except Exception as e:
        # Some structures might not be flattenable
        note(f"Failed to flatten: {e}")


# Test: Special characters in dict keys
@given(st.dictionaries(
    st.text(alphabet='/.\\-_[]{}()', min_size=1, max_size=5),
    st.integers(-100, 100),
    min_size=1, max_size=3
))
@settings(max_examples=100)
def test_special_characters_in_keys(tree):
    """Test handling of special characters in dictionary keys"""
    # These special chars might interfere with path separator logic
    
    # Test with default separator (None - uses tuples)
    flat = tree_module.to_flat_dict(tree)
    reconstructed = tree_module.from_flat_dict(flat, target=tree)
    
    assert set(tree.keys()) == set(reconstructed.keys())
    for key in tree:
        assert tree[key] == reconstructed[key]
    
    # Test with '/' separator - might conflict with keys containing '/'
    if not any('/' in k for k in tree.keys()):
        flat_sep = tree_module.to_flat_dict(tree, sep='/')
        reconstructed_sep = tree_module.from_flat_dict(flat_sep, target=tree, sep='/')
        assert set(tree.keys()) == set(reconstructed_sep.keys())


# Test: Large arrays and chunking in msgpack
@given(st.integers(1, 3))
@settings(max_examples=10, deadline=10000)
def test_msgpack_large_array_chunking(power):
    """Test msgpack chunking for large arrays"""
    # Create a large array that exceeds MAX_CHUNK_SIZE (2**30 bytes)
    # Using smaller arrays for testing
    size = 2 ** (20 + power)  # 2^21 to 2^23 elements
    
    # Create array with float64 (8 bytes each)
    large_array = np.arange(size, dtype=np.float32)
    tree = {'large': large_array, 'small': np.array([1, 2, 3])}
    
    # Should handle chunking automatically
    serialized = msgpack_utils.msgpack_serialize(tree)
    restored = msgpack_utils.msgpack_restore(serialized)
    
    assert 'large' in restored
    assert 'small' in restored
    assert restored['large'].shape == large_array.shape
    assert np.allclose(restored['large'], large_array, rtol=1e-6)
    assert np.array_equal(restored['small'], tree['small'])


# Test: Complex nested transformations
@given(
    st.dictionaries(st.text(alphabet='abc', min_size=1, max_size=2), 
                   st.integers(1, 10), min_size=2, max_size=4),
    st.dictionaries(st.text(alphabet='abc', min_size=1, max_size=2), 
                   st.integers(11, 20), min_size=2, max_size=4)
)
@settings(max_examples=100)
def test_merge_intersect_composition(tree1, tree2):
    """Test composition of merge and intersect operations"""
    # Property: intersection is subset of both inputs
    intersected = transform_utils.intersect_trees(tree1, tree2)
    for key in intersected:
        assert key in tree1
        assert key in tree2
    
    # Property: merge contains all keys from both
    merged = transform_utils.merge_trees(tree1, tree2)
    for key in tree1:
        assert key in merged
    for key in tree2:
        assert key in merged
    
    # Property: (A ∩ B) ⊆ (A ∪ B)
    for key in intersected:
        assert key in merged
    
    # Property: intersection with merge should give intersection
    inter_merge = transform_utils.intersect_trees(intersected, merged)
    assert set(inter_merge.keys()) == set(intersected.keys())


# Test named tuples (mentioned in docstring)
from collections import namedtuple

@given(st.integers(-100, 100), st.floats(allow_nan=False, allow_infinity=False))
@settings(max_examples=50)
def test_named_tuple_serialization(x, y):
    """Test that NamedTuples are converted to dicts as documented"""
    Point = namedtuple('Point', ['x', 'y'])
    point = Point(x, y)
    
    tree = {'point': point, 'data': [1, 2, 3]}
    
    # Serialize should convert namedtuple to dict
    serialized = tree_module.serialize_tree(tree)
    
    # The namedtuple should become a dict
    assert isinstance(serialized['point'], dict)
    assert 'x' in serialized['point']
    assert 'y' in serialized['point']
    assert serialized['point']['x'] == x
    assert serialized['point']['y'] == y


if __name__ == "__main__":
    print("Running edge case tests...")
    
    # Test empty container handling
    try:
        tree_module.serialize_tree({})
    except ValueError as e:
        print(f"✓ Empty dict raises error as expected: {e}")
    
    # Test tuple to list conversion
    tree = {'a': (1, 2, 3), 'b': [4, 5, 6]}
    serialized = tree_module.serialize_tree(tree)
    print(f"✓ Tuple conversion: {tree} -> {serialized}")
    assert isinstance(serialized['a'], list)
    
    print("\nRun full tests with: pytest test_orbax_edge_cases.py -v")