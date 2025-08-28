import jax
import jax.numpy as jnp
import numpy as np
import optax.second_order
from hypothesis import given, strategies as st, assume, settings
import pytest


# Test with very small values to check numerical stability
@given(
    params=st.lists(st.floats(min_value=-1e-8, max_value=1e-8, 
                               allow_nan=False, allow_infinity=False), 
                     min_size=2, max_size=2),
    inputs=st.lists(st.lists(st.floats(min_value=-1e-8, max_value=1e-8,
                                        allow_nan=False, allow_infinity=False),
                              min_size=2, max_size=2),
                    min_size=2, max_size=2),
    targets=st.lists(st.floats(min_value=-1e-8, max_value=1e-8,
                                allow_nan=False, allow_infinity=False),
                     min_size=2, max_size=2)
)
@settings(max_examples=50)
def test_fisher_diag_small_values(params, inputs, targets):
    """Test Fisher diagonal with very small values."""
    params = jnp.array(params)
    inputs = jnp.array(inputs)
    targets = jnp.array(targets)
    
    def loss_fn(p, x, t):
        pred = jnp.dot(x, p)
        return jnp.mean((pred - t) ** 2)
    
    fisher = optax.second_order.fisher_diag(loss_fn, params, inputs, targets)
    
    # Fisher diagonal should still be non-negative
    assert jnp.all(fisher >= -1e-10), f"Negative Fisher values: {fisher}"
    # Check for NaN or inf
    assert jnp.all(jnp.isfinite(fisher)), f"Non-finite Fisher values: {fisher}"


# Test with large parameter spaces
@given(
    param_size=st.integers(min_value=10, max_value=50)
)
@settings(max_examples=20, deadline=20000)
def test_hessian_diag_large_params(param_size):
    """Test Hessian diagonal computation with larger parameter spaces."""
    params = jnp.ones(param_size) * 0.1
    inputs = jnp.ones((5, param_size)) * 0.1
    targets = jnp.ones(5) * 0.5
    
    def loss_fn(p, x, t):
        pred = jnp.dot(x, p)
        return jnp.mean((pred - t) ** 2)
    
    # This should not crash or produce NaN/inf
    hess_diag = optax.second_order.hessian_diag(loss_fn, params, inputs, targets)
    
    assert hess_diag.shape == (param_size,), f"Wrong shape: {hess_diag.shape}"
    assert jnp.all(jnp.isfinite(hess_diag)), f"Non-finite values in Hessian diagonal"


# Test HVP with special vectors
@settings(max_examples=50)
@given(
    scale=st.floats(min_value=1e-10, max_value=1e10, 
                    allow_nan=False, allow_infinity=False)
)
def test_hvp_scaling(scale):
    """Test HVP scaling properties."""
    params = jnp.array([1.0, 2.0])
    inputs = jnp.array([[1.0, 0.5], [0.5, 1.0]])
    targets = jnp.array([1.5, 2.5])
    
    def loss_fn(p, x, t):
        pred = jnp.dot(x, p)
        return jnp.mean((pred - t) ** 2)
    
    v = jnp.array([1.0, 1.0])
    
    # Compute HVP with original and scaled vector
    hvp1 = optax.second_order.hvp(loss_fn, v, params, inputs, targets)
    hvp_scaled = optax.second_order.hvp(loss_fn, v * scale, params, inputs, targets)
    
    # HVP should scale linearly
    expected = hvp1 * scale
    
    # Use relative tolerance for large scales
    rtol = 1e-5 if scale < 1e6 else 1e-4
    assert jnp.allclose(hvp_scaled, expected, rtol=rtol), \
        f"Scaling property violated: scale={scale}, diff={jnp.max(jnp.abs(hvp_scaled - expected))}"


# Test with rank-deficient inputs
def test_rank_deficient_inputs():
    """Test with inputs that are rank-deficient."""
    params = jnp.array([1.0, 2.0, 3.0])
    # Rank-deficient inputs (third column is linear combination of first two)
    inputs = jnp.array([[1.0, 0.0, 1.0],
                        [0.0, 1.0, 1.0],
                        [1.0, 1.0, 2.0]])
    targets = jnp.array([1.0, 2.0, 3.0])
    
    def loss_fn(p, x, t):
        pred = jnp.dot(x, p)
        return jnp.mean((pred - t) ** 2)
    
    # These operations should still work with rank-deficient inputs
    fisher = optax.second_order.fisher_diag(loss_fn, params, inputs, targets)
    hess_diag = optax.second_order.hessian_diag(loss_fn, params, inputs, targets)
    hvp_result = optax.second_order.hvp(loss_fn, jnp.ones(3), params, inputs, targets)
    
    assert jnp.all(jnp.isfinite(fisher)), "Fisher has non-finite values"
    assert jnp.all(jnp.isfinite(hess_diag)), "Hessian diagonal has non-finite values"
    assert jnp.all(jnp.isfinite(hvp_result)), "HVP has non-finite values"


# Test orthogonal vectors in HVP
def test_hvp_orthogonal_basis():
    """Test HVP with orthogonal basis vectors."""
    params = jnp.array([1.0, 2.0, 3.0])
    inputs = jnp.eye(3) * 2.0  # Orthogonal inputs
    targets = jnp.array([1.0, 2.0, 3.0])
    
    def loss_fn(p, x, t):
        pred = jnp.dot(x, p)
        return jnp.mean((pred - t) ** 2)
    
    # Compute full Hessian via HVP with standard basis
    hessian_rows = []
    for i in range(3):
        ei = jnp.zeros(3).at[i].set(1.0)
        hessian_rows.append(optax.second_order.hvp(loss_fn, ei, params, inputs, targets))
    
    hessian = jnp.stack(hessian_rows)
    
    # Check symmetry of reconstructed Hessian
    assert jnp.allclose(hessian, hessian.T, rtol=1e-6), \
        f"Reconstructed Hessian is not symmetric: max diff = {jnp.max(jnp.abs(hessian - hessian.T))}"


if __name__ == "__main__":
    print("Running edge case tests for optax.second_order...")
    
    print("\n1. Testing with very small values...")
    test_fisher_diag_small_values()
    
    print("\n2. Testing with large parameter spaces...")
    test_hessian_diag_large_params()
    
    print("\n3. Testing HVP scaling...")
    test_hvp_scaling()
    
    print("\n4. Testing rank-deficient inputs...")
    test_rank_deficient_inputs()
    
    print("\n5. Testing HVP with orthogonal basis...")
    test_hvp_orthogonal_basis()
    
    print("\nAll edge case tests completed!")