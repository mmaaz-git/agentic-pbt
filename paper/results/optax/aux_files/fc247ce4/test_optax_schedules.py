import math
import random
import string
from datetime import datetime

import jax.numpy as jnp
import numpy as np
import optax
from hypothesis import assume, given, settings, strategies as st


@given(
    value=st.one_of(
        st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False),
        st.integers(min_value=-10000, max_value=10000)
    ),
    count=st.integers(min_value=0, max_value=100000)
)
def test_constant_schedule_invariant(value, count):
    schedule = optax.constant_schedule(value)
    result = schedule(count)
    assert result == value


@given(
    init_value=st.floats(min_value=-1e5, max_value=1e5, allow_nan=False, allow_infinity=False),
    end_value=st.floats(min_value=-1e5, max_value=1e5, allow_nan=False, allow_infinity=False),
    transition_steps=st.integers(min_value=1, max_value=10000),
    transition_begin=st.integers(min_value=0, max_value=10000),
    count=st.integers(min_value=0, max_value=100000)
)
def test_linear_polynomial_equivalence(init_value, end_value, transition_steps, transition_begin, count):
    linear_sched = optax.linear_schedule(
        init_value=init_value,
        end_value=end_value, 
        transition_steps=transition_steps,
        transition_begin=transition_begin
    )
    
    poly_sched = optax.polynomial_schedule(
        init_value=init_value,
        end_value=end_value,
        power=1,
        transition_steps=transition_steps,
        transition_begin=transition_begin
    )
    
    linear_result = linear_sched(count)
    poly_result = poly_sched(count)
    
    assert jnp.allclose(linear_result, poly_result, rtol=1e-6, atol=1e-10)


@given(
    init_value=st.floats(min_value=-1e5, max_value=1e5, allow_nan=False, allow_infinity=False),
    end_value=st.floats(min_value=-1e5, max_value=1e5, allow_nan=False, allow_infinity=False),
    power=st.floats(min_value=0.1, max_value=10, allow_nan=False, allow_infinity=False),
    transition_steps=st.integers(min_value=1, max_value=10000),
    transition_begin=st.integers(min_value=0, max_value=10000)
)
def test_polynomial_schedule_boundaries(init_value, end_value, power, transition_steps, transition_begin):
    schedule = optax.polynomial_schedule(
        init_value=init_value,
        end_value=end_value,
        power=power,
        transition_steps=transition_steps,
        transition_begin=transition_begin
    )
    
    # Test at transition_begin - 1 (if positive)
    if transition_begin > 0:
        result_before = schedule(transition_begin - 1)
        assert jnp.allclose(result_before, init_value, rtol=1e-6, atol=1e-10)
    
    # Test at transition_begin
    result_at_begin = schedule(transition_begin)
    assert jnp.allclose(result_at_begin, init_value, rtol=1e-6, atol=1e-10)
    
    # Test at transition_begin + transition_steps
    result_at_end = schedule(transition_begin + transition_steps)
    assert jnp.allclose(result_at_end, end_value, rtol=1e-6, atol=1e-10)
    
    # Test after transition_begin + transition_steps
    result_after = schedule(transition_begin + transition_steps + 100)
    assert jnp.allclose(result_after, end_value, rtol=1e-6, atol=1e-10)


@given(
    init_value=st.floats(min_value=1e-10, max_value=1e5, allow_nan=False, allow_infinity=False),
    boundaries=st.lists(
        st.integers(min_value=1, max_value=10000),
        min_size=0,
        max_size=5,
        unique=True
    ).map(sorted),
    scales=st.lists(
        st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
        min_size=0,
        max_size=5
    )
)
def test_piecewise_constant_cumulative_scaling(init_value, boundaries, scales):
    assume(len(boundaries) == len(scales))
    
    if boundaries:
        boundaries_and_scales = dict(zip(boundaries, scales))
    else:
        boundaries_and_scales = None
    
    schedule = optax.piecewise_constant_schedule(
        init_value=init_value,
        boundaries_and_scales=boundaries_and_scales
    )
    
    # Test that value before first boundary is init_value
    if boundaries:
        result_before = schedule(boundaries[0] - 1)
        assert jnp.allclose(result_before, init_value, rtol=1e-6, atol=1e-10)
        
        # Test cumulative scaling
        expected_value = init_value
        for i, (boundary, scale) in enumerate(zip(boundaries, scales)):
            # Right at or after the boundary
            expected_value = expected_value * scale
            result_after = schedule(boundary)
            assert jnp.allclose(result_after, expected_value, rtol=1e-5, atol=1e-10)
            
            # Well after this boundary but before next (if exists)
            if i < len(boundaries) - 1:
                test_point = (boundary + boundaries[i + 1]) // 2
            else:
                test_point = boundary + 100
            result_between = schedule(test_point)
            assert jnp.allclose(result_between, expected_value, rtol=1e-5, atol=1e-10)
    else:
        # No boundaries, should always return init_value
        for count in [0, 100, 1000, 10000]:
            result = schedule(count)
            assert jnp.allclose(result, init_value, rtol=1e-6, atol=1e-10)


@given(
    init_value=st.floats(min_value=1e-10, max_value=1e5, allow_nan=False, allow_infinity=False),
    decay_steps=st.integers(min_value=1, max_value=10000),
    alpha=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    exponent=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
)
def test_cosine_decay_bounds(init_value, decay_steps, alpha, exponent):
    schedule = optax.cosine_decay_schedule(
        init_value=init_value,
        decay_steps=decay_steps,
        alpha=alpha,
        exponent=exponent
    )
    
    # Test various points
    test_points = [0, decay_steps // 4, decay_steps // 2, 3 * decay_steps // 4, 
                   decay_steps, decay_steps + 100, decay_steps * 2]
    
    min_value = alpha * init_value
    max_value = init_value
    
    for count in test_points:
        result = schedule(count)
        # Value should be between alpha * init_value and init_value
        assert result >= min_value - 1e-10
        assert result <= max_value + 1e-10
    
    # Test boundary values specifically
    result_at_0 = schedule(0)
    assert jnp.allclose(result_at_0, init_value, rtol=1e-6, atol=1e-10)
    
    result_at_end = schedule(decay_steps)
    assert jnp.allclose(result_at_end, alpha * init_value, rtol=1e-6, atol=1e-10)
    
    result_after_end = schedule(decay_steps + 1000)
    assert jnp.allclose(result_after_end, alpha * init_value, rtol=1e-6, atol=1e-10)


@given(
    init_value=st.floats(min_value=1e-10, max_value=100.0, allow_nan=False, allow_infinity=False),
    transition_steps=st.integers(min_value=1, max_value=1000),
    decay_rate=st.floats(min_value=0.01, max_value=0.99, allow_nan=False, allow_infinity=False),
    transition_begin=st.integers(min_value=0, max_value=1000),
    count=st.integers(min_value=0, max_value=10000)
)
def test_exponential_decay_monotonic(init_value, transition_steps, decay_rate, transition_begin, count):
    schedule = optax.exponential_decay(
        init_value=init_value,
        transition_steps=transition_steps,
        decay_rate=decay_rate,
        transition_begin=transition_begin,
        staircase=False
    )
    
    # For decay_rate < 1, the schedule should be non-increasing
    count1 = count
    count2 = count + 1
    
    result1 = schedule(count1)
    result2 = schedule(count2)
    
    # Should be non-increasing (allowing for floating point tolerance)
    assert result2 <= result1 + 1e-10