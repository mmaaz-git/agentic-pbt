#!/usr/bin/env python3
"""Property-based tests for optax using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import jax
import jax.numpy as jnp
import numpy as np
from hypothesis import given, strategies as st, settings, assume
import optax
from optax import tree
import math

# Strategy for generating JAX arrays
@st.composite
def jax_arrays(draw, shape=(3,), dtype=jnp.float32):
    """Generate JAX arrays with reasonable values."""
    # Use reasonable bounds to avoid numerical issues
    elements = st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
    # Convert numpy shape to regular int
    shape_prod = int(np.prod(shape))
    data = draw(st.lists(elements, min_size=shape_prod, max_size=shape_prod))
    arr = np.array(data[:shape_prod]).reshape(shape)
    return jnp.array(arr, dtype=dtype)

@st.composite
def simple_trees(draw):
    """Generate simple pytrees for testing."""
    # Generate a simple tree structure with arrays
    arr1 = draw(jax_arrays(shape=(2,)))
    arr2 = draw(jax_arrays(shape=(3,)))
    scalar = draw(st.floats(min_value=-100, max_value=100, allow_nan=False))
    
    tree = {
        'a': arr1,
        'b': {'c': arr2, 'd': jnp.array(scalar)}
    }
    return tree

@st.composite
def matching_tree_pairs(draw):
    """Generate pairs of trees with matching structure."""
    # Generate matching structure trees
    shape1 = draw(st.tuples(st.integers(1, 5)))
    shape2 = draw(st.tuples(st.integers(1, 5)))
    
    tree1 = {
        'a': draw(jax_arrays(shape=shape1)),
        'b': draw(jax_arrays(shape=shape2))
    }
    
    tree2 = {
        'a': draw(jax_arrays(shape=shape1)),
        'b': draw(jax_arrays(shape=shape2))
    }
    
    return tree1, tree2

@st.composite
def matching_tree_triples(draw):
    """Generate triples of trees with matching structure."""
    shape = draw(st.tuples(st.integers(1, 3)))
    
    tree1 = {'x': draw(jax_arrays(shape=shape))}
    tree2 = {'x': draw(jax_arrays(shape=shape))}
    tree3 = {'x': draw(jax_arrays(shape=shape))}
    
    return tree1, tree2, tree3

def trees_close(tree1, tree2, rtol=1e-5, atol=1e-8):
    """Check if two trees are approximately equal."""
    def close(a, b):
        try:
            return bool(jnp.allclose(a, b, rtol=rtol, atol=atol))
        except:
            return False
    
    try:
        results = jax.tree.map(close, tree1, tree2)
        leaves = jax.tree.leaves(results)
        if not leaves:  # Empty tree
            return True
        return all(leaves)
    except:
        return False

# Test 1: tree_add commutativity
@given(matching_tree_pairs())
@settings(max_examples=100)
def test_tree_add_commutative(tree_pair):
    """Test that tree_add is commutative: add(x, y) == add(y, x)"""
    tree1, tree2 = tree_pair
    
    result1 = tree.add(tree1, tree2)
    result2 = tree.add(tree2, tree1)
    
    assert trees_close(result1, result2), \
        f"tree_add not commutative for trees"

# Test 2: tree_add associativity 
@given(matching_tree_triples())
@settings(max_examples=100)
def test_tree_add_associative(tree_triple):
    """Test that tree_add is associative: add(add(x, y), z) == add(x, add(y, z))"""
    tree1, tree2, tree3 = tree_triple
    
    # Left association
    result1 = tree.add(tree.add(tree1, tree2), tree3)
    # Right association
    result2 = tree.add(tree1, tree.add(tree2, tree3))
    
    assert trees_close(result1, result2, rtol=1e-4, atol=1e-7), \
        f"tree_add not associative"

# Test 3: tree_add_scale property
@given(matching_tree_pairs(), st.floats(min_value=-100, max_value=100, allow_nan=False))
@settings(max_examples=100)
def test_tree_add_scale_equivalence(tree_pair, scalar):
    """Test that add_scale(x, s, y) == add(x, tree_scale(s, y))"""
    tree1, tree2 = tree_pair
    
    # Using add_scale
    result1 = tree.add_scale(tree1, scalar, tree2)
    
    # Using add with explicit scale
    scaled_tree2 = jax.tree.map(lambda x: scalar * x, tree2)
    result2 = tree.add(tree1, scaled_tree2)
    
    assert trees_close(result1, result2, rtol=1e-4, atol=1e-7), \
        f"add_scale not equivalent to add + scale"

# Test 4: Division and multiplication inverse
@given(matching_tree_pairs())
@settings(max_examples=100)
def test_div_mul_inverse(tree_pair):
    """Test that div(mul(x, y), y) ≈ x for non-zero y"""
    tree1, tree2 = tree_pair
    
    # Ensure tree2 has no zeros to avoid division by zero
    def ensure_nonzero(x):
        return jnp.where(jnp.abs(x) < 1e-10, 1e-10, x)
    tree2_nonzero = jax.tree.map(ensure_nonzero, tree2)
    
    # Multiply then divide
    product = tree.mul(tree1, tree2_nonzero)
    quotient = tree.div(product, tree2_nonzero)
    
    assert trees_close(quotient, tree1, rtol=1e-3, atol=1e-6), \
        f"Division not inverse of multiplication"

# Test 5: Clip idempotence
@given(simple_trees(), 
       st.floats(min_value=-100, max_value=0, allow_nan=False),
       st.floats(min_value=0, max_value=100, allow_nan=False))
@settings(max_examples=100)
def test_clip_idempotent(tree_val, min_val, max_val):
    """Test that clip(clip(x, min, max), min, max) == clip(x, min, max)"""
    assume(min_val <= max_val)
    
    # First clip
    clipped_once = tree.clip(tree_val, min_value=min_val, max_value=max_val)
    # Second clip with same bounds
    clipped_twice = tree.clip(clipped_once, min_value=min_val, max_value=max_val)
    
    assert trees_close(clipped_once, clipped_twice), \
        f"Clip not idempotent"

# Test 6: Clip bounds property
@given(simple_trees(),
       st.floats(min_value=-100, max_value=0, allow_nan=False),
       st.floats(min_value=0, max_value=100, allow_nan=False))
@settings(max_examples=100)
def test_clip_bounds(tree_val, min_val, max_val):
    """Test that clipped values are within [min_val, max_val]"""
    assume(min_val <= max_val)
    
    clipped = tree.clip(tree_val, min_value=min_val, max_value=max_val)
    
    def check_bounds(x):
        return bool(jnp.all(x >= min_val) and jnp.all(x <= max_val))
    
    results = jax.tree.map(check_bounds, clipped)
    leaves = jax.tree.leaves(results)
    assert all(leaves) if leaves else True, \
        f"Clipped values not within bounds [{min_val}, {max_val}]"

# Test 7: Constant schedule property
@given(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False),
       st.integers(min_value=0, max_value=10000))
@settings(max_examples=100)
def test_constant_schedule(value, step):
    """Test that constant_schedule always returns the same value."""
    schedule_fn = optax.schedules.constant_schedule(value)
    
    result = schedule_fn(step)
    
    # Should always return the constant value
    assert jnp.isclose(result, value), \
        f"Constant schedule returned {result} instead of {value} at step {step}"

# Test 8: Linear schedule endpoints
@given(st.floats(min_value=-100, max_value=100, allow_nan=False),
       st.floats(min_value=-100, max_value=100, allow_nan=False),
       st.integers(min_value=1, max_value=1000))
@settings(max_examples=100) 
def test_linear_schedule_endpoints(init_val, end_val, transition_steps):
    """Test that linear_schedule has correct start and end values."""
    schedule_fn = optax.schedules.linear_schedule(
        init_value=init_val,
        end_value=end_val,
        transition_steps=transition_steps,
        transition_begin=0
    )
    
    # Check initial value
    start_val = schedule_fn(0)
    assert jnp.isclose(start_val, init_val, rtol=1e-5), \
        f"Linear schedule start value {start_val} != {init_val}"
    
    # Check end value
    end_step_val = schedule_fn(transition_steps)
    assert jnp.isclose(end_step_val, end_val, rtol=1e-5), \
        f"Linear schedule end value {end_step_val} != {end_val}"

# Test 9: Tree add with zero
@given(simple_trees())
@settings(max_examples=100)
def test_tree_add_zero_identity(tree_val):
    """Test that adding zero tree is identity: add(x, 0) == x"""
    # Create zero tree with same structure
    zero_tree = jax.tree.map(lambda x: jnp.zeros_like(x), tree_val)
    
    result = tree.add(tree_val, zero_tree)
    
    assert trees_close(result, tree_val), \
        f"Adding zero tree not identity"

# Test 10: Tree scale by 1 is identity
@given(simple_trees())
@settings(max_examples=100)
def test_tree_scale_one_identity(tree_val):
    """Test that scaling by 1 is identity."""
    scaled = jax.tree.map(lambda x: 1.0 * x, tree_val)
    
    assert trees_close(scaled, tree_val), \
        f"Scaling by 1 not identity"

if __name__ == "__main__":
    print("Running property-based tests for optax...")
    
    # Run each test
    tests = [
        test_tree_add_commutative,
        test_tree_add_associative,
        test_tree_add_scale_equivalence,
        test_div_mul_inverse,
        test_clip_idempotent,
        test_clip_bounds,
        test_constant_schedule,
        test_linear_schedule_endpoints,
        test_tree_add_zero_identity,
        test_tree_scale_one_identity
    ]
    
    for test in tests:
        print(f"Running {test.__name__}...")
        try:
            test()
            print(f"  ✓ {test.__name__} passed")
        except Exception as e:
            print(f"  ✗ {test.__name__} failed: {e}")
    
    print("\nAll tests completed!")