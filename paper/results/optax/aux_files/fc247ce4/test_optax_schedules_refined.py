import math
import random
import string
from datetime import datetime

import jax.numpy as jnp
import numpy as np
import optax
from hypothesis import assume, given, settings, strategies as st


@given(
    init_value=st.floats(min_value=1e-10, max_value=100.0, allow_nan=False, allow_infinity=False),
    boundaries=st.lists(
        st.integers(min_value=1, max_value=1000),
        min_size=1,
        max_size=3,
        unique=True
    ).map(sorted),
    scale=st.floats(min_value=-10.0, max_value=-0.1, allow_nan=False, allow_infinity=False)
)
def test_piecewise_constant_negative_scale(init_value, boundaries, scale):
    # Test that negative scales are rejected
    boundaries_and_scales = dict(zip(boundaries, [scale] * len(boundaries)))
    
    try:
        schedule = optax.piecewise_constant_schedule(
            init_value=init_value,
            boundaries_and_scales=boundaries_and_scales
        )
        # If we get here without error, that's a bug
        result = schedule(boundaries[0])
        assert False, f"Expected ValueError for negative scale {scale}, but got result {result}"
    except ValueError as e:
        # This is expected
        assert "non-negative" in str(e)


@given(
    interpolate_type=st.sampled_from(['linear', 'cosine']),
    init_value=st.floats(min_value=1e-10, max_value=100.0, allow_nan=False, allow_infinity=False),
    boundaries=st.lists(
        st.integers(min_value=1, max_value=1000),
        min_size=1,
        max_size=3,
        unique=True
    ).map(sorted),
    scale=st.floats(min_value=-10.0, max_value=-0.1, allow_nan=False, allow_infinity=False)
)
def test_piecewise_interpolate_negative_scale(interpolate_type, init_value, boundaries, scale):
    # Test that negative scales are rejected
    boundaries_and_scales = dict(zip(boundaries, [scale] * len(boundaries)))
    
    try:
        schedule = optax.piecewise_interpolate_schedule(
            interpolate_type=interpolate_type,
            init_value=init_value,
            boundaries_and_scales=boundaries_and_scales
        )
        # If we get here without error, that's a bug
        result = schedule(boundaries[0])
        assert False, f"Expected ValueError for negative scale {scale}, but got result {result}"
    except ValueError as e:
        # This is expected
        assert "non-negative" in str(e)


@given(
    init_value=st.floats(min_value=1e-10, max_value=100.0, allow_nan=False, allow_infinity=False),
    end_value=st.floats(min_value=1e-10, max_value=100.0, allow_nan=False, allow_infinity=False),
    power=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    transition_steps=st.integers(min_value=-10, max_value=-1),
    transition_begin=st.integers(min_value=0, max_value=100)
)
def test_polynomial_negative_transition_steps(init_value, end_value, power, transition_steps, transition_begin):
    # According to docstring, if transition_steps <= 0, value is held fixed at init_value
    schedule = optax.polynomial_schedule(
        init_value=init_value,
        end_value=end_value,
        power=power,
        transition_steps=transition_steps,
        transition_begin=transition_begin
    )
    
    # Should always return init_value
    for count in [0, 100, 1000, 10000]:
        result = schedule(count)
        assert result == init_value


@given(
    init_value=st.floats(min_value=1e-10, max_value=100.0, allow_nan=False, allow_infinity=False),
    transition_steps=st.integers(min_value=1, max_value=1000),
    transition_begin=st.integers(min_value=0, max_value=100),
    staircase=st.booleans()
)
def test_exponential_decay_zero_rate(init_value, transition_steps, transition_begin, staircase):
    # According to docstring, decay_rate=0 results in constant schedule
    schedule = optax.exponential_decay(
        init_value=init_value,
        transition_steps=transition_steps,
        decay_rate=0,
        transition_begin=transition_begin,
        staircase=staircase
    )
    
    # Should always return init_value
    for count in [0, 100, 1000, 10000]:
        result = schedule(count)
        assert result == init_value


@given(
    init_value=st.floats(min_value=1e-10, max_value=100.0, allow_nan=False, allow_infinity=False),
    decay_steps=st.integers(min_value=-10, max_value=0)
)
def test_cosine_decay_non_positive_steps(init_value, decay_steps):
    # According to the code, cosine_decay_schedule requires positive decay_steps
    try:
        schedule = optax.cosine_decay_schedule(
            init_value=init_value,
            decay_steps=decay_steps,
            alpha=0.0,
            exponent=1.0
        )
        # If we get here without error, that's a bug  
        result = schedule(0)
        assert False, f"Expected ValueError for non-positive decay_steps={decay_steps}, but got result {result}"
    except ValueError as e:
        assert "positive decay_steps" in str(e)


@given(
    interpolate_type=st.sampled_from(['linear', 'cosine']),
    init_value=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    boundary1=st.integers(min_value=10, max_value=100),
    boundary2=st.integers(min_value=200, max_value=300),
    scale1=st.floats(min_value=0.1, max_value=2.0, allow_nan=False, allow_infinity=False),
    scale2=st.floats(min_value=0.1, max_value=2.0, allow_nan=False, allow_infinity=False)
)
def test_piecewise_interpolate_monotonicity_between_boundaries(
    interpolate_type, init_value, boundary1, boundary2, scale1, scale2
):
    # Test that interpolation between boundaries is monotonic
    boundaries_and_scales = {boundary1: scale1, boundary2: scale2}
    
    schedule = optax.piecewise_interpolate_schedule(
        interpolate_type=interpolate_type,
        init_value=init_value,
        boundaries_and_scales=boundaries_and_scales
    )
    
    # Check monotonicity between boundaries
    start_val = float(schedule(boundary1))
    end_val = float(schedule(boundary2))
    
    # Sample points between boundaries
    test_points = sorted([boundary1 + i * (boundary2 - boundary1) // 10 for i in range(11)])
    values = [float(schedule(p)) for p in test_points]
    
    # Check if monotonic (either all increasing or all decreasing)
    diffs = [values[i+1] - values[i] for i in range(len(values)-1)]
    
    # All diffs should have the same sign (allowing for small float errors)
    if start_val < end_val:
        # Should be increasing
        for i, diff in enumerate(diffs):
            assert diff >= -1e-6, f"Non-monotonic at index {i}: diff={diff}, values={values}"
    else:
        # Should be decreasing
        for i, diff in enumerate(diffs):
            assert diff <= 1e-6, f"Non-monotonic at index {i}: diff={diff}, values={values}"


@given(
    transition_steps=st.integers(min_value=-10, max_value=0),
    peak_value=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
)
def test_linear_onecycle_non_positive_steps(transition_steps, peak_value):
    # According to the code, should raise ValueError for non-positive transition_steps
    try:
        schedule = optax.linear_onecycle_schedule(
            transition_steps=transition_steps,
            peak_value=peak_value
        )
        result = schedule(0)
        assert False, f"Expected ValueError for non-positive transition_steps={transition_steps}, but got result {result}"
    except ValueError as e:
        assert "non-positive" in str(e)


@given(
    transition_steps=st.integers(min_value=-10, max_value=0),
    peak_value=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
)
def test_cosine_onecycle_non_positive_steps(transition_steps, peak_value):
    # According to the code, should raise ValueError for non-positive transition_steps
    try:
        schedule = optax.cosine_onecycle_schedule(
            transition_steps=transition_steps,
            peak_value=peak_value
        )
        result = schedule(0)
        assert False, f"Expected ValueError for non-positive transition_steps={transition_steps}, but got result {result}"
    except ValueError as e:
        assert "non-positive" in str(e)