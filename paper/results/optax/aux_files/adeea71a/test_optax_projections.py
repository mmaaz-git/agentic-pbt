import math
import numpy as np
import jax.numpy as jnp
from hypothesis import given, strategies as st, settings, assume
import optax.projections as proj
import optax.tree as tree_utils


# Strategy for valid arrays
def arrays_strategy(min_size=1, max_size=100):
    return st.lists(
        st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
        min_size=min_size, max_size=max_size
    ).map(lambda lst: jnp.array(lst))


# Strategy for tree structures
@st.composite
def tree_strategy(draw):
    array = draw(arrays_strategy())
    # Sometimes return just array, sometimes a dict tree
    if draw(st.booleans()):
        return array
    else:
        return {
            "weights": array,
            "bias": draw(st.floats(min_value=-100, max_value=100, allow_nan=False))
        }


# Test 1: Idempotence - projecting twice equals projecting once
@given(
    tree=tree_strategy(),
    scale=st.floats(min_value=0.1, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_l2_ball_idempotence(tree, scale):
    """Test that projecting onto l2 ball twice gives same result as once."""
    once = proj.projection_l2_ball(tree, scale)
    twice = proj.projection_l2_ball(once, scale)
    
    # Compare with tolerance for floating point
    def assert_close(a, b):
        if isinstance(a, dict):
            for k in a:
                assert_close(a[k], b[k])
        else:
            assert jnp.allclose(a, b, rtol=1e-5, atol=1e-7)
    
    assert_close(once, twice)


@given(
    tree=tree_strategy(),
    scale=st.floats(min_value=0.1, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_l1_ball_idempotence(tree, scale):
    """Test that projecting onto l1 ball twice gives same result as once."""
    once = proj.projection_l1_ball(tree, scale)
    twice = proj.projection_l1_ball(once, scale)
    
    def assert_close(a, b):
        if isinstance(a, dict):
            for k in a:
                assert_close(a[k], b[k])
        else:
            assert jnp.allclose(a, b, rtol=1e-5, atol=1e-7)
    
    assert_close(once, twice)


@given(
    tree=tree_strategy(),
    scale=st.floats(min_value=0.1, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_simplex_idempotence(tree, scale):
    """Test that projecting onto simplex twice gives same result as once."""
    once = proj.projection_simplex(tree, scale)
    twice = proj.projection_simplex(once, scale)
    
    def assert_close(a, b):
        if isinstance(a, dict):
            for k in a:
                assert_close(a[k], b[k])
        else:
            assert jnp.allclose(a, b, rtol=1e-5, atol=1e-7)
    
    assert_close(once, twice)


# Test 2: Constraint satisfaction
@given(
    tree=tree_strategy(),
    scale=st.floats(min_value=0.1, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_l2_ball_constraint_satisfaction(tree, scale):
    """Test that projection onto l2 ball satisfies the constraint ||x||_2 <= scale."""
    result = proj.projection_l2_ball(tree, scale)
    norm = tree_utils.norm(result, ord=2)
    
    # Allow small numerical tolerance
    assert norm <= scale * (1 + 1e-5), f"Norm {norm} exceeds scale {scale}"


@given(
    tree=tree_strategy(),
    scale=st.floats(min_value=0.1, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_l1_ball_constraint_satisfaction(tree, scale):
    """Test that projection onto l1 ball satisfies the constraint ||x||_1 <= scale."""
    result = proj.projection_l1_ball(tree, scale)
    norm = tree_utils.norm(result, ord=1)
    
    # Allow small numerical tolerance
    assert norm <= scale * (1 + 1e-5), f"Norm {norm} exceeds scale {scale}"


@given(
    tree=tree_strategy(),
    scale=st.floats(min_value=0.1, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_simplex_constraint_satisfaction(tree, scale):
    """Test that projection onto simplex satisfies sum=scale and non-negative."""
    result = proj.projection_simplex(tree, scale)
    
    # Check sum equals scale
    total = tree_utils.sum(result)
    assert jnp.allclose(total, scale, rtol=1e-5), f"Sum {total} != scale {scale}"
    
    # Check non-negative
    def check_non_negative(x):
        if isinstance(x, dict):
            for v in x.values():
                check_non_negative(v)
        else:
            assert jnp.all(x >= -1e-7), "Found negative values in simplex projection"
    
    check_non_negative(result)


@given(tree=tree_strategy())
@settings(max_examples=100, deadline=None)
def test_non_negative_constraint_satisfaction(tree):
    """Test that projection onto non-negative orthant satisfies x >= 0."""
    result = proj.projection_non_negative(tree)
    
    def check_non_negative(x):
        if isinstance(x, dict):
            for v in x.values():
                check_non_negative(v)
        else:
            assert jnp.all(x >= -1e-10), "Found negative values"
    
    check_non_negative(result)


# Test 3: Already in set property
@given(scale=st.floats(min_value=0.1, max_value=100))
@settings(max_examples=100, deadline=None)
def test_l2_ball_already_in_set(scale):
    """Test that points already in l2 ball are unchanged."""
    # Create a point that's already in the ball
    tree = jnp.array([scale/2, 0, 0])  # Norm = scale/2 < scale
    result = proj.projection_l2_ball(tree, scale)
    
    assert jnp.allclose(tree, result, rtol=1e-7), "Point already in ball was modified"


@given(scale=st.floats(min_value=0.1, max_value=100))
@settings(max_examples=100, deadline=None)
def test_simplex_already_in_set(scale):
    """Test that points already on simplex are unchanged."""
    # Create a point that's already on the simplex
    n = 5
    tree = jnp.ones(n) * (scale / n)  # Sum = scale, all positive
    result = proj.projection_simplex(tree, scale)
    
    assert jnp.allclose(tree, result, rtol=1e-5), "Point already on simplex was modified"


# Test 4: Box projection properties
@given(
    tree=arrays_strategy(),
    lower=st.floats(min_value=-100, max_value=0),
    upper=st.floats(min_value=0, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_box_constraint_satisfaction(tree, lower, upper):
    """Test that box projection satisfies lower <= x <= upper."""
    assume(lower <= upper)
    
    result = proj.projection_box(tree, lower, upper)
    
    assert jnp.all(result >= lower - 1e-10), f"Values below lower bound {lower}"
    assert jnp.all(result <= upper + 1e-10), f"Values above upper bound {upper}"


@given(
    tree=arrays_strategy(),
    lower=st.floats(min_value=-100, max_value=0),
    upper=st.floats(min_value=0, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_box_idempotence(tree, lower, upper):
    """Test that projecting onto box twice gives same result as once."""
    assume(lower <= upper)
    
    once = proj.projection_box(tree, lower, upper)
    twice = proj.projection_box(once, lower, upper)
    
    assert jnp.allclose(once, twice, rtol=1e-7), "Box projection not idempotent"


# Test 5: Hypercube as special case of box
@given(
    tree=arrays_strategy(),
    scale=st.floats(min_value=0.1, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_hypercube_equals_box(tree, scale):
    """Test that hypercube projection equals box projection with [0, scale]."""
    hypercube_result = proj.projection_hypercube(tree, scale)
    box_result = proj.projection_box(tree, 0, scale)
    
    assert jnp.allclose(hypercube_result, box_result, rtol=1e-7), \
        "Hypercube projection differs from equivalent box projection"


# Test 6: L-infinity ball projection
@given(
    tree=tree_strategy(),
    scale=st.floats(min_value=0.1, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_linf_ball_constraint_satisfaction(tree, scale):
    """Test that projection onto l-inf ball satisfies ||x||_inf <= scale."""
    result = proj.projection_linf_ball(tree, scale)
    norm = tree_utils.norm(result, ord=jnp.inf)
    
    assert norm <= scale * (1 + 1e-5), f"L-inf norm {norm} exceeds scale {scale}"


@given(
    tree=tree_strategy(),
    scale=st.floats(min_value=0.1, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_linf_ball_idempotence(tree, scale):
    """Test that projecting onto l-inf ball twice gives same result as once."""
    once = proj.projection_linf_ball(tree, scale)
    twice = proj.projection_linf_ball(once, scale)
    
    def assert_close(a, b):
        if isinstance(a, dict):
            for k in a:
                assert_close(a[k], b[k])
        else:
            assert jnp.allclose(a, b, rtol=1e-5, atol=1e-7)
    
    assert_close(once, twice)


# Test 7: Sphere projections (exact constraint)
@given(
    tree=tree_strategy(),
    scale=st.floats(min_value=0.1, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_l2_sphere_constraint_satisfaction(tree, scale):
    """Test that projection onto l2 sphere satisfies ||x||_2 = scale."""
    # Skip zero vectors as they can't be projected onto sphere
    norm = tree_utils.norm(tree, ord=2)
    assume(norm > 1e-10)
    
    result = proj.projection_l2_sphere(tree, scale)
    result_norm = tree_utils.norm(result, ord=2)
    
    assert jnp.allclose(result_norm, scale, rtol=1e-4), \
        f"L2 sphere norm {result_norm} != scale {scale}"


@given(
    tree=tree_strategy(),
    scale=st.floats(min_value=0.1, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_l1_sphere_constraint_satisfaction(tree, scale):
    """Test that projection onto l1 sphere satisfies ||x||_1 = scale."""
    # Skip zero vectors
    norm = tree_utils.norm(tree, ord=1)
    assume(norm > 1e-10)
    
    result = proj.projection_l1_sphere(tree, scale)
    result_norm = tree_utils.norm(result, ord=1)
    
    assert jnp.allclose(result_norm, scale, rtol=1e-4), \
        f"L1 sphere norm {result_norm} != scale {scale}"


if __name__ == "__main__":
    # Run a quick smoke test
    print("Running smoke tests...")
    test_l2_ball_idempotence()
    test_l2_ball_constraint_satisfaction()
    test_simplex_constraint_satisfaction()
    print("Smoke tests passed!")