import math
import warnings
import jax
import jax.numpy as jnp
import numpy as np
from hypothesis import given, strategies as st, settings, assume
import optax.monte_carlo as mc
from optax._src import utils


warnings.filterwarnings("ignore", category=DeprecationWarning)


@given(
    mean=st.lists(
        st.floats(
            min_value=-10.0, 
            max_value=10.0, 
            allow_nan=False, 
            allow_infinity=False
        ), 
        min_size=1, 
        max_size=5
    ),
    log_std=st.lists(
        st.floats(
            min_value=-5.0, 
            max_value=2.0, 
            allow_nan=False, 
            allow_infinity=False
        ), 
        min_size=1, 
        max_size=5
    ),
    num_samples=st.integers(min_value=1, max_value=100),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
@settings(max_examples=100)
def test_score_function_jacobians_shape(mean, log_std, num_samples, seed):
    assume(len(mean) == len(log_std))
    
    mean_array = jnp.array(mean)
    log_std_array = jnp.array(log_std)
    params = (mean_array, log_std_array)
    
    def simple_function(x):
        return jnp.sum(x ** 2)
    
    rng = jax.random.PRNGKey(seed)
    
    jacobians = mc.score_function_jacobians(
        simple_function,
        params,
        utils.multi_normal,
        rng,
        num_samples
    )
    
    assert len(jacobians) == len(params)
    
    for i, param in enumerate(params):
        expected_shape = (num_samples,) + param.shape
        assert jacobians[i].shape == expected_shape, f"Jacobian {i} shape mismatch: {jacobians[i].shape} != {expected_shape}"


@given(
    mean=st.lists(
        st.floats(
            min_value=-10.0, 
            max_value=10.0, 
            allow_nan=False, 
            allow_infinity=False
        ), 
        min_size=1, 
        max_size=5
    ),
    log_std=st.lists(
        st.floats(
            min_value=-5.0, 
            max_value=2.0, 
            allow_nan=False, 
            allow_infinity=False
        ), 
        min_size=1, 
        max_size=5
    ),
    num_samples=st.integers(min_value=1, max_value=100),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
@settings(max_examples=100)
def test_pathwise_jacobians_shape(mean, log_std, num_samples, seed):
    assume(len(mean) == len(log_std))
    
    mean_array = jnp.array(mean)
    log_std_array = jnp.array(log_std)
    params = (mean_array, log_std_array)
    
    def simple_function(x):
        return jnp.sum(x ** 2)
    
    rng = jax.random.PRNGKey(seed)
    
    jacobians = mc.pathwise_jacobians(
        simple_function,
        params,
        utils.multi_normal,
        rng,
        num_samples
    )
    
    assert len(jacobians) == len(params)
    
    for i, param in enumerate(params):
        expected_shape = (num_samples,) + param.shape
        assert jacobians[i].shape == expected_shape, f"Jacobian {i} shape mismatch: {jacobians[i].shape} != {expected_shape}"


@given(
    mean=st.lists(
        st.floats(
            min_value=-5.0, 
            max_value=5.0, 
            allow_nan=False, 
            allow_infinity=False
        ), 
        min_size=1, 
        max_size=3
    ),
    log_std=st.lists(
        st.floats(
            min_value=-3.0, 
            max_value=1.0, 
            allow_nan=False, 
            allow_infinity=False
        ), 
        min_size=1, 
        max_size=3
    ),
    num_samples=st.integers(min_value=1, max_value=50),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
@settings(max_examples=50)
def test_measure_valued_jacobians_shape(mean, log_std, num_samples, seed):
    assume(len(mean) == len(log_std))
    
    mean_array = jnp.array(mean)
    log_std_array = jnp.array(log_std)
    params = (mean_array, log_std_array)
    
    def simple_function(x):
        return jnp.sum(x ** 2)
    
    rng = jax.random.PRNGKey(seed)
    
    jacobians = mc.measure_valued_jacobians(
        simple_function,
        params,
        utils.multi_normal,
        rng,
        num_samples,
        coupling=True
    )
    
    assert len(jacobians) == len(params)
    
    expected_shape = (num_samples,) + mean_array.shape
    assert jacobians[0].shape == expected_shape, f"Mean jacobian shape mismatch: {jacobians[0].shape} != {expected_shape}"
    assert jacobians[1].shape == expected_shape, f"Std jacobian shape mismatch: {jacobians[1].shape} != {expected_shape}"


@given(
    mean=st.lists(
        st.floats(
            min_value=-5.0, 
            max_value=5.0, 
            allow_nan=False, 
            allow_infinity=False
        ), 
        min_size=1, 
        max_size=3
    ),
    log_std=st.lists(
        st.floats(
            min_value=-3.0, 
            max_value=1.0, 
            allow_nan=False, 
            allow_infinity=False
        ), 
        min_size=1, 
        max_size=3
    ),
    num_samples=st.integers(min_value=1, max_value=50),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
@settings(max_examples=50)
def test_gradient_estimators_finite(mean, log_std, num_samples, seed):
    assume(len(mean) == len(log_std))
    
    mean_array = jnp.array(mean)
    log_std_array = jnp.array(log_std)
    params = (mean_array, log_std_array)
    
    def simple_function(x):
        return jnp.sum(x ** 2)
    
    rng = jax.random.PRNGKey(seed)
    
    score_jacs = mc.score_function_jacobians(
        simple_function, params, utils.multi_normal, rng, num_samples
    )
    for jac in score_jacs:
        assert jnp.all(jnp.isfinite(jac)), "Score function jacobians contain non-finite values"
    
    pathwise_jacs = mc.pathwise_jacobians(
        simple_function, params, utils.multi_normal, rng, num_samples
    )
    for jac in pathwise_jacs:
        assert jnp.all(jnp.isfinite(jac)), "Pathwise jacobians contain non-finite values"
    
    measure_jacs = mc.measure_valued_jacobians(
        simple_function, params, utils.multi_normal, rng, num_samples
    )
    for jac in measure_jacs:
        assert jnp.all(jnp.isfinite(jac)), "Measure valued jacobians contain non-finite values"


@given(
    initial_value=st.floats(
        min_value=-100.0, 
        max_value=100.0, 
        allow_nan=False, 
        allow_infinity=False
    ),
    sample_values=st.lists(
        st.floats(
            min_value=-100.0, 
            max_value=100.0, 
            allow_nan=False, 
            allow_infinity=False
        ),
        min_size=1,
        max_size=20
    ),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
@settings(max_examples=100)
def test_moving_avg_baseline_with_zero_decay(initial_value, sample_values, seed):
    def simple_function(x):
        return float(x[0])
    
    _, _, update_state = mc.moving_avg_baseline(simple_function, decay=0.0, zero_debias=False)
    
    state = (jnp.array(initial_value), 0)
    
    for value in sample_values:
        samples = jnp.array([[value]])
        state = update_state(None, samples, state)
        
        assert jnp.allclose(state[0], value, rtol=1e-6), f"Moving average with decay=0 should equal last value. Got {state[0]}, expected {value}"


@given(
    initial_value=st.floats(
        min_value=-100.0, 
        max_value=100.0, 
        allow_nan=False, 
        allow_infinity=False
    ),
    sample_values=st.lists(
        st.floats(
            min_value=-100.0, 
            max_value=100.0, 
            allow_nan=False, 
            allow_infinity=False
        ),
        min_size=1,
        max_size=20
    ),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
@settings(max_examples=100)
def test_moving_avg_baseline_with_unit_decay(initial_value, sample_values, seed):
    def simple_function(x):
        return float(x[0])
    
    _, _, update_state = mc.moving_avg_baseline(
        simple_function, 
        decay=1.0, 
        zero_debias=False,
        use_decay_early_training_heuristic=False
    )
    
    state = (jnp.array(initial_value), 0)
    original_value = state[0]
    
    for value in sample_values:
        samples = jnp.array([[value]])
        state = update_state(None, samples, state)
        
        assert jnp.allclose(state[0], original_value, rtol=1e-6), f"Moving average with decay=1 should never change. Got {state[0]}, expected {original_value}"


@given(
    mean=st.lists(
        st.floats(
            min_value=-5.0, 
            max_value=5.0, 
            allow_nan=False, 
            allow_infinity=False
        ), 
        min_size=1, 
        max_size=3
    ),
    log_std=st.lists(
        st.floats(
            min_value=-3.0, 
            max_value=1.0, 
            allow_nan=False, 
            allow_infinity=False
        ), 
        min_size=1, 
        max_size=3
    ),
    num_samples=st.integers(min_value=10, max_value=50),
    eps=st.floats(min_value=1e-10, max_value=1.0),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
@settings(max_examples=50)
def test_control_variate_coefficients_finite(mean, log_std, num_samples, eps, seed):
    assume(len(mean) == len(log_std))
    
    mean_array = jnp.array(mean)
    log_std_array = jnp.array(log_std)
    params = (mean_array, log_std_array)
    
    def simple_function(x):
        return jnp.sum(x ** 2)
    
    rng = jax.random.PRNGKey(seed)
    
    coeffs = mc.estimate_control_variate_coefficients(
        simple_function,
        mc.control_delta_method,
        mc.score_function_jacobians,
        params,
        utils.multi_normal,
        rng,
        num_samples,
        control_variate_state=None,
        eps=eps
    )
    
    assert len(coeffs) == len(params)
    for coeff in coeffs:
        assert jnp.isfinite(coeff), f"Control variate coefficient is not finite: {coeff}"


@given(
    values=st.lists(
        st.floats(
            min_value=-10.0, 
            max_value=10.0, 
            allow_nan=False, 
            allow_infinity=False
        ),
        min_size=100,
        max_size=500
    ),
    decay=st.floats(min_value=0.5, max_value=0.99)
)
@settings(max_examples=50)
def test_moving_avg_convergence(values, decay):
    def simple_function(x):
        return float(x[0])
    
    _, _, update_state = mc.moving_avg_baseline(
        simple_function, 
        decay=decay, 
        zero_debias=True,
        use_decay_early_training_heuristic=False
    )
    
    state = (jnp.array(0.0), 0)
    
    for value in values:
        samples = jnp.array([[value]])
        state = update_state(None, samples, state)
    
    expected_mean = np.mean(values)
    
    assert jnp.abs(state[0] - expected_mean) < 5.0, f"Moving average {state[0]} is too far from mean {expected_mean}"


@given(
    mean=st.lists(
        st.floats(
            min_value=-2.0, 
            max_value=2.0, 
            allow_nan=False, 
            allow_infinity=False
        ), 
        min_size=1, 
        max_size=2
    ),
    log_std=st.lists(
        st.floats(
            min_value=-2.0, 
            max_value=0.5, 
            allow_nan=False, 
            allow_infinity=False
        ), 
        min_size=1, 
        max_size=2
    ),
    num_samples=st.integers(min_value=10, max_value=30),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
@settings(max_examples=30)
def test_control_delta_method_taylor_expansion(mean, log_std, num_samples, seed):
    assume(len(mean) == len(log_std))
    
    mean_array = jnp.array(mean)
    log_std_array = jnp.array(log_std)
    params = (mean_array, log_std_array)
    
    def quadratic_function(x):
        return jnp.sum(x ** 2)
    
    delta_cv, expected_delta, _ = mc.control_delta_method(quadratic_function)
    
    rng = jax.random.PRNGKey(seed)
    dist = utils.multi_normal(*params)
    samples = dist.sample((num_samples,), key=rng)
    
    cv_values = jax.vmap(lambda x: delta_cv(params, x, None))(samples)
    
    assert jnp.all(jnp.isfinite(cv_values)), "Control delta values contain non-finite values"
    
    expected_val = expected_delta(params, None)
    assert jnp.isfinite(expected_val), "Expected delta value is not finite"