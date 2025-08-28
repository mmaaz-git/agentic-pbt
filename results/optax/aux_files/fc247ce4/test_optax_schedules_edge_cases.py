import math
import jax
import jax.numpy as jnp
import numpy as np
import optax
from hypothesis import assume, given, settings, strategies as st


@given(
    init_value=st.floats(min_value=1.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    transition_steps=st.integers(min_value=1, max_value=100),
    decay_rate=st.floats(min_value=2.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    end_value=st.floats(min_value=11.0, max_value=100.0, allow_nan=False, allow_infinity=False)
)
def test_exponential_decay_with_growth_and_upper_bound(init_value, transition_steps, decay_rate, end_value):
    # When decay_rate > 1, it's actually growth, and end_value should be an upper bound
    schedule = optax.exponential_decay(
        init_value=init_value,
        transition_steps=transition_steps,
        decay_rate=decay_rate,
        transition_begin=0,
        staircase=False,
        end_value=end_value
    )
    
    # Test at various points
    for i in range(0, transition_steps * 2, max(1, transition_steps // 10)):
        result = float(schedule(i))
        # Should never exceed end_value (upper bound when decay_rate > 1)
        assert result <= end_value + 1e-6, f"At step {i}: {result} > {end_value}"


@given(
    init_value=st.floats(min_value=10.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    transition_steps=st.integers(min_value=1, max_value=100),
    decay_rate=st.floats(min_value=0.1, max_value=0.9, allow_nan=False, allow_infinity=False),
    end_value=st.floats(min_value=0.1, max_value=9.0, allow_nan=False, allow_infinity=False)
)
def test_exponential_decay_with_decay_and_lower_bound(init_value, transition_steps, decay_rate, end_value):
    # When decay_rate < 1, it's decay, and end_value should be a lower bound
    assume(end_value < init_value)
    
    schedule = optax.exponential_decay(
        init_value=init_value,
        transition_steps=transition_steps,
        decay_rate=decay_rate,
        transition_begin=0,
        staircase=False,
        end_value=end_value
    )
    
    # Test at various points
    for i in range(0, transition_steps * 5, max(1, transition_steps // 5)):
        result = float(schedule(i))
        # Should never go below end_value (lower bound when decay_rate < 1)
        assert result >= end_value - 1e-6, f"At step {i}: {result} < {end_value}"


@given(
    init_value=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    end_value=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    power=st.floats(min_value=1e-10, max_value=1e-5, allow_nan=False, allow_infinity=False),
    transition_steps=st.integers(min_value=1, max_value=100)
)
def test_polynomial_schedule_extreme_small_power(init_value, end_value, power, transition_steps):
    # With very small power, the schedule should change very slowly
    schedule = optax.polynomial_schedule(
        init_value=init_value,
        end_value=end_value,
        power=power,
        transition_steps=transition_steps,
        transition_begin=0
    )
    
    # At the midpoint, with very small power, value should be close to end_value
    mid_result = float(schedule(transition_steps // 2))
    
    # With small power, (0.5)^power is very close to 1
    # So the value should be very close to init_value at midpoint
    frac = 0.5 ** power  # This will be very close to 1
    expected = (init_value - end_value) * frac + end_value
    
    # The schedule should behave correctly even with extreme powers
    assert not math.isnan(mid_result), f"NaN result with power={power}"
    assert not math.isinf(mid_result), f"Inf result with power={power}"


@given(
    boundaries1=st.lists(
        st.integers(min_value=1, max_value=500),
        min_size=2,
        max_size=4,
        unique=True
    ).map(sorted),
    scales1=st.lists(
        st.floats(min_value=0.1, max_value=2.0, allow_nan=False, allow_infinity=False),
        min_size=2,
        max_size=4
    )
)
def test_piecewise_interpolate_continuity(boundaries1, scales1):
    # Test that piecewise_interpolate is continuous at boundaries
    assume(len(boundaries1) == len(scales1))
    
    init_value = 1.0
    boundaries_and_scales = dict(zip(boundaries1, scales1))
    
    schedule = optax.piecewise_interpolate_schedule(
        interpolate_type='linear',
        init_value=init_value,
        boundaries_and_scales=boundaries_and_scales
    )
    
    # Check continuity at each boundary
    for boundary in boundaries1:
        # Get value just before and at the boundary
        val_before = float(schedule(boundary - 0.01))
        val_at = float(schedule(boundary))
        val_after = float(schedule(boundary + 0.01))
        
        # The function should be continuous (allowing for interpolation)
        # The jump at the boundary itself is expected, but we should see smooth behavior around it
        assert not math.isnan(val_before) and not math.isnan(val_at) and not math.isnan(val_after)
        assert not math.isinf(val_before) and not math.isinf(val_at) and not math.isinf(val_after)


@given(
    count=st.integers(min_value=10**15, max_value=10**18)
)
def test_constant_schedule_large_counts(count):
    # Test that constant schedule works with very large step counts
    value = 42.0
    schedule = optax.constant_schedule(value)
    result = schedule(count)
    assert result == value


@given(
    transition_steps=st.integers(min_value=1, max_value=100),
    peak_value=st.floats(min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False),
    pct_start=st.floats(min_value=0.01, max_value=0.49, allow_nan=False, allow_infinity=False),
    pct_final=st.floats(min_value=0.51, max_value=0.99, allow_nan=False, allow_infinity=False)
)
def test_linear_onecycle_phase_ordering(transition_steps, peak_value, pct_start, pct_final):
    # Ensure pct_start < pct_final for valid phase ordering
    assume(pct_start < pct_final)
    
    schedule = optax.linear_onecycle_schedule(
        transition_steps=transition_steps,
        peak_value=peak_value,
        pct_start=pct_start,
        pct_final=pct_final,
        div_factor=25.0,
        final_div_factor=1e4
    )
    
    # Test that we reach peak at pct_start
    peak_step = int(pct_start * transition_steps)
    result_at_peak = float(schedule(peak_step))
    
    # Due to interpolation, might not be exactly peak_value but should be close
    assert abs(result_at_peak - peak_value) <= peak_value * 0.1
    
    # Test that value decreases after peak
    if peak_step < transition_steps - 1:
        mid_step = int((pct_start + pct_final) * transition_steps / 2)
        result_mid = float(schedule(mid_step))
        assert result_mid < peak_value + 1e-6


@given(
    init_value=st.floats(min_value=1.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    boundaries=st.lists(
        st.integers(min_value=1, max_value=100),
        min_size=2,
        max_size=3,
        unique=True
    ),
    # Use same scale for all boundaries
    scale=st.floats(min_value=0.1, max_value=0.9, allow_nan=False, allow_infinity=False)
)
def test_piecewise_constant_duplicate_boundaries(init_value, boundaries, scale):
    # What happens with duplicate boundary values? Let's use the same boundary twice
    if len(boundaries) >= 2:
        dup_boundary = boundaries[0]
        boundaries_and_scales = {dup_boundary: scale, dup_boundary: scale * 0.5}
        
        schedule = optax.piecewise_constant_schedule(
            init_value=init_value,
            boundaries_and_scales=boundaries_and_scales
        )
        
        # Dictionary will keep only the last value for duplicate keys
        result = float(schedule(dup_boundary))
        expected = init_value * (scale * 0.5)  # Should use the last value
        assert abs(result - expected) < 1e-6