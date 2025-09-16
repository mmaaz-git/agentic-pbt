#!/usr/bin/env python3
"""Property-based tests for orbax.checkpoint using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/orbax-checkpoint_env/lib/python3.13/site-packages')

import pytest
from hypothesis import given, strategies as st, settings, assume
import orbax.checkpoint.tree as tree
import orbax.checkpoint.transform_utils as transform_utils


# Strategies for generating nested dictionaries (PyTrees)
simple_values = st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=0, max_size=10),
    st.booleans(),
)

def nested_dict_strategy(max_depth=3):
    """Generate nested dictionaries with controlled depth."""
    return st.recursive(
        simple_values,
        lambda children: st.dictionaries(
            st.text(min_size=1, max_size=5, alphabet='abcdef'),
            children,
            min_size=0,
            max_size=3
        ),
        max_leaves=10
    )

def non_empty_nested_dict_strategy(max_depth=3):
    """Generate non-empty nested dictionaries."""
    return st.recursive(
        simple_values,
        lambda children: st.dictionaries(
            st.text(min_size=1, max_size=5, alphabet='abcdef'), 
            children,
            min_size=1,
            max_size=3
        ),
        max_leaves=10
    )

# Test 1: serialize_tree/deserialize_tree round-trip
@given(nested_dict_strategy())
@settings(max_examples=100)
def test_serialize_deserialize_round_trip(tree_data):
    """Test that serialize followed by deserialize returns the original tree."""
    try:
        # Serialize the tree
        serialized = tree.serialize_tree(tree_data, keep_empty_nodes=False)
        
        # Deserialize back using the original as target
        deserialized = tree.deserialize_tree(serialized, tree_data, keep_empty_nodes=False)
        
        # Check round-trip property
        assert deserialized == tree_data, f"Round-trip failed: {tree_data} != {deserialized}"
    except ValueError as e:
        # Empty trees raise ValueError - this is expected behavior
        if "empty flattened list" in str(e) and not tree_data:
            pass  # Expected for empty trees
        else:
            raise

@given(nested_dict_strategy())
@settings(max_examples=100)
def test_serialize_deserialize_with_empty_nodes(tree_data):
    """Test serialize/deserialize with keep_empty_nodes=True."""
    try:
        serialized = tree.serialize_tree(tree_data, keep_empty_nodes=True)
        deserialized = tree.deserialize_tree(serialized, tree_data, keep_empty_nodes=True)
        assert deserialized == tree_data
    except ValueError as e:
        if "empty flattened list" in str(e) and not tree_data:
            pass  # Expected for completely empty trees
        else:
            raise

# Test 2: to_flat_dict/from_flat_dict round-trip
@given(nested_dict_strategy())
@settings(max_examples=100)
def test_flat_dict_round_trip(tree_data):
    """Test that to_flat_dict followed by from_flat_dict returns the original."""
    # Convert to flat dict
    flat = tree.to_flat_dict(tree_data, keep_empty_nodes=False)
    
    # Convert back using original as target
    reconstructed = tree.from_flat_dict(flat, target=tree_data)
    
    # Check round-trip property
    assert reconstructed == tree_data, f"Flat dict round-trip failed"

@given(nested_dict_strategy())
@settings(max_examples=100)
def test_flat_dict_with_separator(tree_data):
    """Test flat dict conversion with separator."""
    # Use '/' as separator
    flat = tree.to_flat_dict(tree_data, sep='/', keep_empty_nodes=False)
    reconstructed = tree.from_flat_dict(flat, target=tree_data, sep='/')
    assert reconstructed == tree_data

# Test 3: merge_trees properties
@given(nested_dict_strategy())
@settings(max_examples=100)
def test_merge_single_tree(tree_data):
    """Test that merging a single tree returns the same tree."""
    merged = transform_utils.merge_trees(tree_data)
    assert merged == tree_data, "merge_trees with single tree should be idempotent"

@given(nested_dict_strategy())
@settings(max_examples=100)
def test_merge_with_empty(tree_data):
    """Test that merging with empty dict returns original."""
    merged = transform_utils.merge_trees(tree_data, {})
    assert merged == tree_data, "merge_trees with empty dict should return original"

@given(
    non_empty_nested_dict_strategy(),
    non_empty_nested_dict_strategy()
)
@settings(max_examples=100)
def test_merge_trees_precedence(tree1, tree2):
    """Test that last tree takes precedence in merge_trees."""
    merged = transform_utils.merge_trees(tree1, tree2)
    
    # For any key in tree2, the merged value should match tree2's value
    flat_tree2 = tree.to_flat_dict(tree2)
    flat_merged = tree.to_flat_dict(merged)
    
    for key, value in flat_tree2.items():
        assert key in flat_merged, f"Key {key} from tree2 not in merged result"
        assert flat_merged[key] == value, f"tree2 value should take precedence for key {key}"

# Test 4: intersect_trees properties
@given(
    nested_dict_strategy(),
    nested_dict_strategy()
)
@settings(max_examples=100)
def test_intersect_trees_subset(tree1, tree2):
    """Test that intersection contains only common keys."""
    intersected = transform_utils.intersect_trees(tree1, tree2)
    
    flat1 = tree.to_flat_dict(tree1)
    flat2 = tree.to_flat_dict(tree2) 
    flat_intersected = tree.to_flat_dict(intersected)
    
    # All keys in intersection should be in both original trees
    for key in flat_intersected:
        assert key in flat1, f"Intersected key {key} not in tree1"
        assert key in flat2, f"Intersected key {key} not in tree2"
    
    # All common keys should be in intersection
    common_keys = set(flat1.keys()) & set(flat2.keys())
    assert set(flat_intersected.keys()) == common_keys

@given(nested_dict_strategy())
@settings(max_examples=100)
def test_intersect_with_self(tree_data):
    """Test that intersecting a tree with itself returns the same tree."""
    intersected = transform_utils.intersect_trees(tree_data, tree_data)
    assert intersected == tree_data, "Intersecting tree with itself should return same tree"

# Test 5: Edge cases and additional properties
@given(st.lists(nested_dict_strategy(), min_size=1, max_size=5))
@settings(max_examples=50)
def test_merge_associative(trees):
    """Test that merge is associative (approximately)."""
    if len(trees) < 3:
        assume(len(trees) >= 3)
    
    # Merge first two, then third
    merge_12_3 = transform_utils.merge_trees(
        transform_utils.merge_trees(trees[0], trees[1]), 
        trees[2]
    )
    
    # Merge first, then last two
    merge_1_23 = transform_utils.merge_trees(
        trees[0],
        transform_utils.merge_trees(trees[1], trees[2])
    )
    
    # Should be the same
    assert merge_12_3 == merge_1_23, "merge_trees should be associative"

if __name__ == "__main__":
    # Run a quick test of each property
    print("Running property-based tests for orbax.checkpoint...")
    
    # Test each function briefly
    test_cases = [
        (test_serialize_deserialize_round_trip, {'a': 1, 'b': {'c': 2}}),
        (test_flat_dict_round_trip, {'x': 5, 'y': {'z': 10}}),
        (test_merge_single_tree, {'foo': 'bar'}),
        (test_intersect_with_self, {'p': 1, 'q': 2}),
    ]
    
    for test_fn, test_input in test_cases:
        try:
            test_fn(test_input)
            print(f"✓ {test_fn.__name__} passed with sample input")
        except Exception as e:
            print(f"✗ {test_fn.__name__} failed: {e}")
    
    print("\nNow running full Hypothesis test suite...")
    pytest.main([__file__, "-v", "--tb=short"])